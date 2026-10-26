"""Standard-library CE and gradients; no GPU memory or performance benchmark.
Class-index targets, unweighted mean, no smoothing; -100 means ignored.
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def zeros(rows, cols):
    return [[0.] * cols for _ in range(rows)]


def dense(h, w, b, targets):
    z = [[dot(row, weight) + bias for weight, bias in zip(w, b)] for row in h]
    valid = sum(t != -100 for t in targets)
    if not valid:
        raise ValueError('Define all-ignored loss handling before training')
    dh, dw, db, total = zeros(len(h), len(h[0])), zeros(len(w), len(w[0])), [0.] * len(w), 0.
    for i, target in enumerate(targets):
        if target == -100:
            continue
        m = max(z[i])
        exps = [math.exp(value - m) for value in z[i]]
        ell = sum(exps)
        total += m + math.log(ell) - z[i][target]
        for j in range(len(w)):
            grad = (exps[j] / ell - (j == target)) / valid
            db[j] += grad
            for d in range(len(h[0])):
                dh[i][d] += grad * w[j][d]
                dw[j][d] += grad * h[i][d]
    return total / valid, dh, dw, db


def chunked(h, w, b, targets, row_chunk, vocab_chunk):
    valid = sum(t != -100 for t in targets)
    if not valid:
        raise ValueError('Define all-ignored loss handling before training')
    dh, dw, db = zeros(len(h), len(h[0])), zeros(len(w), len(w[0])), [0.] * len(w)
    total = 0.
    for start in range(0, len(h), row_chunk):
        states = {}
        indices = [i for i in range(start, min(start + row_chunk, len(h))) if targets[i] != -100]
        for i in indices:
            m, ell, target_logit = -math.inf, 0., None
            for vs in range(0, len(w), vocab_chunk):
                end = min(vs + vocab_chunk, len(w))
                z_tile = [dot(h[i], w[j]) + b[j] for j in range(vs, end)]
                new_m = max(m, max(z_tile))
                # First tile initializes from a finite max; no -inf minus -inf.
                ell = (ell * math.exp(m - new_m) if ell else 0.) + sum(math.exp(z - new_m) for z in z_tile)
                m = new_m
                if vs <= targets[i] < end:
                    target_logit = z_tile[targets[i] - vs]
            lse = m + math.log(ell)
            total += lse - target_logit
            states[i] = lse
        # Recompute this row chunk's vocabulary blocks for backward; no full Z/dZ.
        for vs in range(0, len(w), vocab_chunk):
            for i in indices:
                for j in range(vs, min(vs + vocab_chunk, len(w))):
                    z = dot(h[i], w[j]) + b[j]
                    grad = (math.exp(z - states[i]) - (j == targets[i])) / valid
                    db[j] += grad
                    for d in range(len(h[0])):
                        dh[i][d] += grad * w[j][d]
                        dw[j][d] += grad * h[i][d]
    return total / valid, dh, dw, db


def close(a, b, tol=1e-11):
    if isinstance(a, list) or isinstance(a, tuple):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            close(x, y, tol)
    else:
        assert abs(a - b) < tol, (a, b)


if __name__ == '__main__':
    h = [[.2, -.1], [.5, 1.], [-.3, .7], [.8, -.2]]
    w = [[1., .2], [-.5, .3], [.4, -.6], [.8, .9], [-.2, .7]]
    b, targets = [.1, -.2, .3, .1, -.1], [2, -100, 0, 4]
    reference = dense(h, w, b, targets)
    for rows in [1, 2, 3, 8]:
        for vocab in [1, 2, 4, 8]:
            close(reference, chunked(h, w, b, targets, rows, vocab))
    # Independent finite differences for hidden inputs, weights and bias.
    for values, grads in [(h, reference[1]), (w, reference[2]), ([b], [reference[3]])]:
        for row, grow in zip(values, grads):
            for d, grad in enumerate(grow):
                old, eps = row[d], 1e-5
                row[d] = old + eps
                plus = dense(h, w, b, targets)[0]
                row[d] = old - eps
                minus = dense(h, w, b, targets)[0]
                row[d] = old
                assert abs((plus - minus) / (2 * eps) - grad) < 2e-8
    close(dense(h, w, [x + 1000 for x in b], targets), chunked(h, w, [x + 1000 for x in b], targets, 3, 2), 1e-10)
    true_loss, wrong_loss = math.log(10 / 3), math.log(7 / 3)
    assert abs(true_loss - wrong_loss) > .3
    # Row chunks contain 1 versus 2 valid targets: unweighted mean of chunk means is wrong.
    first = dense(h[:2], w, b, targets[:2])[0]
    second = dense(h[2:], w, b, targets[2:])[0]
    close((first + 2 * second) / 3, reference[0])
    assert abs((first + second) / 2 - reference[0]) > 1e-4
    try:
        chunked(h, w, b, [-100] * 4, 2, 2)
        raise AssertionError('All ignored rows must not silently divide by zero')
    except ValueError:
        pass
    print('PASS: all chunk sizes, ignored rows, non-even boundaries and large logit offsets')
    print('PASS: hidden/weight/bias finite differences and weighted loss normalization')
    print('Vocabulary denominator:', true_loss, '!= target-block-only:', wrong_loss)
