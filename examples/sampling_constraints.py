"""CPU sampling contract, top-k selection and a finite yes/no language.
Does not implement FlashInfer's sorting-free rejection kernel or full JSON grammar.
"""
import heapq
import math


def softmax(logits, allowed, temperature=1.):
    if temperature <= 0:
        raise ValueError('Greedy is a separate path')
    indices = [i for i in range(len(logits)) if i in allowed]
    if not indices:
        raise ValueError('No legal token')
    maximum = max(logits[i] / temperature for i in indices)
    values = [math.exp(logits[i] / temperature - maximum) if i in allowed else 0.
              for i in range(len(logits))]
    total = sum(values)
    if not total > 0 or not math.isfinite(total):
        raise ValueError('Invalid probability row')
    return [v / total for v in values]


def renorm(probs, kept):
    mass = sum(probs[i] for i in kept)
    if mass <= 0:
        raise ValueError('No remaining candidate')
    return [p / mass if i in kept else 0. for i, p in enumerate(probs)]


def top_k(probs, k, partial=False):
    candidates = [i for i, p in enumerate(probs) if p > 0]
    key = lambda i: (probs[i], -i)  # lower token ID wins ties in this example
    chosen = heapq.nlargest(k, candidates, key=key) if partial else sorted(candidates, key=key, reverse=True)[:k]
    return renorm(probs, set(chosen))


def top_p(probs, threshold):
    if not 0 < threshold <= 1:
        raise ValueError('top_p must be in (0,1]')
    candidates = sorted([i for i, p in enumerate(probs) if p > 0], key=lambda i: (-probs[i], i))
    kept, mass = set(), 0.
    for i in candidates:
        kept.add(i)
        mass += probs[i]
        if mass + 1e-14 >= threshold:
            break
    return renorm(probs, kept)


def cdf_sample(probs, uniform):
    cumulative = 0.
    for i, p in enumerate(probs):
        cumulative += p
        if uniform < cumulative:
            return i
    return max(i for i, p in enumerate(probs) if p > 0)


def close(a, b):
    assert all(abs(x - y) < 1e-12 for x, y in zip(a, b)), (a, b)


class FiniteLanguage:
    def __init__(self):
        self.prefix, self.ended = '', False

    def allowed(self, fragment):
        if self.ended:
            return False
        if fragment == '<EOS>':
            return self.prefix in ['yes', 'no']
        return any(word.startswith(self.prefix + fragment) for word in ['yes', 'no'])

    def accept(self, fragment):
        if not self.allowed(fragment):
            raise ValueError('Illegal fragment')
        if fragment == '<EOS>':
            self.ended = True
        else:
            self.prefix += fragment

    def snapshot(self):
        return self.prefix, self.ended

    def restore(self, snapshot):
        self.prefix, self.ended = snapshot


if __name__ == '__main__':
    logits = [math.log(p) for p in [.4, .3, .2, .1]]
    for allowed in [{0, 1, 2, 3}, {2, 3}, {1}, {0, 2}]:
        for tau in [.5, 1., 2.]:
            probs = softmax(logits, allowed, tau)
            close(probs, softmax([x + 1000 for x in logits], allowed, tau))
            for k in [1, 2, 4]:
                for threshold in [.5, .8, 1.]:
                    reference = top_p(top_k(probs, k), threshold)
                    partial = top_p(top_k(probs, k, partial=True), threshold)
                    close(reference, partial)
                    # Deterministic quantile grid checks the probability intervals, not RNG bits.
                    counts = [0] * 4
                    for step in range(1000):
                        counts[cdf_sample(partial, (step + .5) / 1000)] += 1
                    assert all(abs(n / 1000 - p) <= .0011 for n, p in zip(counts, partial))
    original = softmax(logits, {0, 1, 2, 3})
    sequential = top_p(top_k(original, 2), .5)
    other_order = top_k(top_p(original, .5), 2)
    close(sequential, [1., 0., 0., 0.])
    close(other_order, [4/7, 3/7, 0., 0.])
    close(top_k([.5, .5, 0.], 1, partial=True), [1., 0., 0.])
    for invalid in [set()]:
        try:
            softmax(logits, invalid)
            raise AssertionError('Empty mask accepted')
        except ValueError:
            pass
    try:
        renorm(original, set())
        raise AssertionError('Empty filter accepted')
    except ValueError:
        pass
    state = FiniteLanguage()
    assert state.allowed('yes') and state.allowed('ye') and not state.allowed('yes!')
    state.accept('y')
    saved = state.snapshot()
    state.accept('es')
    assert state.allowed('<EOS>') and not state.allowed('no')
    state.restore(saved)
    assert state.prefix == 'y' and not state.allowed('<EOS>')
    state.accept('e')
    state.accept('s')
    state.accept('<EOS>')
    assert state.ended and not state.allowed('yes')
    print('PASS: sorted/partial top-k distributions, masks, ties and stable Softmax')
    print('PASS: filter-order counterexample, CDF intervals, finite-language state/rollback')
