"""CPU-only liveness/address checks and strided view example; no benchmarks."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Buffer:
    name: str
    size: int
    start: int
    end: int


def overlaps(a0, a1, b0, b1):
    return max(a0, b0) < min(a1, b1)


def validate(objects, offsets, capacities):
    for obj in objects:
        assert offsets[obj.name] >= 0
        assert capacities[obj.name] >= obj.size
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            live = overlaps(a.start, a.end, b.start, b.end)
            address = overlaps(offsets[a.name], offsets[a.name] + a.size,
                               offsets[b.name], offsets[b.name] + b.size)
            assert not (live and address), (a.name, b.name)


def plan(objects):
    # Whole fixed slots: simple first-fit, not an optimal general allocator.
    slots, assigned, capacities = [], {}, {}
    for obj in sorted(objects, key=lambda o: (o.start, o.name)):
        chosen = next((slot for slot in slots
                       if slot['size'] >= obj.size and slot['end'] <= obj.start), None)
        if chosen is None:
            chosen = {'offset': sum(s['size'] for s in slots),
                      'size': obj.size, 'end': obj.end}
            slots.append(chosen)
        chosen['end'] = obj.end
        assigned[obj.name] = chosen['offset']
        capacities[obj.name] = chosen['size']
    validate(objects, assigned, capacities)
    return assigned, capacities, sum(s['size'] for s in slots)


class View:
    def __init__(self, storage, shape, stride):
        self.storage, self.shape, self.stride = storage, shape, stride

    def address(self, i, j):
        assert 0 <= i < self.shape[0] and 0 <= j < self.shape[1]
        return i * self.stride[0] + j * self.stride[1]

    def read(self, i, j):
        return self.storage[self.address(i, j)]

    def write(self, i, j, value):
        self.storage[self.address(i, j)] = value

    def rows(self):
        return [[self.read(i, j) for j in range(self.shape[1])]
                for i in range(self.shape[0])]


def main():
    objects = [Buffer('A', 4, 0, 3), Buffer('B', 6, 1, 4), Buffer('C', 4, 3, 5)]
    offsets, capacities, total = plan(objects)
    assert total == 10 and offsets['A'] == offsets['C']
    delayed = [Buffer('A', 4, 0, 5), *objects[1:]]
    try:
        validate(delayed, offsets, capacities)
    except AssertionError:
        print('PASS: pending A reader makes old reuse plan invalid')
    else:
        raise AssertionError('Live buffers share an address')
    assert plan(delayed)[2] == 14
    # Check every discrete phase independently of the planner's slot choice.
    for time in range(5):
        active = [o for o in objects if o.start <= time < o.end]
        assert sum(o.size for o in active) <= total
    storage = list(range(6))
    base = View(storage, (2, 3), (3, 1))
    transposed = View(storage, (3, 2), (1, 3))
    assert transposed.rows() == [[0, 3], [1, 4], [2, 5]]
    copied = View([item for row in transposed.rows() for item in row], (3, 2), (2, 1))
    transposed.write(1, 0, 99)
    assert base.read(0, 1) == 99 and copied.read(1, 0) == 1
    print('PASS: fixed-slot reserve 14 -> 10 MiB; delayed reader requires 14 MiB')
    print('PASS: transposed view aliases original; contiguous copy is independent')


if __name__ == '__main__':
    main()
