"""Structural MLP rewrite and distillation-logit gradients; stdlib CPU only."""
from math import exp, log, isclose


def matmul(a, b):
    assert len(a[0]) == len(b)
    return [[sum(x*y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def mlp(x, w1, w2, mask=None):
    hidden = matmul(x, w1)
    active = [[max(0, v)*(1 if mask is None else mask[j]) for j, v in enumerate(row)] for row in hidden]
    return matmul(active, w2)


def softmax(z, temperature=1):
    assert temperature > 0
    shifted = [(v-max(z))/temperature for v in z]
    e = [exp(v) for v in shifted]
    return [v/sum(e) for v in e]


def log_softmax(z, temperature=1):
    shifted = [(v-max(z))/temperature for v in z]
    norm = log(sum(exp(v) for v in shifted))
    return [v-norm for v in shifted]


def loss(z, teacher, label, temperature, alpha):
    p = softmax(teacher, temperature)
    lp, lq = log_softmax(teacher, temperature), log_softmax(z, temperature)
    kl = sum(pi*(a-b) for pi, a, b in zip(p, lp, lq))
    return (1-alpha)*(-log_softmax(z)[label]) + alpha*temperature**2*kl


def gradient(z, teacher, label, temperature, alpha):
    q1, qt, pt = softmax(z), softmax(z, temperature), softmax(teacher, temperature)
    return [(1-alpha)*(q1[i]-(i == label)) + alpha*temperature*(qt[i]-pt[i]) for i in range(len(z))]


def main():
    x = [[1, 2, -.5, 1], [0, -1, 2, .5]]
    w1 = [[(i+j+1)/10 for j in range(8)] for i in range(4)]
    w2 = [[(i+j+1)/20 for j in range(4)] for i in range(8)]
    full = mlp(x, w1, w2)
    keep = [0, 2, 5, 7]  # a non-contiguous keep set checks paired row/column mapping
    mask = [int(j in keep) for j in range(8)]
    masked = mlp(x, w1, w2, mask)
    compact = mlp(x, [[row[j] for j in keep] for row in w1], [w2[j] for j in keep])
    assert all(isclose(a, b, abs_tol=1e-12) for ra, rb in zip(masked, compact) for a, b in zip(ra, rb))
    assert any(abs(a-b) > .01 for ra, rb in zip(full, compact) for a, b in zip(ra, rb))
    wrong = mlp(x, [[row[j] for j in keep] for row in w1], [w2[j] for j in reversed(keep)])
    assert any(abs(a-b) > .01 for ra, rb in zip(masked, wrong) for a, b in zip(ra, rb))
    assert (4*8+8*4, 4*len(keep)+len(keep)*4) == (64, 32)
    teacher = [2.0, 1.0, 0.0]
    for t in [1, 2, 4]:
        for alpha in [0, .7, 1]:
            z = [.2, -.3, .1]
            g = gradient(z, teacher, 0, t, alpha)
            eps = 1e-5
            for i in range(3):
                plus, minus = z[:], z[:]
                plus[i] += eps
                minus[i] -= eps
                numeric = (loss(plus, teacher, 0, t, alpha)-loss(minus, teacher, 0, t, alpha))/(2*eps)
                assert isclose(numeric, g[i], abs_tol=1e-9)
    z = [0.0, 0.0, 0.0]
    g = gradient(z, teacher, 0, 2, 1)
    assert all(isclose(a, b, abs_tol=1e-4) for a, b in zip(g, [-.3463, .0523, .2940]))
    assert isclose(sum(g), 0, abs_tol=1e-12)
    initial = loss(z, teacher, 0, 2, .7)
    for _ in range(100):
        g = gradient(z, teacher, 0, 2, .7)
        z = [v-.1*d for v, d in zip(z, g)]
    assert loss(z, teacher, 0, 2, .7) < initial
    assert teacher == [2.0, 1.0, 0.0]
    # Stable probabilities and log loss for large logits, no exp(1000).
    assert isclose(sum(softmax([1000, 999, 998], 2)), 1, abs_tol=1e-12)
    assert isclose(loss([1000, 999, 998], [2, 1, 0], 0, 2, 1), 0, abs_tol=1e-12)
    print('PASS: paired structural pruning matches masked reference, not original; wrong pairing rejected')
    print('PASS: mixed hard/soft-loss gradients by finite differences, T=1/2/4; student-only logit optimization')
    print('MLP dense multiply count per token: original/masked 64, compact 32; not device timing')
    print('No LLM training, automatic pruning search or hardware sparsity implemented')


if __name__ == '__main__':
    main()
