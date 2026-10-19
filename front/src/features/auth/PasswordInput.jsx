// 비밀번호 입력칸 + 눈 아이콘 (보완 2 · 보완 목록 ④)
// "비밀번호 표시" 체크박스 대신 입력칸 안의 눈 아이콘으로 보기 / 숨기기. 회원가입 · 로그인이 함께 쓴다.
// 그 밖의 속성(id, value, onChange, className, aria-* 등)은 input 에 그대로 넘긴다.
import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import theme from '../../styles/theme';
import './PasswordInput.css';

export default function PasswordInput(props) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="password-input">
      <input {...props} type={visible ? 'text' : 'password'} />
      <button
        className="password-toggle"
        type="button"
        aria-label={visible ? '비밀번호 숨기기' : '비밀번호 보기'}
        aria-pressed={visible}
        onClick={() => setVisible((prev) => !prev)}
      >
        {visible ? <EyeOff size={theme.iconSize.md} /> : <Eye size={theme.iconSize.md} />}
      </button>
    </div>
  );
}
