"""A separately versioned model; old 68-input checkpoints remain intact."""
import json
from pathlib import Path
import numpy as np
import torch
from vehicle_matching.finance import Assumptions, Profile, assess
from vehicle_matching.preference_model import preference_network
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.ui_scenario_features import FEATURE_NAMES, encode_ui_scenario
from tools.data.households.generate_scenario_population import file_hash, write_json


class UiScenarioRanker:
    schema = 'ui-scenario-ranker-v1'

    def __init__(self, net, stats, traits):
        self.net, self.traits = net.eval(), traits
        self.mean, self.scale, self.minimum, self.maximum = [np.asarray(value,dtype=np.float32) for value in stats]
        self.assumptions = Assumptions()
        if any(value.shape != (len(FEATURE_NAMES),) or not np.isfinite(value).all() for value in stats) or np.any(self.scale<=0):
            raise ValueError('Invalid UI scenario normalization')

    def score_features(self, values):
        x = np.asarray(values,dtype=np.float32).reshape(-1,len(FEATURE_NAMES))
        if not np.isfinite(x).all(): raise ValueError('Invalid UI scenario features')
        if not len(x): return []
        with torch.no_grad():
            return self.net(torch.from_numpy((x-self.mean)/self.scale)).flatten().tolist()

    def score_candidates(self, user, vehicles):
        profile = Profile(**user['profile'])
        rows = []
        for vehicle in vehicles:
            cost = assess(profile,vehicle)
            if not cost['eligible'] or seating_status(profile,vehicle) != 'match':
                raise ValueError('Candidate fails financial/seating requirements')
            rows.append(encode_ui_scenario(user,vehicle,self.traits[vehicle.id],cost))
        return self.score_features(rows)

    def save(self, output, provenance, catalog_path, traits_path):
        output = Path(output); output.mkdir(parents=True,exist_ok=False)
        torch.save(self.net.state_dict(),output/'model.pt')
        for source,name in [(catalog_path,'catalog.json'),(traits_path,'vehicle_traits.json')]:
            (output/name).write_bytes(Path(source).read_bytes())
        write_json(output/'metadata.json',{'schema':self.schema,'features':FEATURE_NAMES,'architecture':[len(FEATURE_NAMES),64,32,1],
            **{key:value.tolist() for key,value in zip(('mean','scale','minimum','maximum'),(self.mean,self.scale,self.minimum,self.maximum))},
            'files_sha256':{name:file_hash(output/name) for name in ('model.pt','catalog.json','vehicle_traits.json')},'training':provenance})

    @classmethod
    def load(cls, directory):
        path = Path(directory); meta = json.loads((path/'metadata.json').read_text(encoding='utf-8'))
        if meta['schema'] != cls.schema or meta['features'] != list(FEATURE_NAMES): raise ValueError('UI model contract mismatch')
        for name,digest in meta['files_sha256'].items():
            if file_hash(path/name) != digest: raise ValueError(f'UI model checksum mismatch: {name}')
        net = preference_network(len(FEATURE_NAMES));net.load_state_dict(torch.load(path/'model.pt',map_location='cpu',weights_only=True))
        return cls(net,[np.asarray(meta[key],dtype=np.float32) for key in ('mean','scale','minimum','maximum')],
                   json.loads((path/'vehicle_traits.json').read_text(encoding='utf-8'))['vehicles'])
