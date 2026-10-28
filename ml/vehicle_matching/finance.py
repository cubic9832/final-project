"""Versioned experimental assumptions, not lending eligibility decisions."""
import math
from dataclasses import asdict, dataclass, replace

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
    cost_importance: int = 3
    space_importance: int = 3
    minimum_seats: int = 0
    preferred_size: str = 'any'
    financing_mode: str = 'fixed'
    fuel_importance: int = 3
    seating_importance: int = 3
    purpose_importance: int = 1
    purchase_price_ceiling: float = 0
    preferred_body_type: str = 'any'
    body_importance: int = 3

    def __post_init__(self):
        if self.financing_mode not in ('fixed', 'automatic', 'recommendation'):
            raise ValueError('Invalid financing mode')
        for name in ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets',
                     'down_payment', 'emergency_reserve', 'monthly_savings', 'annual_distance',
                     'annual_rate', 'minimum_buffer', 'purchase_price_ceiling'):
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
        if self.emergency_reserve > self.liquid_assets or self.down_payment > self.liquid_assets - self.emergency_reserve:
            raise ValueError('down_payment + emergency_reserve exceeds liquid_assets')
        for weight in (self.body_importance, self.cost_importance, self.space_importance, self.fuel_importance,
                       self.seating_importance, self.purpose_importance):
            if type(weight) is not int or not 1 <= weight <= 5:
                raise ValueError('Importance must be an integer from 1 to 5')
        if type(self.minimum_seats) is not int or not 0 <= self.minimum_seats <= 9:
            raise ValueError('Invalid minimum seating capacity')
        if self.preferred_size not in ('any', 'small', 'medium', 'large'):
            raise ValueError('Unknown preferred size')
        if self.preferred_body_type not in ('any', 'SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP', 'COUPE', 'CONVERTIBLE', 'ROADSTER', 'OTHER'):
            raise ValueError('Unknown preferred body type')


@dataclass(frozen=True)
class Assumptions:
    version: str = 'cost-utility-v2.3-base-cost-only'
    acquisition_ratio: float = 0
    monthly_insurance: float = 100000
    monthly_maintenance: float = 60000
    monthly_tax: float = 25000
    # Accepted only for historical bundle loading; no longer used in calculations.
    stress_rate_addition: float = 0
    stress_running_multiplier: float = 1
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
        return {key: value for key, value in asdict(self).items() if not key.startswith('stress_')}


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
    recommendation = profile.financing_mode == 'recommendation'
    if profile.financing_mode == 'recommendation':
        # Recommendation never creates a loan. Only currently spendable cash
        # may pay the purchase price; income is checked against running costs.
        profile = replace(profile, down_payment=min(vehicle.price, profile.liquid_assets-profile.emergency_reserve),
                          months=0, annual_rate=0, financing_mode='automatic')
    fuel_index = FUELS.index(vehicle.fuel)
    low, high = assumptions.efficiency_ranges[fuel_index]
    efficiency = vehicle.efficiency or (low + high) / 2
    energy = assumptions.energy_prices[fuel_index]
    running = profile.annual_distance / 12 / efficiency * energy
    fixed = sum(getattr(vehicle, key) if getattr(vehicle, key) is not None else getattr(assumptions, key) for key in ("monthly_insurance", "monthly_maintenance", "monthly_tax"))
    total_price = round(vehicle.price, 2)
    principal = max(0, round(total_price - profile.down_payment, 2))
    payment = 0.0 if recommendation else installment(principal, profile.annual_rate, profile.months)
    if recommendation:
        payment = math.ceil(round(payment,2))
        running = math.ceil(round(running+fixed,2))-fixed
    monthly_cost = payment + running + fixed
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    reasons = []
    if profile.purchase_price_ceiling and total_price>profile.purchase_price_ceiling:
        reasons.append('purchase-price-ceiling')
    if profile.months == 0 and principal > 0:
        reasons.append('insufficient-cash-for-outright-purchase')
    cash_after_purchase = max(0, profile.liquid_assets - profile.emergency_reserve - total_price)
    monthly_drawdown = max(0, monthly_cost - available)
    required_drawdown = max(0, monthly_cost + profile.minimum_buffer - available)
    reserve_months = 12
    asset_supported = recommendation and required_drawdown > 0 and cash_after_purchase >= required_drawdown * reserve_months
    if available - monthly_cost < profile.minimum_buffer and not asset_supported:
        reasons.append('insufficient-monthly-buffer')
    # JSON does not support Infinity. Infeasible cash purchases have no installment estimate.
    def finite(value):
        return round(value, 2) if math.isfinite(value) else None
    return {'eligible': not reasons, 'exclusions': reasons, 'total_purchase_cost': round(total_price, 2),
            'funding_source': 'assets' if asset_supported else 'income',
            'monthly_asset_drawdown': round(monthly_drawdown, 2) if recommendation else None,
            'asset_runway_months': round(cash_after_purchase / monthly_drawdown, 1) if recommendation and monthly_drawdown > 0 else None,
            'required_asset_coverage_months': reserve_months if recommendation else None,
            'financing_months': profile.months, 'financing_annual_rate': profile.annual_rate,
            'principal': round(principal, 2), 'monthly_payment': finite(payment), 'monthly_running_cost': round(running + fixed, 2),
            # Historical feature slots reuse the base values, without a second scenario.
            'monthly_total': finite(monthly_cost), 'stress_monthly_total': finite(monthly_cost),
            'remaining_monthly': finite(available - monthly_cost), 'stress_remaining_monthly': finite(available - monthly_cost),
            'efficiency_estimated': vehicle.efficiency is None or vehicle.efficiency_reference_only}
