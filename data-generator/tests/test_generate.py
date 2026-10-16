import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from datagen.cli import main
from datagen.formulas import monthly_payment, registration_fee
from datagen.generate import generate
from datagen.layout import DOMESTIC_CARS, IMPORTED_CARS, PROFILE_PREFIX, SEGMENTS, SPEC_PREFIX
from datagen.schema import LABEL_BASIS, RULE_VERSION, SYNTHETIC


class GenerateTest(unittest.TestCase):
    def test_generated_rows_keep_identities_and_join(self):
        for segment in SEGMENTS:
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                generate(segment=segment, rows=200, seed=11, output_dir=output)
                owners = _read(output / "owners.csv")
                purchases = _read(output / "purchases.csv")
                summary = _read(output / "owner-summary.csv")
                self.assertEqual(len(owners), 200)
                self.assertEqual(
                    [row["프로필_식별자"] for row in owners],
                    [row["프로필_식별자"] for row in purchases],
                )
                self.assertEqual(owners[0]["프로필_식별자"], f"{PROFILE_PREFIX[segment]}0000001")
                self.assertEqual(purchases[0]["차량사양_식별자"], f"{SPEC_PREFIX[segment]}0000001")
                for owner, purchase in zip(owners, purchases):
                    _assert_pair(self, owner, purchase, seed=11)
                _assert_summary(self, owners, summary)

    def test_same_seed_reproduces_files_and_other_seed_differs(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir, tempfile.TemporaryDirectory() as other_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            other = Path(other_dir)
            generate(segment=DOMESTIC_CARS, rows=30, seed=5, output_dir=first)
            generate(segment=DOMESTIC_CARS, rows=30, seed=5, output_dir=second)
            generate(segment=DOMESTIC_CARS, rows=30, seed=6, output_dir=other)
            for name in ("owners.csv", "purchases.csv", "owner-summary.csv"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            self.assertNotEqual((first / "owners.csv").read_bytes(), (other / "owners.csv").read_bytes())

    def test_single_row_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate(segment=IMPORTED_CARS, rows=1, seed=0, output_dir=output)
            owners = _read(output / "owners.csv")
            self.assertEqual(len(owners), 1)
            self.assertEqual(owners[0]["프로필_식별자"], "GI0000001")

    def test_rejects_non_positive_rows_and_unknown_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                generate(segment=DOMESTIC_CARS, rows=0, seed=1, output_dir=Path(directory))
            with self.assertRaises(ValueError):
                generate(segment="bike", rows=10, seed=1, output_dir=Path(directory))

    def test_cli_writes_output_and_rejects_bad_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            code = main(["generate", "--segment", DOMESTIC_CARS, "--rows", "15", "--seed", "3", "--output", str(output)])
            self.assertEqual(code, 0)
            self.assertTrue((output / "owners.csv").is_file())
            self.assertTrue((output / "purchases.csv").is_file())
            self.assertTrue((output / "owner-summary.csv").is_file())
        with self.assertRaises(SystemExit):
            main(["generate", "--segment", DOMESTIC_CARS, "--rows", "0"])


def _assert_pair(test: unittest.TestCase, owner: dict[str, str], purchase: dict[str, str], seed: int) -> None:
    profile_id = owner["프로필_식별자"]
    cash = int(owner["개인_현금성자산_원"])
    financial = int(owner["개인_기타금융자산_원"])
    deposit = int(owner["개인_주거보증금자산_원"])
    realty = int(owner["개인_부동산자산_원"])
    total_assets = cash + financial + deposit + realty
    loan_balance = int(purchase["차량할부원금_원"]) + int(purchase["기존대출잔액_보정후_원"])
    loan_payment = int(purchase["차량_월상환액_원"]) + int(purchase["기존월상환액_보정후_원"])
    spend = int(owner["개인_평균월주거비_원"]) + int(owner["개인_평균월기타생활소비_원"])
    test.assertEqual(int(owner["개인_총자산_차량제외_원"]), total_assets, profile_id)
    test.assertEqual(int(owner["개인_순자산_차량제외_원"]), total_assets - loan_balance, profile_id)
    test.assertEqual(int(owner["개인_평균월소비합계_원"]), spend, profile_id)
    test.assertEqual(int(owner["개인_대출잔액_원"]), loan_balance, profile_id)
    test.assertEqual(int(owner["개인_평균월대출상환액_원"]), loan_payment, profile_id)
    residual = (
        int(owner["개인_평균월실수령소득_원"])
        - spend
        - loan_payment
        - int(owner["개인_평균월저축액_원"])
    )
    test.assertEqual(int(owner["개인_월잔여액_원"]), residual, profile_id)
    test.assertLess(int(owner["부양인원_명"]), int(owner["가구원수_명"]), profile_id)
    test.assertGreaterEqual(int(owner["가구_평균월실수령소득_원"]), int(owner["개인_평균월실수령소득_원"]))

    included = int(purchase["기본가격_원"]) + int(purchase["옵션가격_원"])
    total = included + int(purchase["등록비_가정_원"])
    funding = int(purchase["본인구매자금_원"]) + int(purchase["가족지원금_가정_원"]) + int(purchase["차량할부원금_원"])
    test.assertEqual(int(purchase["옵션포함가격_원"]), included, profile_id)
    test.assertEqual(registration_fee(included), int(purchase["등록비_가정_원"]), profile_id)
    test.assertEqual(int(purchase["총구매비용_가정_원"]), total, profile_id)
    test.assertEqual(funding, total, profile_id)
    test.assertEqual(int(purchase["구매직후_현금_원"]), cash, profile_id)
    test.assertEqual(int(purchase["구매직전_현금_원"]) - int(purchase["본인구매자금_원"]), cash, profile_id)
    test.assertEqual(purchase["현재_개인연간세전소득_원"], owner["개인_연간세전소득_원"], profile_id)
    test.assertEqual(purchase["구매_모델"], owner["보유차량_모델"], profile_id)
    test.assertLessEqual(int(purchase["기존대출잔액_보정후_원"]), int(purchase["기존대출잔액_보정전_원"]), profile_id)

    principal_part, interest, monthly = monthly_payment(
        int(purchase["차량할부원금_원"]),
        float(purchase["차량할부_연금리_가정"] or 0),
        int(purchase["할부기간_개월"]),
    )
    test.assertEqual(int(purchase["차량_월원금상환액_원"]), principal_part, profile_id)
    test.assertEqual(int(purchase["차량_월이자_원"]), interest, profile_id)
    test.assertEqual(int(purchase["차량_월상환액_원"]), monthly, profile_id)
    test.assertEqual(int(purchase["차량_월원금상환액_원"]) + interest, monthly, profile_id)

    age = int(owner["나이_세"])
    decade = (age // 10) * 10
    test.assertEqual(owner["연령대"], f"{decade}대", profile_id)
    years = int(owner["경력_년"])
    test.assertEqual(owner["경력_구분"], "사회초년생" if years <= 3 else "경력자", profile_id)
    test.assertIn(owner["데이터_구분"], {"학습", "평가", "검증"})
    test.assertEqual(owner["합성데이터_여부"], SYNTHETIC)
    test.assertEqual(owner["라벨_근거"], LABEL_BASIS)
    test.assertEqual(owner["생성규칙_버전"], RULE_VERSION)
    test.assertEqual(owner["난수_시드"], str(seed))


def _assert_summary(test: unittest.TestCase, owners: list[dict[str, str]], summary: list[dict[str, str]]) -> None:
    grouped: dict[str, list[dict[str, str]]] = {}
    for owner in owners:
        grouped.setdefault(owner["보유차량_라벨코드"], []).append(owner)
    test.assertEqual([row["차량_라벨코드"] for row in summary], sorted(grouped))
    for row in summary:
        members = grouped[row["차량_라벨코드"]]
        test.assertEqual(int(row["보유자수"]), len(members))
        age_mean = int(round(sum(int(owner["나이_세"]) for owner in members) / len(members)))
        cash_mean = int(round(sum(int(owner["개인_현금성자산_원"]) for owner in members) / len(members)))
        test.assertEqual(int(row["평균나이_세"]), age_mean)
        test.assertEqual(int(row["평균현금성자산_원"]), cash_mean)
        incomes = sorted(int(owner["개인_연간세전소득_원"]) for owner in members)
        middle = len(incomes) // 2
        if len(incomes) % 2 == 1:
            expected_median = incomes[middle]
        else:
            expected_median = int(round((incomes[middle - 1] + incomes[middle]) / 2))
        test.assertEqual(int(row["연간세전소득_중앙값_원"]), expected_median)
        test.assertLessEqual(int(row["연간세전소득_10백분위_원"]), expected_median)
        test.assertLessEqual(expected_median, int(row["연간세전소득_90백분위_원"]))
        bands = Counter(owner["연령대"] for owner in members)
        top = max(bands.values())
        test.assertEqual(row["최빈연령대"], sorted(band for band, count in bands.items() if count == top)[0])


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))
