from pathlib import Path

DOMESTIC_CARS = "domestic-car"
IMPORTED_CARS = "imported-car"
SEGMENTS = (DOMESTIC_CARS, IMPORTED_CARS)

PROFILE_PREFIX = {
    DOMESTIC_CARS: "GD",
    IMPORTED_CARS: "GI",
}

SPEC_PREFIX = {
    DOMESTIC_CARS: "GDC",
    IMPORTED_CARS: "GIC",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def seed_directory(segment: str) -> Path:
    return repo_root() / "data" / "seed" / segment


def default_output_directory(segment: str) -> Path:
    return repo_root() / "data" / "generated" / segment
