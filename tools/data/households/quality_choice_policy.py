"""Preference-first candidate pools with explicit affordability headroom."""
import hashlib
import random

import numpy as np

from tools.data.households.relabel_preference_choices import ChoicePolicy, FEATURES, PREFERENCES, FUEL_LABELS


class QualityPolicy(ChoicePolicy):
    def __init__(self, vehicles):
        super().__init__(vehicles)
        # Unknown data is neutral in scoring, and separately pending specification review.
        for size in self.size_scores:
            self.size_scores[size] = np.where(self.length > 0, self.size_scores[size], .5)
        self.preference_fuel = np.array(['HYBRID' if v.original_fuel == 'PHEV' else v.fuel for v in self.vehicles])

    def pool(self, row, context):
        original_score, payment, running, remaining, upfront = super().evaluate(row, context)
        income = int(row[FEATURES[0]])
        monthly = payment + running
        headroom = np.maximum(np.maximum(100000, np.ceil(income * .05)), np.ceil(monthly * .1)).astype(int)
        raw_eligible = np.isfinite(original_score) & (remaining-context['buffer'] >= headroom+2)
        size = {'작음':'small', '중간':'medium', '큼':'large'}[row[PREFERENCES[1]]]
        from vehicle_matching.preferences import SIZE_BANDS
        low, high = SIZE_BANDS[size]
        gap = np.maximum(np.maximum(low-self.length,self.length-high),0)
        # An unverified specification is pending, not evidence that the vehicle is unsuitable.
        known = self.length > 0
        eligible = raw_eligible & known & (gap <= 500)
        size_match = known & (gap == 0)
        wanted = next((key for key,value in FUEL_LABELS.items() if value == row[PREFERENCES[2]]),None)
        fuel_match = (self.preference_fuel == wanted) if wanted else np.ones(len(self.vehicles),dtype=bool)
        levels = size_match.astype(int) + fuel_match.astype(int)
        if not np.any(eligible):
            return None, '여유자금또는정원가격제원조건부족'
        tier = int(np.max(levels[eligible]))
        if tier < 1:
            return None, '크기연료둘다불일치'
        tier_mask = eligible & (levels == tier)
        available_models = int(np.count_nonzero(np.maximum.reduceat(eligible,self.starts)))
        if available_models < 3:
            return None, '적격모델3개미만'
        available = income-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']
        principal = self.price-upfront
        factor = (.06/12)/(1-(1+.06/12)**-60)
        total = self.price+running*60+principal*(factor*60-1)
        budget = max(1,available*60+int(row[FEATURES[1]])-context['reserve'])
        economy = np.clip(1-total/budget,0,1)
        target = {'출퇴근':4100,'가족이동':4750,'여가':4900,'업무':4600}[row[FEATURES[7]]]
        purpose = np.where(known,np.maximum(0,1-np.abs(self.length-target)/1500),.5)
        weight = int(row[PREFERENCES[0]])
        score = (weight*economy+.25*purpose+.25*self.size_scores[size]+.25*fuel_match)/(weight+.75)
        score = np.where(tier_mask,score,-np.inf)
        model_scores = np.maximum.reduceat(score,self.starts)
        best = float(np.max(model_scores))
        shortlist = np.flatnonzero(model_scores >= best-.12)
        if len(shortlist) < 2:
            return None, '선호우선비교모델2개미만'
        return {'scores':score,'model_scores':model_scores,'shortlist':shortlist,'best':best,
                'payment':payment,'running':running,'remaining':remaining,'upfront':upfront,
                'headroom':headroom,'eligible_models':available_models,'tier':tier,
                'fuel_available':bool(np.any(eligible & fuel_match)),
                'size_available':bool(np.any(eligible & size_match)),
                'unknown_pending':int(np.count_nonzero(raw_eligible & ~known))}, '통과'

    def select(self, row, context, pool, seed):
        rng = random.Random(hashlib.sha256(f'{seed}:{row["프로필_식별자"]}'.encode()).hexdigest())
        choices = pool['shortlist']
        weights = np.exp((pool['model_scores'][choices]-pool['best'])/.06)
        model = rng.choices(choices.tolist(),weights=weights.tolist())[0]
        start,end = self.starts[model],self.ends[model]
        index = int(start+np.argmax(pool['scores'][start:end]))
        vehicle = self.vehicles[index]
        return {'vehicle':vehicle,'score':float(pool['scores'][index]),'best':pool['best'],
                'payment':int(pool['payment'][index]),'running':int(pool['running'][index]),
                'remaining':int(pool['remaining'][index]),'upfront':round(float(pool['upfront'][index])),
                'eligible_models':pool['eligible_models'],'fuel_available':pool['fuel_available'],'size_available':pool['size_available'],
                'both_available':pool['tier']==2,'tier':pool['tier'],
                'comparison_models':len(choices),'required_headroom':int(pool['headroom'][index]),
                'semantic_fuel':FUEL_LABELS[self.preference_fuel[index]]}
