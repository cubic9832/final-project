import unittest

from tools.data.vehicles.normalize_vehicle_details import parse_prices, parse_kia_efficiency, parse_kia_electric, join_details


class VehicleDetailsTests(unittest.TestCase):
    def test_hybrid_price_uses_discounted_price_and_not_supply_price(self):
        model={'brand':'현대','model':'코나 Hybrid'}
        doc={'url':'https://example.com/price.pdf'}
        pages=[{'page':1,'text':'2027 코나 하이브리드\n세제혜택 전 판매가격 세제혜택 후 판매가격\nModern\n(모던)\n30,380,000\n27,618,182(2,761,818)\n29,380,000\n• 파워트레인 : 가솔린 1.6 하이브리드 엔진\n• 외관 : 17인치 알로이 휠'}]
        rows=parse_prices(model,doc,pages)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['price_won'],29380000)
        self.assertEqual(rows[0]['price_before_tax_benefit_won'],30380000)

    def test_unannounced_tax_benefit_price_stays_missing(self):
        model={'brand':'현대','model':'아반떼 Hybrid'}
        doc={'url':'https://example.com/price.pdf'}
        pages=[{'page':1,'text':'세제혜택 전 판매가격 세제혜택 후 판매가격\nModern\n30,420,000\n27,654,545(2,765,455)\n환경 친화적 자동차 고시 완료 후 안내 예정\n• 파워트레인 : 가솔린 1.6 하이브리드 엔진'}]
        rows=parse_prices(model,doc,pages)
        self.assertIsNone(rows[0]['price_won'])
        self.assertEqual(rows[0]['price_before_tax_benefit_won'],30420000)

    def test_niro_column_order_and_weight_not_used_as_displacement(self):
        model={'brand':'기아','model':'니로'}
        pages=[{'page':4,'text':'정부 신고 연비\n도심 고속도로 복합\n1.6 하이브리드\n16인치 타이어 21.4 18.8 20.2\n1,580 6단 DCT 1\n1,450\n76\n18인치 타이어 20.6 18.1 19.4\n1,470\n80\n※ 위 연비'}]
        rows=parse_kia_efficiency(model,{'url':'https://example.com/price.pdf'},pages)
        self.assertEqual(rows[0]['combined_efficiency'],20.2)
        self.assertEqual(rows[0]['city_efficiency'],21.4)
        self.assertEqual(rows[1]['displacement_cc'],1580)

    def test_electric_efficiency_and_range_are_separate(self):
        pages=[{'page':4,'text':'정부 신고 에너지 소비효율 km/kWh\n스탠다드 2WD\n17인치 350 380 313 5.2 5.6 4.7\n※ 위 에너지'}]
        rows=parse_kia_electric({'model':'EV3'},{'url':'https://example.com/price.pdf'},pages)
        self.assertEqual(rows[0]['range_combined_km'],350)
        self.assertEqual(rows[0]['combined_efficiency'],5.2)
        self.assertEqual(rows[0]['efficiency_unit'],'km/kWh')

    def test_ambiguous_drive_does_not_get_a_guessed_efficiency(self):
        price={'brand':'기아','model':'스포티지','powertrain':'1.6 가솔린 터보','fuel':'GASOLINE','default_wheel_inches':17}
        specs=[{'brand':'기아','model':'스포티지','powertrain':'1.6 가솔린 터보','fuel':'GASOLINE','wheel_inches':'17','configuration':'17인치 '+drive} for drive in ['2WD','4WD']]
        result=join_details([price],specs)[0]
        self.assertNotIn('combined_efficiency',result)
        self.assertIn('복수 사양',result['join_status'])

    def test_special_trim_wheel_overrides_inherited_wheel(self):
        model={'brand':'기아','model':'셀토스'}
        text='1.6 가솔린 터보 (단위 : 원)\n시그니처 3,145만\n• 외장 : 18인치 휠\nX-Line 3,263만\n▶ 시그니처 기본 품목 외\n• 외장 : X-Line 전용 외장 디자인\n• 내장 : 블랙 인테리어\n※ X-Line 전용 외장디자인 적용 부위\n235/45 R19 타이어&블랙 휠'
        rows=parse_prices(model,{'url':'https://example.com/price.pdf'},[{'page':1,'text':text}])
        self.assertEqual(rows[0]['default_wheel_inches'],18)
        self.assertEqual(rows[1]['default_wheel_inches'],19)


if __name__=='__main__':
    unittest.main()
