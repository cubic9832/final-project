"""Versioned 68-input scenario ranker, isolated from existing serving checkpoints."""
from pathlib import Path
import json

import numpy as np
import torch

from vehicle_matching.finance import Assumptions, Profile, assess
from vehicle_matching.preference_model import preference_network
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.scenario_features import CHANNELS, FEATURE_NAMES, encode_scenario
from tools.data.households.generate_scenario_population import file_hash, write_json


class ScenarioRanker:
    schema = 'scenario-ranker-v1'

    def __init__(self, net, mean, scale, minimum, maximum):
        self.net = net.eval()
        self.mean, self.scale, self.minimum, self.maximum = [np.asarray(v,dtype=np.float32) for v in (mean,scale,minimum,maximum)]
        for values in (self.mean,self.scale,self.minimum,self.maximum):
            if values.shape != (len(FEATURE_NAMES),) or not np.isfinite(values).all():
                raise ValueError('Invalid scenario normalization statistics')
        if np.any(self.scale<=0) or np.any(self.minimum>self.maximum):
            raise ValueError('Invalid scenario normalization range')

    def score_features(self, values):
        x = np.asarray(values,dtype=np.float32)
        if x.ndim!=2 or x.shape[1]!=len(FEATURE_NAMES) or not np.isfinite(x).all():
            raise ValueError('Expected finite 68-column scenario features')
        if not len(x):
            return []
        with torch.no_grad():
            return self.net(torch.from_numpy((x-self.mean)/self.scale)).flatten().tolist()

    def score_candidates(self, user, vehicles):
        profile = Profile(**user['profile'])
        weights = np.asarray(user['channel_weights'],dtype=np.float32)
        if weights.shape!=(len(CHANNELS),) or not np.isfinite(weights).all() or np.any(weights<0) or weights.sum()<=0:
            raise ValueError('Invalid user channel weights')
        if any(not isinstance(v,(int,float)) or not np.isfinite(v) or not 0<=v<=1 for v in user['model_affinities'].values()):
            raise ValueError('Invalid model affinities')
        rows = []
        for vehicle in vehicles:
            cost = assess(profile,vehicle)
            if not cost['eligible'] or seating_status(profile,vehicle)!='match':
                raise ValueError(f'Candidate fails financial/seating requirements: {vehicle.id}')
            rows.append(encode_scenario(user,profile,vehicle,cost))
        return self.score_features(np.asarray(rows,dtype=np.float32).reshape(-1,len(FEATURE_NAMES)))

    def save(self, directory, provenance, catalog_path):
        directory = Path(directory)
        directory.mkdir(parents=True,exist_ok=False)
        torch.save(self.net.state_dict(),directory/'model.pt')
        (directory/'catalog.json').write_bytes(Path(catalog_path).read_bytes())
        write_json(directory/'metadata.json',{'schema':self.schema,'features':list(FEATURE_NAMES),
                   'architecture':[len(FEATURE_NAMES),64,32,1],
                   'mean':self.mean.tolist(),'scale':self.scale.tolist(),'minimum':self.minimum.tolist(),
                   'maximum':self.maximum.tolist(),'weights_sha256':file_hash(directory/'model.pt'),
                   'catalog_sha256':file_hash(directory/'catalog.json'),'assumptions':Assumptions().to_dict(),
                   'training':provenance})

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        metadata = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
        if metadata['schema']!=cls.schema or metadata['features']!=list(FEATURE_NAMES) or metadata['architecture']!=[len(FEATURE_NAMES),64,32,1]:
            raise ValueError('Scenario model contract mismatch')
        for filename,key in [('model.pt','weights_sha256'),('catalog.json','catalog_sha256')]:
            if file_hash(directory/filename)!=metadata[key]:
                raise ValueError(f'Scenario model checksum mismatch: {filename}')
        net = preference_network(len(FEATURE_NAMES))
        net.load_state_dict(torch.load(directory/'model.pt',map_location='cpu',weights_only=True))
        return cls(net,*(metadata[k] for k in ('mean','scale','minimum','maximum')))
