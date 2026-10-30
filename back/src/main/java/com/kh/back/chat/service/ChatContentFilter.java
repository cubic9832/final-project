package com.kh.back.chat.service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

/**
 * 8단계: 상담 메시지 금칙어 검사 (욕설 · 패드립 · 성적인 표현). 걸리면 보내지 못한다 — 회원 · 상담원 모두.
 * 단어 목록은 resources/chat/blocked-words.txt, 괜찮은 말(오탐 예외)은 allowed-words.txt (돈 드는 AI 판별은 쓰지 않는다)
 * 비교 방법: 소문자로 → 띄어쓰기 · 숫자 · 기호 빼기 → 괜찮은 말 지우기 → 금칙어가 들어 있나
 */
@Component
public class ChatContentFilter {

    private final List<String> blockedWords;
    private final List<String> allowedWords;

    public ChatContentFilter() {
        this.blockedWords = load("chat/blocked-words.txt");
        this.allowedWords = load("chat/allowed-words.txt");
    }

    public boolean isBlocked(String text) {
        String compact = normalize(text);
        for (String allowed : allowedWords) {
            compact = compact.replace(allowed, ""); // "대출 시 발생" 의 "시발생" 같은 말은 먼저 지운다
        }
        for (String word : blockedWords) {
            if (compact.contains(word)) {
                return true;
            }
        }
        return false;
    }

    // 한글(완성형 · 자음 모음)과 영문만 남긴다 → "씨 발", "씨1발", "f.u.c.k" 도 같은 글자로 비교된다
    static String normalize(String text) {
        return text.toLowerCase(Locale.ROOT).replaceAll("[^가-힣ㄱ-ㅎㅏ-ㅣa-z]", "");
    }

    // 한 줄에 하나, 빈 줄과 # 설명은 건너뛴다. 목록 단어도 같은 방법으로 다듬어 둔다
    private static List<String> load(String path) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new ClassPathResource(path).getInputStream(), StandardCharsets.UTF_8))) {
            return reader.lines()
                    .map(String::strip)
                    .filter(line -> !line.isEmpty() && !line.startsWith("#"))
                    .map(ChatContentFilter::normalize)
                    .filter(word -> !word.isEmpty())
                    .toList();
        } catch (IOException e) {
            throw new UncheckedIOException("금칙어 목록을 읽지 못했습니다: " + path, e);
        }
    }
}
