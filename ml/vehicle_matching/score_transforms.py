"""Experimental score mappings; no automatic change to serving behavior."""
import numpy as np
import torch


def transform_scores(logits, method, center=0.0, temperature=1.0):
    values = np.asarray(logits, dtype=np.float64)
    if not np.isfinite(values).all() or not np.isfinite(temperature) or temperature <= 0:
        raise ValueError('Finite scores and positive temperature required')
    if not len(values):
        return values
    if method == 'legacy_sigmoid':
        return torch.from_numpy(values.astype(np.float32)).sigmoid().numpy().astype(np.float64)
    if method == 'neutral':
        return np.full(len(values), .5)
    if method == 'minmax':
        width = np.ptp(values)
        return (values-values.min())/width if width > 0 else np.full(len(values), .5)
    if method == 'calibrated_sigmoid':
        if not np.isfinite(center):
            raise ValueError('Finite center required')
        return torch.from_numpy((values-center)/temperature).sigmoid().numpy()
    if method == 'softmax':
        shifted = (values-values.max())/temperature
        exponentials = np.exp(shifted)
        return exponentials/exponentials.sum()
    raise ValueError(f'Unknown transform: {method}')


def fit_sigmoid(logits, targets, weights):
    """Fit positive slope/center to soft rule labels on calibration cases only.

    Equal total weight per profile prevents cases with many trims dominating.
    The result is a rule-score calibration, not a purchase probability.
    """
    z = torch.as_tensor(np.asarray(logits), dtype=torch.float64)
    y = torch.as_tensor(np.asarray(targets), dtype=torch.float64)
    w = torch.as_tensor(np.asarray(weights), dtype=torch.float64)
    if not len(z) or not torch.isfinite(z).all() or not torch.isfinite(y).all() or not torch.isfinite(w).all():
        raise ValueError('Finite nonempty calibration data required')
    if not torch.all((y >= 0) & (y <= 1)) or not torch.all(w > 0):
        raise ValueError('Invalid calibration targets or weights')
    location = float(z.mean())
    scale = max(1.0, float(z.std()))
    normalized = (z-location)/scale
    log_slope = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    intercept = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.LBFGS([log_slope, intercept], max_iter=100, line_search_fn='strong_wolfe')

    def closure():
        optimizer.zero_grad()
        predicted = normalized*log_slope.exp()+intercept
        loss = ((torch.nn.functional.softplus(predicted)-y*predicted)*w).sum()/w.sum()
        loss.backward()
        return loss

    optimizer.step(closure)
    slope = float(log_slope.detach().exp())
    temperature = scale/slope
    center = location-float(intercept.detach())*temperature
    if not np.isfinite(center) or not np.isfinite(temperature) or temperature <= 0:
        raise ValueError('Calibration did not converge')
    return {'center':center, 'temperature':temperature,
            'method':'positive-slope logistic soft-label fit; equal profile weights',
            'target':'current rule utility excluding ML; not actual purchase probability'}
