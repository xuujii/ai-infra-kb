"""Two-layer scalar attention: independent samples vs isolated packing.

Pure Python, no performance/gradient claim. Includes a deliberately leaky
causal mask and incorrect position continuation as negative controls.
"""
from math import exp, isclose


def layer(hidden, docs, isolated=True):
    out = []
    for i, q in enumerate(hidden):
        visible = [j for j in range(i+1) if not isolated or docs[j] == docs[i]]
        scores = [q*hidden[j]*.02 for j in visible]
        top = max(scores)
        weights = [exp(score-top) for score in scores]
        out.append(sum(w*hidden[j] for w, j in zip(weights, visible))/sum(weights))
    return out


def forward(tokens, docs, positions, isolated=True):
    hidden = [token*.05+pos*.1 for token, pos in zip(tokens, positions)]
    for _ in range(2):
        hidden = layer(hidden, docs, isolated)
    return hidden


def aligned_targets(samples):
    # Targets already align with each input/logit position; do not shift twice.
    return [target for sample in samples for target in sample[1:]+[None]]


def padded_slots(batches):
    return sum(len(batch)*max(batch) for batch in batches)


if __name__ == '__main__':
    samples = [[11,12,13], [21,22]]
    tokens = sum(samples, [])
    docs, positions = [0,0,0,1,1], [0,1,2,0,1]
    separate = sum([forward(sample, [0]*len(sample), list(range(len(sample)))) for sample in samples], [])
    packed = forward(tokens, docs, positions)
    assert all(isclose(a,b,abs_tol=1e-12) for a,b in zip(separate,packed))
    leaky = forward(tokens, docs, positions, isolated=False)
    wrong_position = forward(tokens, docs, list(range(5)))
    assert not isclose(packed[3], leaky[3], abs_tol=1e-6)
    assert not isclose(packed[3], wrong_position[3], abs_tol=1e-6)
    assert aligned_targets(samples) == [12,13,None,22,None]
    assert sum(t is not None for t in aligned_targets(samples)) == 3
    # B1 only sees itself under sample-isolated causal attention.
    assert [j for j in range(4) if docs[j] == docs[3]] == [3]
    assert padded_slots([[2,8],[3,7]]) == 30
    assert padded_slots([[2,3],[7,8]]) == 22
    assert sum([2,8,3,7]) == 20
    print('Independent and packed two-layer outputs match:', packed)
    print('B1:', 'correct', packed[3], 'leaky', leaky[3], 'wrong position', wrong_position[3])
    print('Aligned targets: [12,13,None,22,None], 3 valid; padding slots: 30 -> 22.')
    print('Boundary, position, target and output checks passed. Not a device benchmark.')
