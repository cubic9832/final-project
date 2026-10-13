import { ArrowRight, BriefcaseBusiness, GraduationCap, Laptop, Users, House } from 'lucide-react';
import theme from '../../styles/theme';
import { formatAmount } from '../vehicle/vehicleData';

const artwork = { starter: GraduationCap, employee: BriefcaseBusiness, couple: Users, family: House, freelancer: Laptop };

export default function ProfilePresetCard({ preset, onSelect }) {
  const Illustration = artwork[preset.id];
  return (
    <button type="button" className="profile-preset-card" onClick={() => onSelect(preset)} aria-label={`${preset.name} 예시로 차량 비교하기`}>
      <span className="profile-preset-art" aria-hidden="true"><Illustration size={theme.iconSize.lg} strokeWidth={1.5} /></span>
      <span className="profile-preset-name">{preset.name}</span>
      <span className="profile-preset-occupation">{preset.occupation}</span>
      <span className="profile-preset-income"><span>{preset.incomeLabel}</span><strong>{formatAmount(preset.annualIncome)}</strong></span>
      <span className="profile-preset-balances">
        <span><span>자산</span><strong>{formatAmount(preset.assets)}</strong></span>
        <span><span>부채</span><strong>{formatAmount(preset.debtBalance)}</strong></span>
      </span>
      <span className="profile-preset-action">차량 3대 비교하기 <ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></span>
    </button>
  );
}
