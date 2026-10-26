"""Snapshot, restart and one-buffer checkpoint schedule. No disk/DCP I/O."""
from copy import deepcopy
import random


def initial():
    return dict(theta=[1.0], momentum=[0.0], step=0, cursor=0,
                rng=random.Random(123).getstate())


def train(s, count):
    rng = random.Random()
    rng.setstate(s['rng'])
    for _ in range(count):
        target = (s['cursor'] % 3-1) + rng.uniform(-.1, .1)
        grad = s['theta'][0]-target
        s['momentum'][0] = .9*s['momentum'][0]+grad
        s['theta'][0] -= .05*s['momentum'][0]
        s['step'] += 1
        s['cursor'] += 1
    s['rng'] = rng.getstate()


class CommitStore:
    """Teaching completion contract, not a filesystem durability protocol."""
    def __init__(self):
        self.pending = {}
        self.committed = {}

    def begin(self, version, expected):
        assert version not in self.pending and version not in self.committed
        self.pending[version] = dict(expected=set(expected), shards={})

    def write(self, version, shard, payload):
        entry = self.pending[version]
        assert shard in entry['expected']
        entry['shards'][shard] = deepcopy(payload)

    def commit(self, version):
        entry = self.pending[version]
        if set(entry['shards']) != entry['expected']:
            raise ValueError('Incomplete snapshot cannot be committed')
        self.committed[version] = deepcopy(entry['shards'])
        del self.pending[version]

    def restore_latest(self):
        if not self.committed:
            raise ValueError('No committed checkpoint')
        version = max(self.committed)
        return version, deepcopy(self.committed[version])


def schedule(interval=2, write=12):
    time = write_end = waiting = 0
    events = []
    for step in range(1, 5):
        time += 10
        if step % interval == 0:
            stage_start = max(time, write_end)
            waiting += stage_start-time
            time = stage_start+2
            # This new snapshot only uses the slot after the preceding write.
            assert stage_start >= write_end
            write_end = time+write
            events.append((step, stage_start, time, write_end))
    return dict(training=time, final=max(time, write_end), wait=waiting,
                sync=40+len(events)*(2+write), events=events)


def main():
    uninterrupted = initial()
    train(uninterrupted, 8)
    original = initial()
    train(original, 4)
    snapshot = deepcopy(original)
    shallow = dict(original)
    train(original, 1)
    assert shallow['theta'] == original['theta']  # aliases live parameter storage
    assert snapshot['theta'] != original['theta']
    resumed = deepcopy(snapshot)
    train(resumed, 4)
    assert resumed == uninterrupted
    no_momentum = deepcopy(snapshot)
    no_momentum['momentum'] = [0.0]
    train(no_momentum, 4)
    assert no_momentum['theta'] != uninterrupted['theta']
    no_rng = deepcopy(snapshot)
    no_rng['rng'] = initial()['rng']
    train(no_rng, 4)
    assert no_rng['theta'] != uninterrupted['theta']
    store = CommitStore()
    store.begin(4, ['rank0', 'rank1', 'metadata'])
    for key in ['rank0', 'rank1', 'metadata']:
        store.write(4, key, snapshot)
    store.commit(4)
    store.begin(8, ['rank0', 'rank1', 'metadata'])
    store.write(8, 'rank0', uninterrupted)
    try:
        store.commit(8)
    except ValueError:
        pass
    else:
        raise AssertionError('Accepted incomplete checkpoint')
    version, saved = store.restore_latest()
    assert version == 4 and saved['rank0'] == snapshot
    assert schedule()['training'] == 44 and schedule()['final'] == 56
    assert schedule()['sync'] == 68 and schedule()['wait'] == 0
    slow = schedule(write=40)
    assert [slow[k] for k in ['training', 'final', 'wait', 'sync']] == [64, 104, 20, 124]
    frequent = schedule(interval=1)
    assert [frequent[k] for k in ['training', 'final', 'wait', 'sync']] == [54, 66, 6, 96]
    print('PASS: exact toy restart with optimizer/RNG/cursor; shallow alias, missing momentum and RNG negative cases')
    print('PASS: incomplete shards rejected; preceding committed version stays recoverable')
    print('One buffer, write 12 ms: training 44 ms, final write 56 ms, synchronous 68 ms')
    print('One buffer, write 40 ms: training 64 ms, final write 104 ms, waiting 20 ms; no measured I/O')


if __name__ == '__main__':
    main()
