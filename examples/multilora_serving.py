"""CPU mixed-LoRA routing, merged weights and adapter read lifetimes."""
def mv(w, x):
    return [sum(a * b for a, b in zip(row, x)) for row in w]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def delta(x, adapter):
    down, up, scale = adapter
    return [scale * v for v in mv(up, mv(down, x))]


def merged(w, adapter):
    down, up, scale = adapter
    return [[v + scale * sum(up[i][r] * down[r][j] for r in range(len(down)))
             for j, v in enumerate(row)] for i, row in enumerate(w)]


def close(a, b):
    for x, y in zip(a, b):
        if isinstance(x, list):
            close(x, y)
        else:
            assert abs(x - y) < 1e-12, (x, y)


class AdapterSlot:
    """One ready immutable version; cannot evict while an async reader holds it."""
    def __init__(self, version):
        self.version, self.readers, self.ready = version, 0, False

    def acquire(self, version):
        if not self.ready or version != self.version:
            raise ValueError('Wrong version or load not complete')
        self.readers += 1

    def release(self):
        if self.readers <= 0:
            raise ValueError('No active reader')
        self.readers -= 1

    def evict(self):
        if self.readers:
            raise ValueError('Cannot overwrite active device readers')
        self.ready = False


if __name__ == '__main__':
    w = [[float(i == j) for j in range(4)] for i in range(4)]
    adapters = {
        'A': ([[1., 0., 0., 0.]], [[1.], [2.], [0.], [-1.]], .5),
        'B': ([[0., 1., 0., 0.], [0., 0., 1., 0.]], [[0., 1.], [1., 0.], [-1., 2.], [0., 1.]], .25)
    }
    inputs = [[1., 2., 3., 4.], [2., -1., 1., .5], [.5, 1., -1., 2.], [2., 0., .5, 1.]]
    identities = ['A', 'B', 'A', None]
    direct = [add(mv(w, x), delta(x, adapters[name])) if name else mv(w, x)
              for x, name in zip(inputs, identities)]
    grouped = [mv(w, x) for x in inputs]
    indices = {name: [i for i, identity in enumerate(identities) if identity == name] for name in adapters}
    assert indices == {'A': [0, 2], 'B': [1]}
    for name, rows in indices.items():
        for original_row in rows:
            grouped[original_row] = add(grouped[original_row], delta(inputs[original_row], adapters[name]))
    by_merge = [mv(merged(w, adapters[name]), x) if name else mv(w, x)
                for x, name in zip(inputs, identities)]
    close(direct, grouped)
    close(direct, by_merge)
    wrong = add(mv(w, inputs[1]), delta(inputs[1], adapters['A']))
    assert any(abs(a - b) > .1 for a, b in zip(wrong, direct[1]))
    # A simplified next-layer key derived from the adapter-modified hidden output.
    key_projection = [[1., .3, -.5, .2]]
    key_a = mv(key_projection, add(mv(w, inputs[0]), delta(inputs[0], adapters['A'])))
    key_b = mv(key_projection, add(mv(w, inputs[0]), delta(inputs[0], adapters['B'])))
    assert key_a != key_b, 'Same input prefix alone does not establish KV compatibility'
    slot = AdapterSlot('A:v1')
    try:
        slot.acquire('A:v1')
        raise AssertionError('Unready adapter used')
    except ValueError:
        pass
    slot.ready = True
    slot.acquire('A:v1')
    try:
        slot.evict()
        raise AssertionError('Live reader overwritten')
    except ValueError:
        pass
    try:
        slot.acquire('A:v2')
        raise AssertionError('Version mismatch accepted')
    except ValueError:
        pass
    slot.release()
    slot.evict()
    assert not slot.ready
    effective = 2 * (2 * 1 + 1 * 2) * (4 + 4)
    padded = 2 * 4 * 2 * (4 + 4)
    assert (effective, padded) == (64, 128)
    print('PASS: per-request, grouped restoration and per-adapter merged outputs')
    print('PASS: wrong adapter/KV counterexamples and ready/version/reader checks')
    print('Toy valid branch FLOP:', effective, 'versus uniform allocation:', padded)
