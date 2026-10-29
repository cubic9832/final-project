import json
import unittest

from tools.data.vehicles.complete_vehicle_specifications import OUTPUT, CATALOG, FIELDS


class CompleteSpecificationsTests(unittest.TestCase):
    def test_no_missing_values_and_original_references_preserved(self):
        read = lambda p:json.loads(p.read_text(encoding='utf-8'))
        original={row['id']:row for row in read(CATALOG)}
        completed=read(OUTPUT/'vehicles.json')
        self.assertEqual(set(original),{row['id'] for row in completed})
        for row in completed:
            specs=row['specifications'];source=original[row['id']]
            self.assertEqual(set(specs),set(FIELDS))
            for spec in specs.values():
                self.assertNotIn(spec['value'],(None,''))
                self.assertTrue(spec['basis'])
                if spec['status']=='estimated':
                    self.assertFalse(spec['source_url'])
            self.assertTrue(2500<=float(specs['length_mm']['value'])<=6000)
            self.assertTrue(1<=float(specs['seats']['value'])<=15)
            self.assertEqual(row['source_identity']['year'],source.get('year'))
            for key,old in [('length_mm','length_mm'),('seats','seats'),('price_won','price'),('efficiency','efficiency')]:
                if source.get(old) is not None:
                    self.assertEqual(specs[key]['value'],source[old])

    def test_neutral_assumptions_and_purpose_estimates_do_not_claim_verification(self):
        traits=json.loads((OUTPUT/'vehicle_traits.json').read_text(encoding='utf-8'))['vehicles']
        for row in traits.values():
            self.assertTrue(all(value is not None for value in row['values'].values()))
            for name in ('ride_comfort','interior_minimalism'):
                self.assertEqual(row['evidence'][name]['kind'],'synthetic-neutral-prior')
            for name in ('seat_capacity','compactness'):
                if row['evidence'][name]['kind']=='estimated-purpose-proxy':
                    self.assertIn('승격하지 않음',row['evidence'][name]['limitation'])


if __name__=='__main__':
    unittest.main()
