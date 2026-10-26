import csv
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from vehicle_matching.catalog import ROOT
from vehicle_matching.refine_population import collect, legacy_profile, build, verify_saved
from test_vehicle_matching import person, vehicle


class RefinePopulationTests(unittest.TestCase):
    def legacy_row(self, **changes):
        row={'프로필_식별자':'old','데이터_구분':'평가','월소득보정액_원':'0',
             '개인_평균월실수령소득_원':'6000000','개인_현금성자산_원':'90000000',
             '구매투입가능자금_원':'60000000','개인_평균월주거비_원':'1000000',
             '개인_평균월기타생활소비_원':'500000','기존월상환액_보정전_원':'200000',
             '선호연료':'하이브리드','선호크기':'상관없음','최소탑승인원_명':'0',
             '가성비중요도_1부터5':'3','공간중요도_1부터5':'3',
             '연료중요도_1부터5':'3','탑승인원중요도_1부터5':'3',
             '구매가격상한_원_0이면미지정':'0','선택차량번호':'irrelevant'}
        return {**row, **changes}

    def test_preserves_spendable_cash_and_does_not_read_old_vehicle_label(self):
        row=self.legacy_row();p=legacy_profile(row)
        self.assertEqual(p.liquid_assets,60000000)
        self.assertEqual(p.monthly_expenses,1500000)
        self.assertEqual(p,legacy_profile({**row,'선택차량번호':'another'}))
        with self.assertRaises(ValueError):legacy_profile({**row,'구매투입가능자금_원':'90000001'})

    def test_duplicate_test_group_cannot_leak_into_training(self):
        p=legacy_profile(self.legacy_row())
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
            root=Path(folder)
            (root/'new').write_text(json.dumps({'id':0,'split':'train','profile':asdict(p)})+'\n',encoding='utf-8')
            for filename,rows,fields in [('old',[self.legacy_row(),self.legacy_row(프로필_식별자='repair',월소득보정액_원='100')],None),
                                        ('coverage',[],['프로필_식별자']),('provenance',[],['프로필_식별자','생성유형'])]:
                with (root/filename).open('w',encoding='utf-8',newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=fields or list(rows[0]));writer.writeheader();writer.writerows(rows)
            records,counts,rejected=collect(root/'new',root/'old',root/'coverage',root/'provenance')
            self.assertEqual(len(records),1)
            self.assertEqual(records[0]['split'],'test')
            self.assertEqual(counts['stricter_split_reassignments'],1)
            self.assertEqual(sum(rejected.values()),2)

    def test_comparisons_and_no_choice_cases_are_separated(self):
        cars=[vehicle(id=str(i),model=str(i),price=20000000+i*3000000) for i in range(3)]
        records=[]
        for i,(split,cash) in enumerate([('train',60000000),('validation',70000000),('test',80000000),('test',1)]):
            p=person(liquid_assets=cash,down_payment=0,emergency_reserve=0,monthly_savings=0,months=0,annual_rate=0,financing_mode='recommendation')
            records.append({'id':i,'split':split,'profile':asdict(p),'origin':'test','original_id':str(i)})
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
            output=Path(folder)/'data'
            arrays,retained,report=build(output,records,cars,set(),42)
            self.assertEqual(len(retained),3)
            self.assertEqual(report['counts']['financial'],1)
            self.assertTrue(verify_saved(output,cars,report)['passed'])


if __name__=='__main__':unittest.main()
