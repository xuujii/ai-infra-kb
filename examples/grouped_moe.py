"""CPU grouped expert MLP, restore and fixed-gate linear gradient checks."""
from math import ceil

ROUTES = [[(0,.7),(1,.3)],[(1,.6),(2,.4)],[(0,.5),(1,.5)],[(0,.2),(1,.8)]]


def linear(x, weight):
    return [sum(x[k] * weight[k][j] for k in range(len(x))) for j in range(len(weight[0]))]


def expert(e, x):
    up = [[.1 * (e + 1), .3, .5], [.2, -.4, .2 * (e + 1)]]
    down = [[.4, .2], [-.3, .5], [.7, -.6]]
    bias = [.1 * (e + 1), -.2, .05]
    hidden = [max(0, z + b) for z, b in zip(linear(x, up), bias)]
    return linear(hidden, down)


def pack():
    jobs, offsets = [], [0]
    for e in range(4):
        for token, route in enumerate(ROUTES):
            for logical, gate in route:
                if logical == e:
                    jobs.append((token, e, gate))
        offsets.append(len(jobs))
    return jobs, offsets


def grouped(xs, wrong_index=False):
    jobs, offsets = pack()
    output = [[0.0, 0.0] for _ in xs]
    for e in range(4):
        for token, logical, gate in jobs[offsets[e]:offsets[e + 1]]:
            assert logical == e
            result = expert(e, xs[token])
            dest = (token + 1) % len(xs) if wrong_index else token
            for d in range(2):
                output[dest][d] += gate * result[d]
    return output


def direct(xs):
    return [[sum(g * expert(e, x)[d] for e, g in route) for d in range(2)]
            for x, route in zip(xs, ROUTES)]


def linear_loss(xs, weights):
    ys = [[sum(g * linear(x, weights[e])[d] for e, g in route) for d in range(2)]
          for x, route in zip(xs, ROUTES)]
    return sum(y * y / 2 for row in ys for y in row), ys


if __name__ == '__main__':
    xs = [[.3,-.2],[-.4,.8],[.6,.1],[-.2,-.5]]
    assert pack()[1] == [0,3,7,8,8]
    expected, actual = direct(xs), grouped(xs)
    assert max(abs(a - b) for r, s in zip(expected, actual) for a, b in zip(r, s)) < 1e-12
    assert max(abs(a - b) for r, s in zip(expected, grouped(xs, True)) for a, b in zip(r, s)) > 1e-3
    weights = [[[.2 * (e + 1), .1], [-.3, .4]] for e in range(4)]
    _, dy = linear_loss(xs, weights)
    dx = [[0.0, 0.0] for _ in xs]
    jobs, _ = pack()
    for token, e, gate in jobs:
        for k in range(2):
            dx[token][k] += gate * sum(dy[token][d] * weights[e][k][d] for d in range(2))
    for token, row in enumerate(xs):
        for k, old in enumerate(row):
            row[k] = old + 1e-6
            plus = linear_loss(xs, weights)[0]
            row[k] = old - 1e-6
            minus = linear_loss(xs, weights)[0]
            row[k] = old
            assert abs((plus - minus) / 2e-6 - dx[token][k]) < 1e-9
    for tile, grouped_rows in [(1,8),(2,10),(4,12)]:
        assert sum(ceil(n / tile) * tile for n in [3,4,1,0]) == grouped_rows
    print('PASS: grouped ReLU MLP equals per-token reference; wrong restore differs')
    print('PASS: fixed-gate linear expert input gradients match finite differences')
    print('Counts [3,4,1,0], offsets [0,3,7,8,8]; tile coverage rows 8/10/12')
