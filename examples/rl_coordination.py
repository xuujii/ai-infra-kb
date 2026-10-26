"""RL outer-stage dependencies, version-safe publication and trajectory metadata."""
from math import exp, log, isclose
from copy import deepcopy


def pipeline(batches=3, rollout=40, scoring=20, training=30):
    ready = [0, 0, 0]
    result = []
    for batch in range(batches):
        previous = 0
        record = []
        for stage, duration in enumerate([rollout, scoring, training]):
            start = max(ready[stage], previous)
            finish = start+duration
            record.append((start, finish))
            ready[stage] = previous = finish
        result.append(record)
    for i, record in enumerate(result):
        for stage, (a, b) in enumerate(record):
            assert b > a
            if stage:
                assert a >= record[stage-1][1]
            if i:
                assert a >= result[i-1][stage][1]
    return result


class WeightPublisher:
    """In-place teaching engine: must finish old readers before switching."""
    def __init__(self):
        self.version = 0
        self.weights = {'part0':[1.0], 'part1':[2.0]}
        self.readers = 0
        self.staging = None

    def begin_reader(self, kv_version):
        if kv_version != self.version:
            raise ValueError('KV belongs to a different policy version')
        self.readers += 1
        return self.version

    def end_reader(self):
        assert self.readers > 0
        self.readers -= 1

    def stage(self, version, pieces, completed):
        assert version > self.version
        self.staging = dict(version=version, pieces=deepcopy(pieces), completed=completed)

    def publish(self):
        s = self.staging
        if self.readers:
            raise ValueError('Cannot overwrite a version with active readers')
        if s is None or not s['completed'] or set(s['pieces']) != {'part0', 'part1'}:
            raise ValueError('All weight pieces and device operations must be complete')
        self.version, self.weights = s['version'], deepcopy(s['pieces'])
        self.staging = None


def group_admissible(trajectories, expected, current_version, max_lag):
    if len(trajectories) != expected or not trajectories:
        return False
    group = trajectories[0]['group']
    for t in trajectories:
        if t['group'] != group or not t['complete'] or not t['versions']:
            return False
        if len(t['versions']) != len(t['behavior_logprobs']):
            return False
        if any(v > current_version or current_version-v > max_lag for v in t['versions']):
            return False
    return True  # teaching engineering gate, not proof of algorithmic correctness


def rejected(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Unsafe operation was accepted')


def main():
    records = pipeline()
    assert records == [[(0, 40), (40, 60), (60, 90)],
                       [(40, 80), (80, 100), (100, 130)],
                       [(80, 120), (120, 140), (140, 170)]]
    assert 3*(40+20+30) == 270 and records[-1][-1][1] == 170
    assert pipeline(5)[-1][-1][1] == 250
    engine = WeightPublisher()
    engine.stage(1, {'part0':[3.0]}, completed=True)
    rejected(engine.publish)
    assert engine.version == 0
    pieces = {'part0':[3.0], 'part1':[4.0]}
    engine.stage(1, pieces, completed=False)
    rejected(engine.publish)
    engine.begin_reader(0)
    engine.stage(1, pieces, completed=True)
    rejected(engine.publish)
    engine.end_reader()
    engine.publish()
    assert engine.version == 1 and engine.weights == pieces
    pieces['part0'][0] = 100
    assert engine.weights['part0'] == [3.0]
    rejected(lambda: engine.begin_reader(0))
    engine.begin_reader(1)
    engine.end_reader()
    behavior_logprob, current_logprob = log(.2), log(.4)
    assert isclose(exp(current_logprob-behavior_logprob), 2)
    assert exp(current_logprob-current_logprob) == 1  # incorrect replacement
    t = dict(group='P', versions=[0, 1], behavior_logprobs=[log(.2), log(.3)], complete=True)
    group = [deepcopy(t), deepcopy(t)]
    assert group_admissible(group, 2, 1, 1)
    assert not group_admissible(group, 2, 2, 1)
    assert not group_admissible(group, 2, 1, 0)
    assert not group_admissible(group[:1], 2, 1, 1)
    broken = deepcopy(group)
    broken[1]['group'] = 'Q'
    assert not group_admissible(broken, 2, 1, 1)
    broken = deepcopy(group)
    broken[1]['complete'] = False
    assert not group_admissible(broken, 2, 1, 1)
    broken = deepcopy(group)
    broken[0]['behavior_logprobs'].pop()
    assert not group_admissible(broken, 2, 1, 1)
    print('PASS: all R/P/T stage and resource dependencies; serial 270 ms, pipeline 170 ms')
    print('PASS: incomplete weights, pending device work, old readers and stale KV rejected')
    print('PASS: behavior probability ratio and complete-group/version-lag metadata')
    print('Fixed-behavior scheduling toy; no PPO/GRPO optimizer, hardware transfer or quality claim')


if __name__ == '__main__':
    main()
