package com.kh.back.auth;

import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.MemberDto;
import com.kh.back.member.MemberResponse;
import com.kh.back.member.MemberMapper;
import com.kh.back.member.UserProfileDto;
import com.kh.back.member.UserProfileMapper;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    // 일반 회원가입으로 만들어지는 역할. 관리자(ADMIN)는 회원가입으로 만들 수 없다
    private static final String DEFAULT_ROLE = "USER";

    // 보완 5: 가입 가능 나이. 차량 추천 서비스라 운전면허를 딸 수 있는 나이(만 18세, 1·2종 보통 기준)부터 받는다
    // (도로교통법 기준 — 법 조항은 확인 필요. 프론트 profileRules.js 의 MIN_SIGNUP_AGE 와 같은 값)
    private static final int MIN_SIGNUP_AGE = 18;

    private static final String GOOGLE = "GOOGLE"; // social_accounts.provider

    private final MemberMapper memberMapper;
    private final LoginAttemptLimiter loginAttemptLimiter;
    private final EmailVerificationService emailVerificationService;
    private final GoogleTokenVerifier googleTokenVerifier;
    private final GoogleSignupStore googleSignupStore;
    private final SocialAccountMapper socialAccountMapper;
    private final RecaptchaVerifier recaptchaVerifier;
    private final UserProfileMapper userProfileMapper;
    private final RefreshTokenMapper refreshTokenMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;

    @Override
    @Transactional
    public MemberResponse signup(SignupRequest request) {
        String email = normalizeEmail(request.getEmail());

        // 보완 2: 반복 · 연속 문자, 이메일 아이디 포함, 흔한 비밀번호 금지 (길이 · 문자 종류는 SignupRequest 가 먼저 검사)
        String passwordViolation = PasswordPolicy.check(request.getPassword(), email);
        if (passwordViolation != null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_POLICY", passwordViolation);
        }

        // 보완 5: 만 나이 = 생일이 지났는지까지 따진 나이 (Period 가 계산). 오늘 날짜는 서버 기준
        if (Period.between(request.getBirthDate(), LocalDate.now()).getYears() < MIN_SIGNUP_AGE) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "AGE_RESTRICTED",
                    "만 " + MIN_SIGNUP_AGE + "세 이상만 가입할 수 있습니다. (운전면허 취득 가능 나이 기준)");
        }

        if (memberMapper.findByEmail(email) != null) {
            throw emailDuplicated();
        }
        // 보완 7: 이메일 인증을 마쳐야 가입할 수 있다 (인증 후 30분 안)
        if (!emailVerificationService.isVerified(email)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "EMAIL_NOT_VERIFIED", "이메일 인증을 완료해 주세요.");
        }
        String nickName = request.getNickName().trim();
        checkNickNameWords(nickName); // 보완 3 추가: 금지어
        if (memberMapper.countByNickName(nickName) > 0) {
            throw nickNameDuplicated(); // 보완 3: 닉네임 중복 금지 (V7 UNIQUE)
        }

        MemberDto member = new MemberDto();
        member.setEmail(email);
        member.setPasswordHash(passwordEncoder.encode(request.getPassword())); // 원래 비밀번호는 저장하지 않는다
        member.setNickName(nickName);
        member.setRole(DEFAULT_ROLE);

        try {
            memberMapper.insert(member); // 이후 member.getId() 에 새 번호가 들어 있다
        } catch (DuplicateKeyException e) {
            // 위의 중복 확인과 저장 사이에 같은 이메일 · 닉네임이 먼저 가입된 경우 (UNIQUE 위반)
            // 어느 쪽이 겹쳤는지는 DB 오류 문구의 키 이름으로 구분한다
            String reason = String.valueOf(e.getMessage());
            throw reason.contains("uq_users_nick_name") ? nickNameDuplicated() : emailDuplicated();
        }

        // 보완 5: 개인 정보는 user_profiles 에 따로 저장한다. 같은 트랜잭션이라 여기서 실패하면 회원 저장도 취소된다
        UserProfileDto profile = new UserProfileDto();
        profile.setUserId(member.getId());
        profile.setPhone(request.getPhone().replace("-", "")); // 숫자만 저장
        profile.setBirthDate(request.getBirthDate());
        profile.setGender(request.getGender());
        userProfileMapper.insert(profile);

        // 보완 6: 가입 전에 이 이메일로 로그인에 실패한 기록이 있으면 지운다
        // (없는 이메일로 틀린 기록이 새 계정의 첫 로그인에 이어져 바로 reCAPTCHA 가 뜨지 않게)
        loginAttemptLimiter.reset(email);
        emailVerificationService.consume(email); // 보완 7: 쓴 인증 기록은 지운다

        return MemberResponse.from(member, profile);
    }

    // 보완 6: 잠겨 있으면 429 LOGIN_LOCKED (남은 시간을 분 단위로 안내)
    private void throwIfLocked(String email) {
        long minutes = loginAttemptLimiter.lockedMinutesLeft(email);
        if (minutes > 0) {
            throw new ApiException(HttpStatus.TOO_MANY_REQUESTS, "LOGIN_LOCKED",
                    "로그인에 5번 실패해 잠시 잠겼습니다. " + minutes + "분 뒤에 다시 시도해 주세요.");
        }
    }

    // 보완 7: [인증 코드 받기] — 형식 확인 → 이미 가입된 이메일이면 409 → 코드 발송 (기존 [중복 확인] 을 대신한다)
    @Override
    public EmailVerificationResponse sendEmailVerification(String email) {
        if (!isEmailAvailable(email)) {
            throw emailDuplicated();
        }
        boolean alreadyVerified = emailVerificationService.sendCode(normalizeEmail(email));
        return new EmailVerificationResponse(EmailVerificationService.CODE_VALIDITY.getSeconds(),
                EmailVerificationService.RESEND_COOLDOWN.getSeconds(), emailVerificationService.isMailEnabled(),
                alreadyVerified);
    }

    @Override
    public void confirmEmailVerification(String email, String code) {
        emailVerificationService.confirmCode(normalizeEmail(email), code);
    }

    // 보완 3: [중복 확인] 버튼 — 형식이 맞고 아직 가입되지 않은 이메일이면 true
    @Override
    @Transactional(readOnly = true)
    public boolean isEmailAvailable(String email) {
        String normalized = email == null ? "" : normalizeEmail(email);
        if (normalized.isEmpty() || normalized.length() > 100 || !normalized.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "이메일 형식이 올바르지 않습니다.");
        }
        return memberMapper.findByEmail(normalized) == null;
    }

    // 보완 3: [중복 확인] 버튼 — 2~12자이고 아직 쓰는 사람이 없는 닉네임이면 true
    // 보완 3 추가: 금지어가 들어 있으면 400 NICKNAME_FORBIDDEN (중복 여부보다 먼저 알려 준다)
    @Override
    @Transactional(readOnly = true)
    public boolean isNickNameAvailable(String nickName) {
        String trimmed = nickName == null ? "" : nickName.trim();
        if (trimmed.length() < 2 || trimmed.length() > 12) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "이름 또는 닉네임은 2~12자로 입력해 주세요.");
        }
        checkNickNameWords(trimmed);
        return memberMapper.countByNickName(trimmed) == 0;
    }

    // 보완 7 추가: 비밀번호 찾기 ① 인증 코드 받기 — 가입한 이메일만, 구글로만 가입한 계정은 비밀번호가 없어 안내
    // (가입 인증과 같은 표 · 규칙을 쓴다. 가입 인증은 "가입 안 한 이메일", 여기는 "가입한 이메일" 이라 겹치지 않는다)
    @Override
    public EmailVerificationResponse sendPasswordResetCode(String email) {
        String normalized = resetTarget(email).getEmail();
        boolean alreadyVerified = emailVerificationService.sendCode(normalized);
        return new EmailVerificationResponse(EmailVerificationService.CODE_VALIDITY.getSeconds(),
                EmailVerificationService.RESEND_COOLDOWN.getSeconds(), emailVerificationService.isMailEnabled(),
                alreadyVerified);
    }

    // ② 코드 확인
    @Override
    public void confirmPasswordResetCode(String email, String code) {
        emailVerificationService.confirmCode(resetTarget(email).getEmail(), code);
    }

    // ③ 새 비밀번호로 바꾸기 — 인증 후 30분 안, 회원가입과 같은 비밀번호 규칙
    // 바꾸면 모든 기기 로그인을 끊고(refresh token 삭제), 로그인 실패 잠금도 푼다 (본인 확인을 마쳤으니)
    @Override
    @Transactional
    public void resetPassword(PasswordResetRequest request) {
        MemberDto member = resetTarget(request.getEmail());
        String email = member.getEmail();
        if (!emailVerificationService.isVerified(email)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "EMAIL_NOT_VERIFIED", "이메일 인증을 먼저 완료해 주세요.");
        }
        String violation = PasswordPolicy.check(request.getNewPassword(), email);
        if (violation != null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_POLICY", violation);
        }
        memberMapper.updatePasswordHash(member.getId(), passwordEncoder.encode(request.getNewPassword()));
        refreshTokenMapper.deleteByUserId(member.getId());
        loginAttemptLimiter.reset(email);
        emailVerificationService.consume(email);
    }

    // 보완 2 추가: 마이페이지 비밀번호 변경 — 현재 비밀번호 확인 → 회원가입과 같은 규칙 → 저장
    // 모든 refresh token 을 지워 다른 기기 로그인을 끊고, 지금 기기에는 로그인처럼 새 토큰을 발급한다 (로그인 유지)
    @Override
    @Transactional
    public AuthTokens changePassword(Long userId, PasswordChangeRequest request) {
        if (userId == null) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "AUTH_REQUIRED", "로그인이 필요합니다.");
        }
        MemberDto member = memberMapper.findById(userId);
        if (member == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "MEMBER_NOT_FOUND", "회원 정보를 찾을 수 없습니다.");
        }
        if (member.isSocialOnly()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "SOCIAL_ACCOUNT", "구글로 가입한 계정은 비밀번호가 없습니다.");
        }
        if (!passwordEncoder.matches(request.getCurrentPassword(), member.getPasswordHash())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_MISMATCH", "현재 비밀번호가 올바르지 않습니다.");
        }
        if (request.getCurrentPassword().equals(request.getNewPassword())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "SAME_PASSWORD", "현재와 다른 비밀번호를 입력해 주세요.");
        }
        String violation = PasswordPolicy.check(request.getNewPassword(), member.getEmail());
        if (violation != null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PASSWORD_POLICY", violation);
        }
        memberMapper.updatePasswordHash(member.getId(), passwordEncoder.encode(request.getNewPassword()));
        refreshTokenMapper.deleteByUserId(member.getId());
        return issueTokens(member);
    }

    // 비밀번호 찾기 대상 회원: 형식 오류 400, 가입 안 한 이메일 400 EMAIL_NOT_FOUND, 구글로만 가입 400 SOCIAL_ACCOUNT
    // (회원가입 [인증 코드 받기]에서 이미 가입 여부가 드러나므로 여기서 숨겨도 의미가 없다)
    private MemberDto resetTarget(String email) {
        String normalized = email == null ? "" : normalizeEmail(email);
        if (normalized.isEmpty() || normalized.length() > 100 || !normalized.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "이메일 형식이 올바르지 않습니다.");
        }
        MemberDto member = memberMapper.findByEmail(normalized);
        if (member == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "EMAIL_NOT_FOUND", "가입되지 않은 이메일입니다.");
        }
        if (member.isSocialOnly()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "SOCIAL_ACCOUNT", "구글로 가입한 계정입니다. 구글로 로그인해 주세요.");
        }
        return member;
    }

    // 보완 8: 구글 로그인
    // ① 이미 연결된 구글 계정 → 그 회원으로 로그인
    // ② 연결은 없지만 같은 이메일로 가입한 회원 → 자동 연결 후 로그인 (구글이 확인한 이메일이라 같은 사람으로 본다)
    // ③ 처음 온 사람 → 가입 대기 번호를 주고 추가 정보 입력 화면으로 (보완 5 필수 항목 · 만 18세 확인)
    @Override
    @Transactional
    public GoogleLoginResult googleLogin(String idToken) {
        GoogleTokenVerifier.GoogleUser google = googleTokenVerifier.verify(idToken);

        Long linkedUserId = socialAccountMapper.findUserId(GOOGLE, google.sub());
        if (linkedUserId != null) {
            MemberDto member = memberMapper.findById(linkedUserId);
            if (member != null) {
                return new GoogleLoginResult(issueTokens(member), null);
            }
        }

        MemberDto sameEmail = memberMapper.findByEmail(google.email());
        if (sameEmail != null) {
            socialAccountMapper.insert(sameEmail.getId(), GOOGLE, google.sub(), google.email());
            loginAttemptLimiter.reset(google.email()); // 구글로 본인 확인이 됐으니 비밀번호 실패 기록은 지운다
            return new GoogleLoginResult(issueTokens(sameEmail), null);
        }

        String signupToken = googleSignupStore.save(google);
        return new GoogleLoginResult(null,
                new GoogleLoginResult.SignupRequired(signupToken, google.email(), google.name()));
    }

    // 보완 8: 추가 정보로 가입 — 회원가입과 같은 검사(만 18세 · 닉네임 중복), 비밀번호 · 이메일 인증은 없다 (구글이 확인)
    @Override
    @Transactional
    public AuthTokens googleSignup(GoogleSignupRequest request) {
        GoogleSignupStore.Pending pending = googleSignupStore.take(request.getSignupToken());
        if (pending == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "GOOGLE_SIGNUP_EXPIRED", "시간이 지났습니다. 구글 로그인을 다시 시도해 주세요.");
        }
        if (Period.between(request.getBirthDate(), LocalDate.now()).getYears() < MIN_SIGNUP_AGE) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "AGE_RESTRICTED",
                    "만 " + MIN_SIGNUP_AGE + "세 이상만 가입할 수 있습니다. (운전면허 취득 가능 나이 기준)");
        }
        // 추가 정보를 입력하는 사이 같은 이메일로 가입했으면 그 회원에 연결한다
        MemberDto existing = memberMapper.findByEmail(pending.email());
        if (existing != null) {
            socialAccountMapper.insert(existing.getId(), GOOGLE, pending.sub(), pending.email());
            return issueTokens(existing);
        }
        String nickName = request.getNickName().trim();
        checkNickNameWords(nickName); // 보완 3 추가: 금지어
        if (memberMapper.countByNickName(nickName) > 0) {
            throw nickNameDuplicated();
        }

        MemberDto member = new MemberDto();
        member.setEmail(pending.email());
        member.setPasswordHash(MemberDto.SOCIAL_ONLY_PASSWORD); // 비밀번호 없음 → 이메일 · 비밀번호 로그인은 항상 실패
        member.setNickName(nickName);
        member.setRole(DEFAULT_ROLE);
        try {
            memberMapper.insert(member);
        } catch (DuplicateKeyException e) {
            String reason = String.valueOf(e.getMessage());
            throw reason.contains("uq_users_nick_name") ? nickNameDuplicated() : emailDuplicated();
        }

        UserProfileDto profile = new UserProfileDto();
        profile.setUserId(member.getId());
        profile.setPhone(request.getPhone().replace("-", ""));
        profile.setBirthDate(request.getBirthDate());
        profile.setGender(request.getGender());
        userProfileMapper.insert(profile);

        socialAccountMapper.insert(member.getId(), GOOGLE, pending.sub(), pending.email());
        return issueTokens(member);
    }

    @Override
    @Transactional
    public AuthTokens login(LoginRequest request, String clientIp) {
        String email = normalizeEmail(request.getEmail());

        // 보완 6: 5번 틀려 잠긴 이메일은 비밀번호를 보지 않고 거절한다 (잠금 10분)
        throwIfLocked(email);

        // 보완 6: 3번 이상 틀렸으면 비밀번호를 보기 전에 reCAPTCHA 부터 확인한다 (자동 대입 공격 차단)
        if (loginAttemptLimiter.isCaptchaRequired(email)) {
            String token = request.getRecaptchaToken();
            if (token == null || token.isBlank()) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "CAPTCHA_REQUIRED", "로봇이 아님을 확인해 주세요.");
            }
            if (!recaptchaVerifier.verify(token, clientIp)) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "CAPTCHA_FAILED", "로봇 확인에 실패했습니다. 다시 체크해 주세요.");
            }
        }

        MemberDto member = memberMapper.findByEmail(email);

        // 이메일이 없을 때와 비밀번호가 틀렸을 때 같은 메시지를 쓴다 → 어떤 이메일이 가입되어 있는지 알려 주지 않기 위해
        if (member == null || !passwordEncoder.matches(request.getPassword(), member.getPasswordHash())) {
            loginAttemptLimiter.recordFailure(email);
            throwIfLocked(email); // 이번이 5번째 실패면 잠금 안내
            // 이번 실패로 기준(3번)을 넘었으면 화면에 reCAPTCHA 를 띄우라고 알린다
            if (loginAttemptLimiter.isCaptchaRequired(email)) {
                // 4번째 실패면 잠금 전 마지막 기회라고 알린다
                String warning = loginAttemptLimiter.failureCount(email) == LoginAttemptLimiter.LOCK_LIMIT - 1
                        ? " 한 번 더 틀리면 10분 동안 로그인할 수 없습니다."
                        : " 로봇이 아님을 확인해 주세요.";
                throw new ApiException(HttpStatus.UNAUTHORIZED, "CAPTCHA_REQUIRED",
                        "이메일 또는 비밀번호가 올바르지 않습니다." + warning);
            }
            throw new ApiException(HttpStatus.UNAUTHORIZED, "LOGIN_FAILED", "이메일 또는 비밀번호가 올바르지 않습니다.");
        }

        loginAttemptLimiter.reset(email);
        return issueTokens(member);
    }

    @Override
    @Transactional
    public AuthTokens refresh(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw refreshInvalid(); // 쿠키가 없음 = 로그인한 적 없거나 로그아웃한 브라우저
        }

        RefreshTokenDto saved = refreshTokenMapper.findByToken(refreshToken);
        // DB 에 없으면 로그아웃했거나 이미 한 번 쓴(교체된) 토큰, 기간이 지났으면 만료된 토큰
        if (saved == null || saved.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw refreshInvalid();
        }

        // 한 번 쓴 refresh token 은 지우고 새로 발급한다 (rotation → 훔친 토큰을 오래 쓰지 못하게)
        // 같은 토큰으로 동시에 두 번 요청이 와도 지우기에 성공한 한 요청만 통과한다
        if (refreshTokenMapper.deleteByToken(refreshToken) == 0) {
            throw refreshInvalid();
        }

        MemberDto member = memberMapper.findById(saved.getUserId());
        if (member == null) {
            throw refreshInvalid();
        }
        return issueTokens(member);
    }

    @Override
    @Transactional
    public void logout(String refreshToken) {
        if (refreshToken != null && !refreshToken.isBlank()) {
            refreshTokenMapper.deleteByToken(refreshToken); // DB 에서 지우면 그 refresh token 으로는 더 이상 재발급할 수 없다
        }
    }

    // access token(JWT) 과 refresh token(무작위 문자열)을 함께 발급한다
    private AuthTokens issueTokens(MemberDto member) {
        // 회원 번호와 역할을 담은 access token(JWT) 발급 (유효 시간: application.yml 의 jwt.access-token-validity)
        String accessToken = jwtProvider.createAccessToken(member.getId(), member.getRole());

        // refresh token 은 JWT 가 아니라 추측할 수 없는 무작위 값(UUID)이고, DB 에 저장해 두고 비교한다
        RefreshTokenDto refresh = new RefreshTokenDto();
        refresh.setUserId(member.getId());
        refresh.setToken(UUID.randomUUID().toString());
        refresh.setExpiresAt(LocalDateTime.now().plus(jwtProvider.getRefreshTokenValidity()));
        refreshTokenMapper.insert(refresh);

        return new AuthTokens(accessToken, refresh.getToken(), MemberResponse.from(member));
    }

    private ApiException refreshInvalid() {
        return new ApiException(HttpStatus.UNAUTHORIZED, "REFRESH_INVALID", "다시 로그인해 주세요.");
    }

    // 앞뒤 공백을 지우고 소문자로 맞춘다 → "User@Example.com " 과 "user@example.com" 을 같은 이메일로 본다
    // 회원가입과 로그인이 같은 규칙을 써야 대소문자를 다르게 입력해도 로그인된다
    private String normalizeEmail(String email) {
        return email.trim().toLowerCase();
    }

    private ApiException emailDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "EMAIL_DUPLICATED", "이미 가입된 이메일입니다.");
    }

    // 보완 3 추가: 닉네임 금지어(운영자 사칭 · 욕설)면 400 NICKNAME_FORBIDDEN
    private void checkNickNameWords(String nickName) {
        String message = NickNamePolicy.check(nickName);
        if (message != null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "NICKNAME_FORBIDDEN", message);
        }
    }

    private ApiException nickNameDuplicated() {
        return new ApiException(HttpStatus.CONFLICT, "NICKNAME_DUPLICATED", "이미 사용 중인 닉네임입니다.");
    }
}
