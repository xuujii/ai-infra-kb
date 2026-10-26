"""Stable CPU Split-KV merge; no device parallel execution/timing."""
from math import exp, log, sqrt, inf


def partial(scores, values):
    visible = [(s, v) for s, v in zip(scores, values) if s is not None]
    if not visible:
        return -inf, 0.0, [0.0] * len(values[0]) if values else []
    maximum = max(s for s, _ in visible)
    weights = [exp(s - maximum) for s, _ in visible]
    return maximum, sum(weights), [sum(w * v[d] for w, (_, v) in zip(weights, visible))
                                  for d in range(len(visible[0][1]))]


def merge(states):
    valid = [state for state in states if state[1] > 0]
    if not valid:
        raise ValueError('All-masked row has no softmax distribution in this example')
    maximum = max(m for m, _, _ in valid)
    scales = [exp(m - maximum) for m, _, _ in valid]
    denominator = sum(s * l for s, (_, l, _) in zip(scales, valid))
    return [sum(s * u[d] for s, (_, _, u) in zip(scales, valid)) / denominator
            for d in range(len(valid[0][2]))]


def split(scores, values, parts):
    states = []
    for i in range(parts):
        start, end = i * len(scores) // parts, (i + 1) * len(scores) // parts
        states.append(partial(scores[start:end], values[start:end]))
    return merge(states)


def reference(scores, values):
    # Direct complete softmax, independent of partial-state merge.
    visible = [i for i, s in enumerate(scores) if s is not None]
    maximum = max(scores[i] for i in visible)
    weights = [exp(scores[i] - maximum) for i in visible]
    return [sum(w * values[i][d] for w, i in zip(weights, visible)) / sum(weights)
            for d in range(len(values[0]))]


if __name__ == '__main__':
    scores, values = [log(x) for x in (1, 2, 3, 4)], [[1], [2], [4], [8]]
    assert abs(split(scores, values, 2)[0] - 4.9) < 1e-12
    a, b = partial(scores[:2], values[:2]), partial(scores[2:], values[2:])
    wrong = (a[2][0] / a[1] + b[2][0] / b[1]) / 2
    assert abs(wrong - 4.9) > .9
    print('Worked example: correct 4.9, wrong local average', wrong)
    keys = [[.1,.7],[.9,-.2],[-.3,.6],[.4,.4],[-.8,.3]]
    values = [[1,2],[-1,.5],[.3,-.7],[2.1,.4],[.8,1.2]]
    for query in [[.2,-.5],[1,.1],[-.4,.8]]:
        base_scores = [sum(q * k for q, k in zip(query, key)) / sqrt(2) for key in keys]
        for offset in (0, 1000, -1000):
            for mask in ([True] * 5, [False, False, True, True, False]):
                scores = [s + offset if visible else None for s, visible in zip(base_scores, mask)]
                expected = reference(scores, values)
                for parts in (1, 2, 3, 8):
                    result = split(scores, values, parts)
                    assert max(abs(a - b) for a, b in zip(result, expected)) < 1e-12
    print('PASS: vectors, non-even splits, empty/masked splits and large score offsets')
