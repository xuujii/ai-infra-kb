"""Equal-shape elementwise fusion: semantics and logical bytes, no device test."""
from math import isclose


def separate(x, b):
    assert len(x) == len(b)
    a = [u + v for u, v in zip(x, b)]
    return a, [max(v, 0) for v in a]


def fused(x, b):
    assert len(x) == len(b)
    return [max(u + v, 0) for u, v in zip(x, b)]


def gradient_from_output(y, dy):
    assert len(y) == len(dy)
    return [g if v > 0 else 0 for v, g in zip(y, dy)]


def logical_bytes(n, element_bytes, save_intermediate=False):
    # Materialized logical arrays; not actual cache/HBM traffic.
    return 5*n*element_bytes, (4 if save_intermediate else 3)*n*element_bytes


if __name__ == '__main__':
    x, b, dy = [-3., 1., 2., -1.], [1., 2., -4., 2.], [1., 2., 3., 4.]
    a, y = separate(x, b)
    assert y == fused(x, b) == [0., 3., 0., 1.]
    dx = gradient_from_output(y, dy)
    assert dx == [0., 2., 0., 4.]
    def objective(values):
        return sum(v*g for v, g in zip(separate(values, b)[1], dy))
    eps = 1e-5
    # Independent finite differences away from ReLU's nondifferentiable zero.
    for i, expected in enumerate(dx):
        plus, minus = x.copy(), x.copy()
        plus[i] += eps
        minus[i] -= eps
        numerical = (objective(plus)-objective(minus))/(2*eps)
        assert isclose(numerical, expected, abs_tol=1e-8)
    for n in (1, 1024, 1048576):
        for width in (2, 4):
            split, merged = logical_bytes(n, width)
            assert split-merged == 2*n*width
            assert logical_bytes(n, width, True)[1] == 4*n*width
    print('intermediate:', a, 'output:', y, 'input/bias gradients:', dx)
    print('N=1048576, 2 bytes: split 10 MiB, fused 6 MiB; keep intermediate 8 MiB.')
    print('Output, numerical-gradient and logical-traffic checks passed. Not a hardware test.')
