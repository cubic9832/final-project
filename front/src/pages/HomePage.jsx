import { Link, useNavigate } from 'react-router-dom';
import ProfilePresetSlider from '../features/preset/ProfilePresetSlider';
import { profilePresets } from '../features/preset/profilePresets';
import './HomePage.css';

export default function HomePage() {
  const navigate = useNavigate();
  return (
    <div className="preset-home">
      <div className="preset-home-heading">
        <span className="preset-home-eyebrow">내 상황에서 시작하는 자동차 비교</span>
        <h1>당신과 가장 가까운 상황은?</h1>
        <p>비슷한 상황을 선택하고, 차량 3대의 구매비용과 유지비를 바로 비교해 보세요.</p>
      </div>
      <ProfilePresetSlider presets={profilePresets} onSelect={(selected) => navigate(`/vehicles/compare?preset=${selected.id}`)} />
      <p className="preset-home-note">서비스 체험용 가상 프로필입니다. 자산은 현금성 자산이며, 비교 결과는 실제 추천이나 금융 심사 결과가 아닙니다.</p>
      <div className="preset-home-direct"><p>내 상황을 직접 입력하고 싶다면</p><Link to="/financial">내 재무 정보로 시작하기</Link></div>
    </div>
  );
}
