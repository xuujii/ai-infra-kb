"""CPU semantics: shared KV and a simplified MLA with a position branch.
Not a model conversion, GPU kernel, quality test or speed benchmark.
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def mv(matrix, vector):
    return [dot(row, vector) for row in matrix]


def transpose(matrix):
    return list(map(list, zip(*matrix)))


def softmax(scores):
    maximum = max(scores)
    values = [math.exp(s - maximum) for s in scores]
    return [v / sum(values) for v in values]


def weighted(prob, vectors):
    return [sum(p * v[d] for p, v in zip(prob, vectors))
            for d in range(len(vectors[0]))]


def close(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        if isinstance(x, list):
            close(x, y)
        else:
            assert abs(x - y) < 1e-12, (x, y)


def rotate(x, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [c * x[0] - s * x[1], s * x[0] + c * x[1]]


def check_shared_kv():
    queries = [[1., 0.], [0., 1.], [1., 2.], [-1., 1.]]
    for kv_heads in [1, 2, 4]:
        keys = [[[1 + g, 0.], [0., 1 + g], [.5, -.5]]
                for g in range(kv_heads)]
        values = [[[1., g], [2., 1 + g], [-1., 2 + g]]
                  for g in range(kv_heads)]
        group = 4 // kv_heads
        expanded_k = [[row[:] for row in keys[h // group]] for h in range(4)]
        expanded_v = [[row[:] for row in values[h // group]] for h in range(4)]
        direct, expanded = [], []
        for h, q in enumerate(queries):
            prob = softmax([dot(q, k) / math.sqrt(2)
                            for k in keys[h // group]])
            direct.append(weighted(prob, values[h // group]))
            other_prob = softmax([dot(q, k) / math.sqrt(2)
                                  for k in expanded_k[h]])
            expanded.append(weighted(other_prob, expanded_v[h]))
        close(direct, expanded)
        if kv_heads < 4:
            assert direct[0] != direct[1], 'Shared KV need not imply equal output'
    print('PASS: MHA/GQA/MQA head mapping; shared and expanded KV agree')


def check_latent():
    latent = [[1., 2.], [.5, -1.], [-.5, 1.5]]
    key_up = [[[1., 2.], [0., 1.], [1., -.5]],
              [[.5, 1.], [2., 0.], [-1., 1.]]]
    value_up = [[[1., 0.], [1., 2.]], [[.5, 1.], [2., -1.]]]
    queries = [[2., 3., -.5], [1., -.5, 2.]]
    q_position = [rotate([1., .2], .9), rotate([-.3, 1.], .9)]
    k_position = [rotate([.1 + j, .7], .2 * j) for j in range(3)]
    # Keep the model's score scale: 3 content + 2 position dimensions.
    # Do NOT replace it with sqrt(latent_dim=2) after absorption.
    scale = math.sqrt(5)
    for h in range(2):
        keys = [mv(key_up[h], c) for c in latent]
        values = [mv(value_up[h], c) for c in latent]
        full_scores = [(dot(queries[h], keys[j])
                        + dot(q_position[h], k_position[j])) / scale
                       for j in range(3)]
        latent_q = mv(transpose(key_up[h]), queries[h])
        absorbed_scores = [(dot(latent_q, latent[j])
                            + dot(q_position[h], k_position[j])) / scale
                           for j in range(3)]
        close(full_scores, absorbed_scores)
        full_output = weighted(softmax(full_scores), values)
        short_output = weighted(softmax(absorbed_scores), latent)
        close(full_output, mv(value_up[h], short_output))
    close(mv(transpose([[1., 2.], [0., 1.]]), [2., 3.]), [2., 7.])
    print('PASS: MLA expanded and absorbed content scores/outputs, with position branch')


if __name__ == '__main__':
    check_shared_kv()
    check_latent()
    common = 4096 * 32 * 2 / 2**20
    capacities = [common * 2 * h * 128 for h in [32, 8, 1]]
    capacities.append(common * (512 + 64))
    assert capacities == [2048., 512., 64., 144.]
    print('Toy cache MiB:', capacities, '(different architectures; not quality equivalence)')
