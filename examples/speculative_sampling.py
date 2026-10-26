"""Enumerate one exact speculative-sampling step; not a model benchmark."""
from math import isclose


def distribution_after_step(p, q):
    assert len(p) == len(q)
    assert all(x >= 0 for x in p + q)
    assert isclose(sum(p), 1) and isclose(sum(q), 1)
    accepted = [min(px, qx) for px, qx in zip(p, q)]
    residual = [max(px - qx, 0) for px, qx in zip(p, q)]
    rejected = sum(residual)
    corrected = [a + r for a, r in zip(accepted, residual)]
    # A tempting but incorrect alternative: sample directly from p on rejection.
    naive = [a + rejected * px for a, px in zip(accepted, p)]
    return accepted, rejected, corrected, naive


if __name__ == "__main__":
    p, q = [0.5, 0.3, 0.2], [0.2, 0.5, 0.3]
    accepted, rejected, corrected, naive = distribution_after_step(p, q)
    print("target p:", p, "draft q:", q)
    print("acceptance probabilities:", [min(1, px / qx) for px, qx in zip(p, q)])
    print("accepted probability mass:", accepted)
    print("rejection probability:", round(rejected, 8))
    print("correct final distribution:", [round(x, 8) for x in corrected])
    print("incorrect resample-from-p:", [round(x, 8) for x in naive])
    for target, draft in ((p, q), (p, p), ([1, 0], [0, 1]),
                          ([0, 0.6, 0.4], [0.2, 0.8, 0])):
        _, _, result, _ = distribution_after_step(target, draft)
        assert all(isclose(x, y, abs_tol=1e-12) for x, y in zip(result, target))
    assert any(not isclose(x, y) for x, y in zip(naive, p))
    print("Probability checks passed, including identical and disjoint distributions.")
    print("This validates a single-step probability mechanism, not a full decoding engine.")
