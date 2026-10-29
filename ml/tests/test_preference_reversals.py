import unittest

from experiments.audit_preference_reversals import classify_reversal, decompose


class PreferenceReversalTests(unittest.TestCase):
    def test_seat_preference_loss_is_separated_from_cost_and_ml_advantages(self):
        def score(cost,seats,ml):
            components=[{'key':key,'score':value,'weight':weight,'contribution':value*weight/7}
                        for key,value,weight in [('cost',cost,3),('seating',seats,3),('model',ml,1)]]
            return {'components':components,'total':sum(c['contribution'] for c in components)}
        first=score(50,100,50);second=score(77,71,99)
        deltas,losses=decompose(first,second)
        self.assertEqual(losses[0]['condition'],'seating')
        self.assertTrue(losses[0]['lost_full_match'])
        self.assertLess(deltas['cost']+deltas['seating'],0)
        self.assertGreater(sum(deltas.values()),0)
        self.assertEqual(classify_reversal(deltas,losses),'선호하락_비용평가이점있음_ML로역전')

    def test_ml_only_gain_does_not_get_described_as_economic_tradeoff(self):
        deltas={'cost':-1,'fuel':0,'space':0,'seating':-2,'model':4}
        self.assertEqual(classify_reversal(deltas,[{'condition':'seating'}]),'명시평가항목상열세_ML로역전')


if __name__=='__main__':unittest.main()
