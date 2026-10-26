"""CPU ring RS+AG simulation and ideal costs; no device benchmark."""
from copy import deepcopy
from math import log2


def ring_allreduce(inputs):
    p, size = len(inputs), len(inputs[0])
    assert p > 1 and size % p == 0 and all(len(x) == size for x in inputs)
    width = size // p
    buffers = [[row[c * width:(c + 1) * width] for c in range(p)] for row in inputs]
    sent = [0] * p
    expected = [sum(row[i] for row in inputs) for i in range(size)]
    for step in range(p - 1):
        messages = [(r, (r + 1) % p, (r - step) % p,
                     deepcopy(buffers[r][(r - step) % p])) for r in range(p)]
        for src, dst, c, values in messages:
            buffers[dst][c] = [a + b for a, b in zip(buffers[dst][c], values)]
            sent[src] += width
    for r in range(p):
        c = (r + 1) % p
        assert buffers[r][c] == expected[c * width:(c + 1) * width]
    for step in range(p - 1):
        messages = [(r, (r + 1) % p, (r + 1 - step) % p,
                     deepcopy(buffers[r][(r + 1 - step) % p])) for r in range(p)]
        for src, dst, c, values in messages:
            buffers[dst][c] = values
            sent[src] += width
    outputs = [[x for chunk in row for x in chunk] for row in buffers]
    assert all(row == expected for row in outputs)
    assert all(n == 2 * (p - 1) * width for n in sent)
    return outputs, sent


def teaching_cost(p, size, alpha_us=5, bandwidth_gib=25):
    assert p > 1 and log2(p).is_integer()
    alpha, payload = alpha_us / 1000, size / (bandwidth_gib * 2 ** 30) * 1000
    return (2 * (p - 1) * alpha + 2 * (p - 1) / p * payload,
            2 * log2(p) * (alpha + payload))


if __name__ == '__main__':
    result, sent = ring_allreduce([[10 ** r * (i + 1) for i in range(4)] for r in range(4)])
    assert result[0] == [1111, 2222, 3333, 4444]
    for p in (2, 3, 4, 8):
        ring_allreduce([[(r - 2) * 100 + i for i in range(p * 3)] for r in range(p)])
    small, large = teaching_cost(8, 4096), teaching_cost(8, 64 * 2 ** 20)
    assert small[1] < small[0] and large[0] < large[1] and abs(large[0] - 4.445) < 1e-12
    print('PASS: 2/3/4/8 rank ring equals direct sum; per-rank send count correct')
    print('4-rank output:', result[0], 'sent elements:', sent)
    print('Ideal small/large costs (ms), not NCCL Tree estimates:', small, large)
