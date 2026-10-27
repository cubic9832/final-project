"""Required seating, then importance-ordered preference penalties, then raw ML."""
from vehicle_matching.preferences import SIZE_BANDS

POLICY = 'required-seats-preference-priority-ml-v1'

def seating_status(profile, vehicle):
    if not profile.minimum_seats:
        return 'match'
    if vehicle.seats_status == 'official-reference-conflict':
        return 'unknown'
    if vehicle.seats is None:
        return 'unknown'
    if vehicle.seats >= profile.minimum_seats:
        return 'match'
    if vehicle.seat_options and max(vehicle.seat_options) >= profile.minimum_seats:
        return 'unknown'
    return 'insufficient'

def preference_penalties(profile, vehicle):
    items = []
    if profile.preferred_fuel:
        fuel = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
        items.append(('fuel', profile.fuel_importance, float(fuel != profile.preferred_fuel)))
    if profile.preferred_body_type != 'any':
        items.append(('body', profile.body_importance, float(vehicle.body_type != profile.preferred_body_type)))
    if profile.preferred_size != 'any':
        lower, upper = SIZE_BANDS[profile.preferred_size]
        # Unknown length cannot outrank any known length. Distance remains continuous.
        penalty = 10.0 if vehicle.length_mm is None else max(lower - vehicle.length_mm, vehicle.length_mm - upper, 0) / 1000
        items.append(('space', profile.space_importance, penalty))
    return items

def ranking_key(profile, vehicle, score):
    items = preference_penalties(profile, vehicle)
    # Equal importance shares one penalty group; higher importance always comes first.
    return tuple(sum(p for _, w, p in items if w == weight) for weight in range(5, 0, -1)) + (-score, vehicle.id)
