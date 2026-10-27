"""Price snapshot ingestion. Missing efficiency stays unknown, never zero."""
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / 'data/vehicles/csv/domestic-vehicle-details.csv'
FUELS = ('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC')


@dataclass(frozen=True)
class Vehicle:
    id: str
    brand: str
    model: str
    trim: str
    year: str
    price: float
    fuel: str
    efficiency: float | None
    source_url: str
    checked_on: str
    # A price snapshot is not proof of present availability or manual verification.
    quality: str = 'automatically-extracted-snapshot'
    length_mm: int | None = None
    seats: int | None = None
    space_source_url: str | None = None
    seat_options: tuple[int, ...] = ()
    seats_source_url: str | None = None
    original_fuel: str | None = None
    source_note: str | None = None
    seats_status: str | None = None
    seats_label: str | None = None
    seats_note: str | None = None
    default_configuration: str | None = None
    efficiency_reference_only: bool = False
    body_type: str | None = None
    body_source_urls: tuple[str, ...] = ()
    image_url: str | None = None

    def __post_init__(self):
        import math
        if self.body_type not in (None, 'SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP'):
            raise ValueError('Unknown vehicle body type')
        if not all((self.id, self.brand, self.model, self.trim, self.source_url, self.checked_on)):
            raise ValueError('Vehicle identity and provenance are required')
        if self.fuel not in FUELS or not math.isfinite(self.price) or self.price <= 0:
            raise ValueError('Unsupported fuel or invalid vehicle price')
        if self.efficiency is not None and (not math.isfinite(self.efficiency) or self.efficiency <= 0):
            raise ValueError('Efficiency must be positive or unknown')
        if self.length_mm is not None and (type(self.length_mm) is not int or not 2500 <= self.length_mm <= 6000):
            raise ValueError('Invalid vehicle length')
        if self.seats is not None and (type(self.seats) is not int or not 1 <= self.seats <= 15):
            raise ValueError('Invalid seating capacity')
        if any(type(value) is not int or not 1 <= value <= 15 for value in self.seat_options):
            raise ValueError('Invalid seating options')


def load_csv(path=DEFAULT_CSV):
    vehicles, rejected, seen, ambiguous = [], [], set(), set()
    source_rows = 0
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        for index, row in enumerate(csv.DictReader(stream), 2):
            source_rows += 1
            try:
                fuel = row['연료']
                efficiency = float(row['복합연비_전비']) if row['복합연비_전비'] else None
                unit = 'km/kWh' if fuel == 'ELECTRIC' else 'km/L'
                if efficiency is not None and row['연비_전비단위'] != unit:
                    raise ValueError('Efficiency unit mismatch')
                identity = [row[key] for key in ('브랜드', '모델', '연식', '트림', '엔진_파워트레인', '기본휠_인치')]
                vehicle_id = 'V-' + hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()[:16]
                vehicle = Vehicle(vehicle_id, row['브랜드'], row['모델'], row['트림'], row['연식'],
                                  float(row['판매가격_원']), fuel, efficiency, row['출처_URL'], row['확인일'])
                if vehicle_id in seen:
                    # Do not arbitrarily keep the first/cheapest conflicting price row.
                    ambiguous.add(vehicle_id)
                    raise ValueError('Ambiguous duplicate configuration identity; all matching rows excluded')
                seen.add(vehicle_id)
                vehicles.append(vehicle)
            except (ValueError, KeyError) as error:
                rejected.append({'row': index, 'reason': str(error)})
    vehicles = [v for v in vehicles if v.id not in ambiguous]
    if not vehicles:
        raise ValueError('No usable vehicles in catalog')
    return vehicles, {'source': str(Path(path).relative_to(ROOT)) if Path(path).is_relative_to(ROOT) else str(path),
                      'source_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                      'accepted': len(vehicles), 'model_names': len({(v.brand, v.model) for v in vehicles}),
                      'source_rows': source_rows, 'excluded_rows': source_rows - len(vehicles),
                      'unknown_efficiency': sum(v.efficiency is None for v in vehicles),
                      'ambiguous_identities_removed': len(ambiguous), 'rejected': rejected}


def save_catalog(path, vehicles):
    Path(path).write_text(json.dumps([asdict(v) for v in vehicles], ensure_ascii=False, indent=2), encoding='utf-8')


def catalog_fingerprint(path):
    """Semantic hash survives Git's Windows CRLF / Linux LF conversion."""
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def read_catalog(path):
    vehicles = [Vehicle(**row) for row in json.loads(Path(path).read_text(encoding='utf-8'))]
    if not vehicles or len({v.id for v in vehicles}) != len(vehicles):
        raise ValueError('Empty catalog or duplicate IDs')
    return vehicles
