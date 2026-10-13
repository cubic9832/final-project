import { ArrowRight } from 'lucide-react';
import theme from '../../styles/theme';
import { formatAmount } from '../vehicle/vehicleData';

import starterImage from '../../assets/profiles/starter.webp';
import employeeImage from '../../assets/profiles/employee.webp';
import coupleImage from '../../assets/profiles/couple.webp';
import familyImage from '../../assets/profiles/family.webp';
import freelancerImage from '../../assets/profiles/freelancer.webp';

const artwork = { starter: starterImage, employee: employeeImage, couple: coupleImage, family: familyImage, freelancer: freelancerImage };

export default function ProfilePresetCard({ preset, onSelect }) {
  return (
    <button type="button" className="profile-preset-card" onClick={() => onSelect(preset)} aria-label={`${preset.name} 예시로 차량 비교하기`}>
      <span className="profile-preset-art" aria-hidden="true"><img decoding="async" src={artwork[preset.id]} alt="" width="256" height="256" /></span>
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
