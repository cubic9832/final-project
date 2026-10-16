import csv
import unittest

from datagen.formulas import (
    age_band,
    career_band,
    monthly_payment,
    monthly_takehome,
    registration_fee,
    split_funding,
)
from datagen.layout import SEGMENTS, seed_directory


class FormulaTest(unittest.TestCase):
    def test_installment_matches_seed_purchases(self):
        for segment in SEGMENTS:
            path = seed_directory(segment) / "purchases.csv"
            with path.open(encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    principal = int(row["차량할부원금_원"])
                    rate = float(row["차량할부_연금리_가정"] or 0)
                    months = int(row["할부기간_개월"])
                    _principal_part, interest, monthly = monthly_payment(principal, rate, months)
                    # 시드 이자는 잔액 * 연이율 / 12 의 반올림과 같다.
                    # 시드 월상환은 원리금균등 반올림과 최대 1원 차이 난다.
                    self.assertEqual(interest, int(row["차량_월이자_원"]), row["프로필_식별자"])
                    self.assertLessEqual(abs(monthly - int(row["차량_월상환액_원"])), 1, row["프로필_식별자"])
                    self.assertEqual(
                        int(row["차량_월원금상환액_원"]) + int(row["차량_월이자_원"]),
                        int(row["차량_월상환액_원"]),
                        row["프로필_식별자"],
                    )
                    included = int(row["옵션포함가격_원"])
                    self.assertEqual(registration_fee(included), int(row["등록비_가정_원"]), row["프로필_식별자"])

    def test_payment_boundaries(self):
        self.assertEqual(monthly_payment(0, 0.065, 60), (0, 0, 0))
        self.assertEqual(monthly_payment(1_000_000, 0.065, 0), (0, 0, 0))
        self.assertEqual(monthly_payment(100, 0, 3), (33, 0, 33))

    def test_funding_sum_stays_exact_when_shares_overflow(self):
        self_fund, family, loan = split_funding(100, 0.8, 0.5)
        self.assertEqual((self_fund, family, loan), (0, 20, 80))
        self.assertEqual(self_fund + family + loan, 100)
        self.assertEqual(split_funding(0, 0.5, 0.5), (0, 0, 0))

    def test_age_and_career_bands(self):
        self.assertEqual(age_band(29), "20대")
        self.assertEqual(age_band(30), "30대")
        self.assertEqual(career_band(3), "사회초년생")
        self.assertEqual(career_band(4), "경력자")

    def test_takehome_rounds_to_thousands(self):
        self.assertEqual(monthly_takehome(79_617_000), 5_440_000)

