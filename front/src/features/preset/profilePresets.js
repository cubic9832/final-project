export const profilePresets = [
  { id: 'starter', name: '사회초년생', occupation: '신입 사무직', annualIncome: 3000, incomeLabel: '연봉', assets: 800, debtBalance: 1000, vehicleIds: ['ray', 'casper', 'avante'], conditions: { income: 230, expenses: 120, debt: 15, downPayment: 300, limit: 40 } },
  { id: 'employee', name: '직장인', occupation: '경력 사무직', annualIncome: 5000, incomeLabel: '연봉', assets: 3000, debtBalance: 500, vehicleIds: ['avante', 'seltos', 'kona'], conditions: { income: 360, expenses: 150, debt: 10, downPayment: 1000, limit: 60 } },
  { id: 'couple', name: '맞벌이 부부', occupation: '부부 직장인', annualIncome: 8000, incomeLabel: '합산 연봉', assets: 6000, debtBalance: 3000, vehicleIds: ['avante', 'seltos', 'arkana'], conditions: { income: 560, expenses: 250, debt: 40, downPayment: 1500, limit: 80 } },
  { id: 'family', name: '자녀 있는 가정', occupation: '외벌이 직장인', annualIncome: 6000, incomeLabel: '가구 연봉', assets: 5000, debtBalance: 5000, vehicleIds: ['seltos', 'kona', 'arkana'], conditions: { income: 430, expenses: 250, debt: 60, downPayment: 1000, limit: 60 } },
  { id: 'freelancer', name: '프리랜서', occupation: '디자인·개발', annualIncome: 4500, incomeLabel: '연 소득', assets: 2000, debtBalance: 1500, vehicleIds: ['ray', 'avante', 'arkana'], conditions: { income: 320, expenses: 160, debt: 25, downPayment: 700, limit: 50 } },
];

export function findProfilePreset(id) {
  return profilePresets.find((preset) => preset.id === id);
}

export function applyProfilePreset(preset) {
  return {
    conditions: { ...preset.conditions, cash: preset.assets, condition: '상관없음' },
    comparison: [...preset.vehicleIds],
  };
}
