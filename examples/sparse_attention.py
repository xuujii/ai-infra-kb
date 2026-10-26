"""CPU mask equivalence, gradients, block coverage and sparse weight semantics."""
import math


def visible(i, j, window):
    return max(0, i - window + 1) <= j <= i


def attention(q, k, v, window, sparse=False):
    outputs, rows = [], []
    for i, qi in enumerate(q):
        indices = [j for j in range(len(k)) if visible(i, j, window)]
        if sparse:
            scores = [qi * k[j] for j in indices]
        else:
            # Dense-score + exact same mask reference.
            all_scores = [qi * kj for kj in k]
            scores = [all_scores[j] for j in indices]
        maximum = max(scores)
        exps = [math.exp(s - maximum) for s in scores]
        probs = [e / sum(exps) for e in exps]
        outputs.append(sum(p * v[j] for p, j in zip(probs, indices)))
        rows.append((indices, probs))
    return outputs, rows


def gradients(q, k, v, window):
    out, rows = attention(q, k, v, window, sparse=True)
    dq, dk, dv = [0.] * len(q), [0.] * len(k), [0.] * len(v)
    for i, (indices, prob) in enumerate(rows):
        for j, p in zip(indices, prob):
            ds = out[i] * p * (v[j] - out[i])  # L = half sum(output squared)
            dq[i] += ds * k[j]
            dk[j] += ds * q[i]
            dv[j] += out[i] * p
    return dq, dk, dv


def loss(q, k, v, window):
    return .5 * sum(x * x for x in attention(q, k, v, window)[0])


def coverage(n, window, tile):
    blocks = {(i // tile, j // tile) for i in range(n) for j in range(n)
              if visible(i, j, window)}
    # Exact padded tile coordinate coverage, not hardware instruction count.
    return len(blocks) * tile * tile


if __name__ == '__main__':
    q, k, v = [.2, -.3, .5, 1., -.4], [.1, .6, -.5, .2, .7], [1., -1., 2., .5, 3.]
    for window in [1, 2, 3, 8]:
        reference = attention(q, k, v, window)[0]
        selected = attention(q, k, v, window, sparse=True)[0]
        assert all(abs(a - b) < 1e-12 for a, b in zip(reference, selected))
        analytic = gradients(q, k, v, window)
        for vector, expected in zip([q, k, v], analytic):
            for i in range(len(vector)):
                old, eps = vector[i], 1e-5
                vector[i] = old + eps
                plus = loss(q, k, v, window)
                vector[i] = old - eps
                minus = loss(q, k, v, window)
                vector[i] = old
                assert abs((plus - minus) / (2 * eps) - expected[i]) < 1e-8
    assert sum(visible(i, j, 3) for i in range(8) for j in range(8)) == 21
    assert [coverage(8, 3, t) for t in [1, 2, 4]] == [21, 28, 48]
    assert coverage(8, 8, 2) == 40
    uniform_q, uniform_k, values = [0.] * 8, [1.] * 8, list(range(1, 9))
    full = attention(uniform_q, uniform_k, values, 8)[0][-1]
    local = attention(uniform_q, uniform_k, values, 3)[0][-1]
    assert full == 4.5 and local == 7.
    x, sparse_w = [1, 2, 3, 4], [2, 0, 3, 0]
    packed = [(j, value) for j, value in enumerate(sparse_w) if value != 0]
    assert sum(a * b for a, b in zip(x, sparse_w)) == sum(x[j] * w for j, w in packed) == 11
    assert sum(a * b for a, b in zip(x, [2, .5, 3, 1])) == 16
    print('PASS: dense same-mask and selected attention; Q/K/V finite differences')
    print('PASS: window changes full output 4.5 -> 7; tile coverage 21/28/48')
    print('PASS: packed sparse weights agree with masked weights, not original weights')
