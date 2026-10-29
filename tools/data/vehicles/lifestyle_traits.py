"""Evidence-backed lifestyle traits; unknowns never receive random values."""
import hashlib
import json
import math
from pathlib import Path

from vehicle_matching.catalog import ROOT

DIMENSIONS = ('exterior_sportiness', 'exterior_angularity', 'interior_minimalism',
              'ride_comfort', 'acceleration_performance', 'seat_capacity', 'compactness')
DEFAULT_REVIEWS = ROOT / 'data/vehicles/lifestyle-evidence-v2-20261028/reviews.json'


def read_reviews(path=DEFAULT_REVIEWS):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_traits(cars, reviews):
    """Apply exact family/trim/year selectors; keep raw evidence alongside scores."""
    result = {}
    for car in cars:
        values = dict.fromkeys(DIMENSIONS)
        evidence = {}
        for name, field, source, transform in (
            ('seat_capacity', 'seats', 'seats_source_url', lambda n: min(1, max(0, (n - 2) / 7))),
            ('compactness', 'length_mm', 'space_source_url', lambda n: min(1, max(0, (6000 - n) / 3500))),
        ):
            raw = car.get(field)
            # A source URL alone does not resolve seating conflicts or user-only claims.
            verified = field != 'seats' or car.get('seats_status') == 'official-source-verified'
            if raw is not None and car.get(source) and verified:
                if not math.isfinite(raw) or (field == 'seats' and not 1 <= raw <= 15) or (field == 'length_mm' and not 2500 <= raw <= 6000):
                    raise ValueError(f'Invalid {field}: {car["id"]}')
                values[name] = transform(raw)
                evidence[name] = {'kind': 'official-specification-derived', 'raw_field': field,
                                  'raw_value': raw, 'source_url': car[source],
                                  'checked_on': car.get('checked_on'),
                                  'limitation': 'Capacity/length only; not cargo volume, legroom or comfort.'}
        for review in reviews['reviews']:
            if (car['brand'], car['model']) != (review['brand'], review['model']):
                continue
            if review.get('trims') is not None and car['trim'] not in review['trims']:
                continue
            if review.get('years') is not None and car.get('year') not in review['years']:
                continue
            for name, entry in review['traits'].items():
                if name not in DIMENSIONS:
                    raise ValueError(f'Unknown trait: {name}')
                if values[name] is not None:
                    raise ValueError(f'Conflicting evidence for {car["id"]}/{name}')
                if entry['kind'] not in ('visual-review', 'official-acceleration'):
                    raise ValueError('Unsupported evidence kind')
                if not entry.get('source_url') or not entry.get('basis'):
                    raise ValueError('Evidence source and basis required')
                if entry['kind'] == 'visual-review':
                    if name not in ('exterior_sportiness', 'exterior_angularity', 'interior_minimalism'):
                        raise ValueError('Images do not establish performance or ride comfort')
                    image = (ROOT / entry['image_path']).resolve()
                    if not image.is_relative_to(ROOT.resolve()) or file_hash(image) != entry['image_sha256']:
                        raise ValueError('Review image hash mismatch')
                    value = entry['value']
                    if value not in (0, .5, 1):
                        raise ValueError('Visual rubric is ordinal: 0, .5 or 1')
                else:
                    if name != 'acceleration_performance' or not 1 <= entry['seconds_0_100'] <= 30:
                        raise ValueError('Invalid acceleration evidence')
                    value = min(1, max(0, (12 - entry['seconds_0_100']) / 10))
                values[name] = value
                evidence[name] = dict(entry, scope=review['scope'])
        # Body classification is an observed category, never a proxy for performance.
        body_sources = car.get('body_source_urls') or [car.get('source_url')]
        body = car.get('body_type') if any(body_sources) else None
        for review in reviews.get('body_reviews', []):
            if (car['brand'], car['model']) == (review['brand'], review['model']):
                body, body_sources = review['body_type'], [review['source_url']]
        result[car['id']] = {'values': values, 'evidence': evidence,
                            'body_type': body, 'body_sources': body_sources}
    return result


def pair_masks(a, b):
    return [int(a['values'][name] is not None and b['values'][name] is not None) for name in DIMENSIONS]
