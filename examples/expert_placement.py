"""CPU logical expert/gate/restore checks; no device communication benchmark."""
from math import tanh


def expert(logical, x):
    return tanh((logical + 1) * x + logical * 0.1)


def reference(values, routes):
    return [sum(g * expert(e, x) for e, g in route) for x, route in zip(values, routes)]


def placed(values, routes, mapping):
    counters, jobs = {e: 0 for e in mapping}, []
    for t, (x, route) in enumerate(zip(values, routes)):
        for e, g in route:
            ranks = mapping[e]
            rank = ranks[counters[e] % len(ranks)]
            counters[e] += 1
            jobs.append((rank, t, e, g, x))
    jobs.sort(key=lambda j: (j[0], j[2], j[1]))
    outputs, seen = [0.0] * len(values), set()
    for rank, t, e, g, x in jobs:
        assert rank in mapping[e] and (t, e) not in seen
        seen.add((t, e))
        outputs[t] += g * expert(e, x)
    assert len(seen) == sum(len(route) for route in routes)
    return outputs


if __name__ == '__main__':
    values = [-0.9, -0.2, 0.1, 0.6, 1.0, 1.3]
    routes = [[(0, .7), (1, .3)], [(0, .6), (2, .4)], [(0, .8), (3, .2)],
              [(1, .4), (2, .6)], [(0, .9), (3, .1)], [(0, .5), (2, .5)]]
    expected = reference(values, routes)
    for layout in ({0: [0], 1: [0], 2: [1], 3: [1]},
                   {0: [0], 1: [1], 2: [0], 3: [1]},
                   {0: [0, 1], 1: [0], 2: [1], 3: [1]}):
        assert max(abs(a - b) for a, b in zip(placed(values, routes, layout), expected)) < 1e-12
    wrong_gates = [[(e, 1 / len(route)) for e, _ in route] for route in routes]
    missing = [[route[0]] for route in routes]
    assert max(abs(a - b) for a, b in zip(reference(values, wrong_gates), expected)) > 1e-3
    assert max(abs(a - b) for a, b in zip(reference(values, missing), expected)) > 1e-3
    original, moved, replicated = [100, 20], [90, 30], [60, 60]
    assert sum(original) == sum(moved) == sum(replicated) == 120
    print('PASS: moved/replicated experts preserve weighted top-2 outputs')
    print('PASS: wrong gate and missing contribution fail comparison')
    print('Teaching top-1 loads: 100/20 -> 90/30 -> 60/60; total 120 unchanged')
