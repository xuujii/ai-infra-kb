"""Non-preemptive queue and bounded resource lifecycle; no serving engine."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    name: str
    duration: int
    arrival: int = 0
    priority: int = 5


def schedule(jobs, policy='fcfs'):
    assert policy in ['fcfs', 'priority']
    remaining = list(enumerate(jobs))
    clock, result = 0, []
    while remaining:
        ready = [(i, j) for i, j in remaining if j.arrival <= clock]
        if not ready:
            clock = min(j.arrival for _, j in remaining)
            continue
        key = (lambda item: (item[1].priority, item[1].arrival, item[0])) if policy == 'priority' else (lambda item: (item[1].arrival, item[0]))
        i, j = min(ready, key=key)
        assert j.duration > 0
        start, finish = clock, clock+j.duration
        result.append(dict(name=j.name, start=start, finish=finish, wait=start-j.arrival))
        clock = finish
        remaining.remove((i, j))
    return result


class KVPool:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}

    @property
    def used(self):
        return sum(e['blocks'] for e in self.entries.values())

    def admit(self, name, generation, blocks):
        key = (name, generation)
        assert key not in self.entries and blocks > 0
        if self.used+blocks > self.capacity:
            return False
        self.entries[key] = dict(blocks=blocks, readers=0, cancelled=False, output=[])
        return True

    def start_reader(self, key):
        assert not self.entries[key]['cancelled']
        self.entries[key]['readers'] += 1

    def cancel(self, key):
        self.entries[key]['cancelled'] = True
        self.try_release(key)

    def try_release(self, key):
        e = self.entries[key]
        if not e['cancelled'] or e['readers']:
            return False
        del self.entries[key]
        return True

    def finish_reader(self, key):
        e = self.entries[key]
        assert e['readers'] > 0
        e['readers'] -= 1
        if e['cancelled']:
            self.try_release(key)

    def deliver(self, key, token):
        e = self.entries.get(key)
        if e is None or e['cancelled']:
            return False
        e['output'].append(token)
        return True


def round_budget(limit, decode_count, pending_prefill):
    assert 0 <= decode_count <= limit
    chunk = min(limit-decode_count, pending_prefill)
    return decode_count, chunk


def main():
    jobs = [Job('A', 8), Job('B', 2, priority=0), Job('C', 2, priority=0)]
    fcfs, priority = schedule(jobs), schedule(jobs, 'priority')
    assert [r['name'] for r in fcfs] == ['A', 'B', 'C']
    assert [r['wait'] for r in fcfs] == [0, 8, 10]
    assert [r['name'] for r in priority] == ['B', 'C', 'A']
    assert [r['wait'] for r in priority] == [0, 2, 4]
    assert fcfs[-1]['finish'] == priority[-1]['finish'] == 12
    delayed = schedule([Job('A', 8), Job('B', 2, arrival=1, priority=0)], 'priority')
    assert delayed[1]['start'] == 8  # no priority preemption of already-running A
    pool = KVPool(16)
    assert pool.admit('A', 0, 6) and pool.admit('B', 0, 5)
    assert pool.used == 11 and not pool.admit('C', 0, 7)
    pool.start_reader(('B', 0))
    pool.cancel(('B', 0))
    assert pool.used == 11 and not pool.try_release(('B', 0))
    assert not pool.deliver(('B', 0), 'late')
    assert not pool.admit('C', 0, 7)
    pool.finish_reader(('B', 0))
    assert pool.used == 6 and pool.admit('C', 0, 7)
    assert pool.used == 13
    assert pool.admit('B', 1, 2)
    assert not pool.deliver(('B', 0), 'old-generation')
    assert pool.entries[('B', 1)]['output'] == []
    assert pool.deliver(('B', 1), 'new')
    assert round_budget(8, 2, 20) == (2, 6)
    assert sum(round_budget(8, 2, 3)) == 5
    queue, queue_limit = [], 2
    for name in ['X', 'Y', 'Z']:
        if len(queue) < queue_limit:
            queue.append(name)
    assert queue == ['X', 'Y']
    print('PASS: FCFS/priority wait and work conservation; no preemption of running work')
    print('PASS: bounded KV admission, cancellation, reader completion and old-generation rejection')
    print('PASS: query-token budget and bounded pending queue; not real HTTP or vLLM')


if __name__ == '__main__':
    main()
