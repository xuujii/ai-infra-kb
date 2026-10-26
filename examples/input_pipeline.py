"""Independent CPU preparation, transfer and compute queues, pure Python.

One resource per stage, constant times, enough buffers, no runtime overhead.
Also demonstrates readiness and conservative reusable-slot state checks.
"""


def schedule(n, prepare, transfer, compute):
    assert n > 0 and prepare > 0 and transfer >= 0 and compute > 0
    ends = [0,0,0]
    batches = []
    for _ in range(n):
        times, dependency = [], 0
        for stage, duration in enumerate((prepare,transfer,compute)):
            start = max(ends[stage],dependency)
            ends[stage] = start+duration
            dependency = ends[stage]
            times.append((start,dependency))
        batches.append(times)
    return batches


class ReusableSlot:
    # A combined host/device slot conservatively remains held through compute.
    def __init__(self):
        self.state = 'free'

    def transition(self, expected, next_state):
        if self.state != expected:
            raise RuntimeError(f'Expected {expected}; still {self.state}')
        self.state = next_state

    def fill(self): self.transition('free','host-ready')
    def copy(self): self.transition('host-ready','copying')
    def copy_done(self): self.transition('copying','device-ready')
    def consume(self): self.transition('device-ready','computing')
    def compute_done(self): self.transition('computing','free')


class PendingResult:
    def __init__(self, ready_at): self.ready_at = ready_at
    def read(self, clock):
        if clock < self.ready_at:
            raise RuntimeError('Result transfer is not complete')
        return 'ready-result'


def rejects(action):
    try:
        action()
    except RuntimeError:
        return
    raise AssertionError('Unsafe transition was accepted')


if __name__ == '__main__':
    for n in (1,3,4,8):
        for prepare in (1,3,8):
            for transfer in (0,1,4):
                for compute in (2,6,12):
                    batches = schedule(n,prepare,transfer,compute)
                    assert batches[-1][-1][1] == prepare+transfer+compute+(n-1)*max(prepare,transfer,compute)
                    for i,times in enumerate(batches):
                        for stage,(start,end) in enumerate(times):
                            if stage: assert start >= times[stage-1][1]
                            if i: assert start >= batches[i-1][stage][1]
                            assert end-start == (prepare,transfer,compute)[stage]
    assert schedule(4,3,1,6)[-1][-1][1] == 28
    assert schedule(3,2,0,6)[-1][-1][1] == 20
    assert schedule(3,8,0,6)[-1][-1][1] == 30
    slot = ReusableSlot()
    slot.fill(); slot.copy()
    rejects(slot.fill); rejects(slot.consume)
    slot.copy_done(); slot.consume()
    rejects(slot.fill)
    slot.compute_done(); slot.fill()
    result = PendingResult(9)
    rejects(lambda: result.read(8))
    assert result.read(9) == 'ready-result'
    print('4 batches (3,1,6 ms): serial 40 ms, pipelined 28 ms')
    print('3 batches (2,0,6 ms): serial 24 ms, pipelined 20 ms')
    print('Readiness, slot reuse and dependencies passed for 108 configurations. Not a hardware benchmark.')
