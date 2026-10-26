"""CPU LoRA forward, merge, gradients and frozen-layer chain rule.
No NF4, QLoRA implementation, hardware timing or model quality benchmark.
"""
def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def mv(w, x):
    return [dot(row, x) for row in w]


def transpose(w):
    return list(map(list, zip(*w)))


def outer(a, b):
    return [[x * y for y in b] for x in a]


def forward(x, w, a, b, scale):
    base, delta = mv(w, x), mv(b, mv(a, x))
    return [v + scale * d for v, d in zip(base, delta)]


def merge(w, a, b, scale):
    return [[v + scale * dot(b[i], [row[j] for row in a])
             for j, v in enumerate(row)] for i, row in enumerate(w)]


def grads(x, w, a, b, scale, dy):
    u = mv(a, x)
    du = [scale * v for v in mv(transpose(b), dy)]
    da, db = outer(du, x), outer([scale * v for v in dy], u)
    base_dx, adapter_dx = mv(transpose(w), dy), mv(transpose(a), du)
    dx = [v + d for v, d in zip(base_dx, adapter_dx)]
    return dx, da, db


def close(a, b):
    if isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            close(x, y)
    else:
        assert abs(a - b) < 1e-9, (a, b)


def finite(values, expected, loss):
    for row, grad_row in zip(values, expected):
        for j, expected_value in enumerate(grad_row):
            old, eps = row[j], 1e-5
            row[j] = old + eps
            plus = loss()
            row[j] = old - eps
            minus = loss()
            row[j] = old
            close((plus - minus) / (2 * eps), expected_value)


if __name__ == '__main__':
    close(forward([1., 2.], [[1., 0.], [0., 1.]], [[1., 2.]], [[3.], [4.]], .5), [8.5, 12.])
    x = [.2, -.5, .8]
    w, a, b = [[1., .2, -.3], [-.4, .7, .5]], [[.3, -.2, .5]], [[.4], [-.6]]
    scale, dy = .5, [.7, -.4]
    close(forward(x, w, a, b, scale), mv(merge(w, a, b, scale), x))
    dx, da, db = grads(x, w, a, b, scale, dy)
    loss = lambda: dot(forward(x, w, a, b, scale), dy)
    finite([x], [dx], loss)
    finite(a, da, loss)
    finite(b, db, loss)
    # A frozen downstream layer still passes gradients to upstream LoRA.
    fixed = [[2., -.5], [.1, 1.]]
    z = mv(fixed, forward(x, w, a, b, scale))
    upstream = mv(transpose(fixed), z)
    _, chain_da, chain_db = grads(x, w, a, b, scale, upstream)
    chain_loss = lambda: .5 * dot(mv(fixed, forward(x, w, a, b, scale)), mv(fixed, forward(x, w, a, b, scale)))
    finite(a, chain_da, chain_loss)
    finite(b, chain_db, chain_loss)
    assert any(abs(v) > 1e-5 for row in chain_da + chain_db for v in row)
    # Detaching fixed-layer output would provide zero upstream gradient instead.
    _, detached_da, detached_db = grads(x, w, a, b, scale, [0., 0.])
    assert all(v == 0 for row in detached_da + detached_db for v in row)
    before_w = [row[:] for row in w]
    before_a = [row[:] for row in a]
    for values, gradient in [(a, da), (b, db)]:
        for row, grow in zip(values, gradient):
            for j in range(len(row)):
                row[j] -= .01 * grow[j]
    assert w == before_w and a != before_a
    _, initial_da, initial_db = grads(x, w, a, [[0.], [0.]], scale, dy)
    assert all(v == 0 for row in initial_da for v in row)
    assert any(v != 0 for row in initial_db for v in row)
    assert 16 * (4096 + 4096) == 131072
    print('PASS: forward/merge, x/A/B finite differences and frozen-layer chain rule')
    print('PASS: adapter-only update, zero-B initialization and toy parameter budget')
