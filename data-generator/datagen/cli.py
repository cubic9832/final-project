import argparse
from pathlib import Path

from datagen.generate import generate
from datagen.layout import SEGMENTS, default_output_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="datagen",
        description="시드 분포로 차량 보유자 더미 데이터를 생성합니다.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate", help="보유자, 구매, 요약을 생성합니다")
    generate_parser.add_argument("--segment", required=True, choices=SEGMENTS, help="domestic-car 또는 imported-car")
    generate_parser.add_argument("--rows", required=True, type=int, help="생성 건수")
    generate_parser.add_argument("--seed", type=int, default=42, help="난수 시드")
    generate_parser.add_argument("--output", type=Path, help="출력 디렉터리. 기본값은 data/generated/{segment}")
    args = parser.parse_args(argv)
    if args.rows < 1:
        parser.error("--rows 는 1 이상이어야 합니다")
    output = args.output or default_output_directory(args.segment)
    generate(segment=args.segment, rows=args.rows, seed=args.seed, output_dir=output)
    print(f"{args.segment} {args.rows}건을 생성했습니다: {output}")
    return 0
