"""Versioned experimental assumptions, not lending eligibility decisions."""
import math
from dataclasses import asdict, dataclass

from vehicle_matching.catalog import FUELS, Vehicle

PURPOSES = ('commute', 'leisure', 'family', 'business')


@dataclass(frozen=True)
class Profile:
    monthly_income: float
    monthly_expenses: float
    existing_monthly_payment: float
    liquid_assets: float
    down_payment: float
    emergency_reserve: float
    monthly_savings: float
    annual_distance: float
    months: int
    annual_rate: float = 0.06
    minimum_buffer: float = 0
    purpose: str = 'commute'
    preferred_fuel: str | None = None
    charging_available: bool = False

    def __post_init__(self):
        for name in ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets',
                     'down_payment', 'emergency_reserve', 'monthly_savings', 'annual_distance',
                     'annual_rate', 'minimum_buffer'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{name}: finite nonnegative amount required')
        if isinstance(self.months, bool) or not isinstance(self.months, int) or self.months not in (0, 12, 24, 36, 48, 60, 72):
            raise ValueError('months: choose 0, 12, 24, 36, 48, 60 or 72')
        if self.annual_rate > 1 or self.purpose not in PURPOSES:
            raise ValueError('Invalid rate or purpose')
        if self.preferred_fuel is not None and self.preferred_fuel not in FUELS:
            raise ValueError('Unknown preferred fuel')
        if type(self.charging_available) is not bool:
            raise ValueError('charging_available must be boolean')
        if self.down_payment + self.emergency_reserve > self.liquid_assets:
            raise ValueError('down_payment + emergency_reserve exceeds liquid_assets')


@dataclass(frozen=True)
class Assumptions:
    version: str = 'cost-utility-v2.1'
    acquisition_ratio: float = 0.07
    monthly_insurance: float = 100000
    monthly_maintenance: float = 60000
    monthly_tax: float = 25000
    stress_rate_addition: float = 0.03
    stress_running_multiplier: float = 1.25
    # Unknown efficiency is an interval assumption, never a vehicle specification.
    efficiency_ranges: tuple = ((8, 14), (14, 22), (10, 16), (6, 10), (3, 6))
    energy_prices: tuple = (1800, 1800, 1700, 1100, 350)

    def __post_init__(self):
        if len(self.efficiency_ranges) != len(FUELS) or len(self.energy_prices) != len(FUELS):
            raise ValueError('Fuel assumptions layout mismatch')
        numbers = [self.acquisition_ratio, self.monthly_insurance, self.monthly_maintenance, self.monthly_tax,
                   self.stress_rate_addition, self.stress_running_multiplier, *self.energy_prices]
        if any(not math.isfinite(x) or x < 0 for x in numbers) or self.stress_running_multiplier < 1:
            raise ValueError('Invalid cost assumptions')
        if any(len(pair) != 2 or not 0 < pair[0] <= pair[1] for pair in self.efficiency_ranges):
            raise ValueError('Invalid efficiency intervals')

    def to_dict(self):
        return asdict(self)


def installment(principal, rate, months):
    if principal <= 0:
        return 0.0
    if months == 0:
        return math.inf
    if rate == 0:
        return principal / months
    monthly = rate / 12
    return principal * monthly / (1 - (1 + monthly) ** -months)


def assess(profile: Profile, vehicle: Vehicle, assumptions=Assumptions()):
    fuel_index = FUELS.index(vehicle.fuel)
    low, high = assumptions.efficiency_ranges[fuel_index]
    efficiency = vehicle.efficiency or (low + high) / 2
    worst_efficiency = vehicle.efficiency or low
    energy = assumptions.energy_prices[fuel_index]
    running = profile.annual_distance / 12 / efficiency * energy
    worst_running = profile.annual_distance / 12 / worst_efficiency * energy
    fixed = assumptions.monthly_insurance + assumptions.monthly_maintenance + assumptions.monthly_tax
    total_price = round(vehicle.price * (1 + assumptions.acquisition_ratio), 2)
    principal = max(0, round(total_price - profile.down_payment, 2))
    payment = installment(principal, profile.annual_rate, profile.months)
    stress_payment = installment(principal, profile.annual_rate + assumptions.stress_rate_addition, profile.months)
    monthly_cost = payment + running + fixed
    stress_cost = stress_payment + (worst_running + fixed) * assumptions.stress_running_multiplier
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    reasons = []
    if vehicle.fuel == 'ELECTRIC' and not profile.charging_available:
        reasons.append('charging-unavailable')
    if profile.months == 0 and principal > 0:
        reasons.append('insufficient-cash-for-outright-purchase')
    if available - stress_cost < profile.minimum_buffer:
        reasons.append('insufficient-monthly-buffer-under-stress')
    # JSON does not support Infinity. Infeasible cash purchases have no installment estimate.
    def finite(value):
        return round(value, 2) if math.isfinite(value) else None
    return {'eligible': not reasons, 'exclusions': reasons, 'total_purchase_cost': round(total_price, 2),
            'principal': round(principal, 2), 'monthly_payment': finite(payment), 'monthly_running_cost': round(running + fixed, 2),
            'monthly_total': finite(monthly_cost), 'stress_monthly_total': finite(stress_cost),
            'remaining_monthly': finite(available - monthly_cost), 'stress_remaining_monthly': finite(available - stress_cost),
            'efficiency_estimated': vehicle.efficiency is None}
