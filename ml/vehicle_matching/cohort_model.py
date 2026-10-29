"""Learn per-axis policy matches from controlled cohorts; compose explicit weights."""
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from vehicle_matching.finance import Assumptions
from vehicle_matching.lifestyle_model import digest

SCHEMA = 'controlled-cohort-ranker-v1'
AXES = ('body_type','exterior_sportiness','exterior_angularity','acceleration_performance','compactness','seat_capacity')
# Legacy inference feature indices -> trained axis. Purpose uses the same numeric
# match function as compactness; its exact raw proxy is documented by the service.
CHANNELS = {0:1,1:2,4:3,5:5,6:4,7:4,8:0}


def network():
    return nn.Sequential(nn.Linear(7,24),nn.ReLU(),nn.Linear(24,1))


def inputs(axis, matches):
    values = np.zeros((len(matches),7),dtype=np.float32)
    values[:,axis] = 1
    values[:,-1] = matches
    return values


class CohortRanker:
    schema = SCHEMA
    supported_features = tuple(CHANNELS) + (9,10)

    def __init__(self, net):
        self.net = net.eval()
        self.assumptions = Assumptions()
        self.mean = np.zeros(7,dtype=np.float32)

    def scores(self, features, weights, masks):
        features,weights,masks = [np.asarray(value,dtype=np.float32) for value in (features,weights,masks)]
        if features.ndim != 2 or features.shape[1] != 13 or features.shape != weights.shape or features.shape != masks.shape:
            raise ValueError('Cohort inference shape mismatch')
        if any(not np.isfinite(value).all() for value in (features,weights,masks)) or np.any(weights<0) or not np.isin(masks,(0,1)).all():
            raise ValueError('Invalid cohort inference values')
        result,total = np.zeros(len(features)),np.zeros(len(features))
        with torch.inference_mode():
            for channel in self.supported_features:
                w = weights[:,channel]*masks[:,channel]
                if not w.any():
                    continue
                # Fuel/size are explicit supplementary match rules, not new learned labels.
                match = features[:,channel] if channel in (9,10) else self.net(torch.from_numpy(inputs(CHANNELS[channel],features[:,channel]))).flatten().numpy()
                result += np.clip(match,0,1)*w
                total += w
        return result/np.maximum(total,1e-12)

    def pair_logits(self,a,b,weights,masks):
        return self.scores(a,weights,masks)-self.scores(b,weights,masks)

    @classmethod
    def load(cls,directory):
        torch.set_num_threads(2)
        directory = Path(directory)
        metadata = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
        if metadata['schema'] != SCHEMA or metadata['axes'] != list(AXES) or digest(directory/'model.pt') != metadata['weights_sha256']:
            raise ValueError('Cohort model schema/checksum mismatch')
        net = network()
        net.load_state_dict(torch.load(directory/'model.pt',map_location='cpu',weights_only=True))
        return cls(net)
