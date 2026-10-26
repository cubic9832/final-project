"""Vectorized financial eligibility with weighted soft preferences, no shortlist cutoff."""
import numpy as np

from tools.data.households.quality_choice_policy import QualityPolicy
from tools.data.households.relabel_preference_choices import FEATURES, PREFERENCES, FUEL_LABELS

WEIGHTS=('공간중요도_1부터5','연료중요도_1부터5','탑승인원중요도_1부터5','용도중요도_1부터5')


class FinancialChoicePolicy(QualityPolicy):
    def pool(self,row,context):
        _,payment,running,remaining,upfront=super().evaluate(row,context)
        eligible=remaining>=context['buffer']
        if context['ceiling']: eligible &= self.price<=context['ceiling']
        if context['funds']<0 or context['reserve']<0 or context['funds']+context['reserve']>int(row[FEATURES[1]]):
            return None,'구매투입자금부족'
        if not np.any(eligible): return None,'월자금부족'
        income=int(row[FEATURES[0]])
        available=income-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']
        factor=(.06/12)/(1-(1+.06/12)**-60)
        total=self.price+running*60+(self.price-upfront)*(factor*60-1)
        budget=max(1,available*60+int(row[FEATURES[1]])-context['reserve'])
        economy=np.clip(1-total/budget,0,1)
        size={'작음':'small','중간':'medium','큼':'large'}[row[PREFERENCES[1]]]
        fuel=next((key for key,value in FUEL_LABELS.items() if value==row[PREFERENCES[2]]),None)
        fuel_score=(self.preference_fuel==fuel) if fuel else np.full(len(self.vehicles),.5)
        seats=int(row[PREFERENCES[3]])
        seat_score=np.where(self.capacity>0,np.minimum(1,self.capacity/max(1,seats)),.5) if seats else np.ones(len(self.vehicles))
        target={'출퇴근':4100,'가족이동':4750,'여가':4900,'업무':4600}[row[FEATURES[7]]]
        purpose=np.where(self.length>0,np.maximum(0,1-np.abs(self.length-target)/1500),.5)
        cost_weight=int(row[PREFERENCES[0]])
        sw,fw,nw,pw=(int(row.get(k,default)) for k,default in zip(WEIGHTS,(3,3,3,1)))
        # Neutral ML component matches integrated_score(..., ml_score=.5).
        numerator=cost_weight*economy+sw*self.size_scores[size]+pw*purpose+.5
        denominator=cost_weight+sw+pw+1
        if fuel:
            numerator+=fw*fuel_score; denominator+=fw
        if seats:
            numerator+=nw*seat_score; denominator+=nw
        scores=np.where(eligible,numerator/denominator,-np.inf)
        model_scores=np.maximum.reduceat(scores,self.starts)
        choices=np.flatnonzero(np.isfinite(model_scores))
        return {'scores':scores,'model_scores':model_scores,'shortlist':choices,'best':float(np.max(model_scores)),
                'payment':payment,'running':running,'remaining':remaining,'upfront':upfront,
                'headroom':np.zeros(len(self.vehicles),dtype=int),'eligible_models':len(choices),'tier':0,
                'fuel_available':bool(np.any(eligible & fuel_score.astype(bool))),
                'both_available':bool(np.any(eligible & (self.size_scores[size]==1) & (fuel_score==1))),
                'size_available':bool(np.any(eligible & (self.size_scores[size]==1)))},'재무통과'

    def select(self,row,context,pool,seed):
        result=super().select(row,context,pool,seed)
        result['both_available']=pool['both_available']
        return result

    def top_three(self,pool):
        ordered=sorted(pool['shortlist'],key=lambda m:(-pool['model_scores'][m],self.vehicles[self.starts[m]].id))
        return [int(self.starts[m]+np.argmax(pool['scores'][self.starts[m]:self.ends[m]])) for m in ordered[:3]]
