"""차량 추천 train CLI 호환 진입점."""
import sys

from recommender.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["train", *sys.argv[1:]]))
