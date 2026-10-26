"""Cache identity, parameter references and warmup restoration; CPU toy only."""
from dataclasses import dataclass, replace
from copy import deepcopy
import random


@dataclass(frozen=True)
class CacheKey:
    graph: str
    bucket: str
    dtype: str
    stride: str
    compiler: str
    device: str
    options: tuple
    embedded_weight_version: str | None = None


def initial():
    return dict(theta=[1.0], momentum=[0.0], step=0, cursor=0,
                rng=random.Random(321).getstate())


def train_step(s):
    rng = random.Random()
    rng.setstate(s['rng'])
    target = (s['cursor'] % 3-1)+rng.uniform(-.1, .1)
    s['momentum'][0] = .9*s['momentum'][0]+s['theta'][0]-target
    s['theta'][0] -= .05*s['momentum'][0]
    s['step'] += 1
    s['cursor'] += 1
    s['rng'] = rng.getstate()


def readiness(hit=True, warmed=3, bucket=2):
    assert warmed in [0, 1, 3] and bucket in range(3)
    # Compiled artifacts already cover all three buckets in this scenario.
    return dict(ready=6+(.5 if hit else 8)+.2*warmed,
                first=.05 if bucket < warmed else .45, steady=.05)


def main():
    key = CacheKey('decoder-v1', 'short', 'bf16', 'contiguous', 'compiler-v1', 'device-A', ('fast',))
    cache = {key: 'compatible-plan'}
    assert replace(key) in cache
    for field, value in [('graph', 'decoder-v2'), ('bucket', 'long'), ('dtype', 'fp32'),
                         ('stride', 'transposed'), ('compiler', 'compiler-v2'),
                         ('device', 'device-B'), ('options', ('precise',))]:
        assert replace(key, **{field: value}) not in cache
    embedded = replace(key, embedded_weight_version='weights-v1')
    assert replace(embedded, embedded_weight_version='weights-v2') != embedded
    # Dynamic weight values are not automatically part of a plan's cache key.
    assert key.embedded_weight_version is None
    model = {'parameter': [0.0]}
    optimizer_reference = model['parameter']
    model['parameter'] = [2.0]  # teaching assignment replaces the parameter object
    optimizer_reference[0] -= .1
    assert model['parameter'] == [2.0] and optimizer_reference == [-.1]
    rebound = model['parameter']
    rebound[0] -= .1
    assert model['parameter'] == [1.9]
    baseline = initial()
    train_step(baseline)
    warmed = initial()
    saved = deepcopy(warmed)
    train_step(warmed)
    train_step(warmed)
    warmed = deepcopy(saved)
    train_step(warmed)
    assert warmed == baseline
    weights_only = initial()
    train_step(weights_only)
    weights_only['theta'] = deepcopy(saved['theta'])
    train_step(weights_only)
    assert weights_only['theta'] != baseline['theta']
    assert weights_only['step'] != baseline['step']
    assert readiness() == dict(ready=7.1, first=.05, steady=.05)
    assert readiness(False)['ready'] == 14.6
    assert readiness(warmed=1)['first'] == .45
    assert readiness(warmed=1, bucket=0)['first'] == .05
    assert readiness(warmed=0, bucket=0)['ready'] == 6.5
    print('PASS: cache guards/version/device/dtype, weight specialization identity')
    print('PASS: optimizer references must match installed parameters')
    print('PASS: full warmup-state restoration matches no warmup; weights-only does not')
    print('Toy startup: warm hit 7.1 s, warm miss 14.6 s; unprepared bucket first request .45 s')
    print('No actual file load, compiler, graph capture or device timing')


if __name__ == '__main__':
    main()
