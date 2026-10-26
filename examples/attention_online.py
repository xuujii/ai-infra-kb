"""Tiny CPU illustration of online Softmax. Not a GPU kernel or benchmark.
Run with Python 3: python attention_online.py
"""
import math


def attention_reference(q, k, v):
    out = []
    for row in q:
        scores = [sum(x * y for x, y in zip(row, key)) / math.sqrt(len(row)) for key in k]
        maximum = max(scores)
        weights = [math.exp(s - maximum) for s in scores]
        denominator = sum(weights)
        out.append([sum(w * value[j] for w, value in zip(weights, v)) / denominator
                    for j in range(len(v[0]))])
    return out


def attention_online(q, k, v, block_size):
    out = []
    for row in q:
        maximum, denominator = -math.inf, 0.0
        numerator = [0.0] * len(v[0])
        for start in range(0, len(k), block_size):
            keys = k[start:start + block_size]
            values = v[start:start + block_size]
            scores = [sum(x * y for x, y in zip(row, key)) / math.sqrt(len(row))
                      for key in keys]
            new_maximum = max(maximum, max(scores))
            correction = math.exp(maximum - new_maximum)
            weights = [math.exp(s - new_maximum) for s in scores]
            denominator = correction * denominator + sum(weights)
            numerator = [correction * numerator[j] + sum(w * value[j]
                         for w, value in zip(weights, values))
                         for j in range(len(numerator))]
            maximum = new_maximum
        out.append([n / denominator for n in numerator])
    return out


if __name__ == "__main__":
    q = [[0.2, -0.5], [1.0, 0.1], [-0.4, 0.8]]
    k = [[0.1, 0.7], [0.9, -0.2], [-0.3, 0.6], [0.4, 0.4], [-0.8, 0.3]]
    v = [[1.0, 2.0], [-1.0, 0.5], [0.3, -0.7], [2.1, 0.4], [0.8, 1.2]]
    reference = attention_reference(q, k, v)
    for block_size in [1, 2, 3, 5]:
        actual = attention_online(q, k, v, block_size)
        error = max(abs(x - y) for a, b in zip(reference, actual) for x, y in zip(a, b))
        assert error < 1e-12, (block_size, error)
        print(f"block_size={block_size}, max_absolute_error={error:.3e}")
    print("reference output:", reference)
    toy_q = [[1.0]]
    toy_k = [[math.log(w)] for w in [1, 2, 4, 3]]
    toy_v = [[float(v)] for v in [10, 20, 30, 40]]
    toy_result = attention_online(toy_q, toy_k, toy_v, block_size=2)[0][0]
    assert abs(toy_result - 29.0) < 1e-12
    assert abs(toy_result - attention_reference(toy_q, toy_k, toy_v)[0][0]) < 1e-12
    print("article worked example: output =", toy_result)
    print("Online normalization only; no mask, dropout or backward.")
