import argparse
import json
from pathlib import Path

from recommender.dataset import SEGMENTS, seed_directory
from recommender.evaluate import evaluate_run
from recommender.predict import recommend
from recommender.train import train


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recommender", description="차량 라벨 추천 모델을 학습하고 추론합니다.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="세그먼트 데이터로 학습하고 산출물을 저장합니다")
    train_parser.add_argument("--segment", required=True, choices=SEGMENTS)
    train_parser.add_argument("--data", type=Path, help="owners.csv와 purchases.csv가 있는 디렉터리")
    train_parser.add_argument("--output", type=Path, help="산출물 디렉터리. 기본값은 recommender/runs/{segment}/{시각}")

    predict_parser = subparsers.add_parser("predict", help="프로필 한 건의 상위 차량을 출력합니다")
    predict_parser.add_argument("--run", required=True, type=Path, help="학습 산출물 디렉터리")
    predict_parser.add_argument("--profile", required=True, type=Path, help="프로필 JSON 파일")
    predict_parser.add_argument("--k", type=int, default=3, help="상위 개수")

    evaluate_parser = subparsers.add_parser("evaluate", help="저장된 모델로 평가 분할을 다시 측정합니다")
    evaluate_parser.add_argument("--run", required=True, type=Path)
    evaluate_parser.add_argument("--data", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            directory = train(
                args.data or seed_directory(args.segment),
                segment=args.segment,
                run_dir=args.output,
            )
            print(directory)
            return 0
        if args.command == "predict":
            profile = json.loads(args.profile.read_text(encoding="utf-8"))
            if not isinstance(profile, dict):
                parser.error("--profile 은 객체 JSON이어야 합니다")
            results = recommend(args.run, profile, k=args.k)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return 0
        metrics = evaluate_run(args.run, args.data)
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0
    except ValueError as error:
        parser.error(str(error))
