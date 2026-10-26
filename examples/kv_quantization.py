"""Effect of K/V integer quantization on one attention query; not a benchmark.

Uniform symmetric integer toy: not FP8, KIVI, or a serving implementation.
"""
from math import exp, isclose, sqrt


def quantize(values, scale, qmax=7):
    assert scale > 0
    return [min(qmax, max(-qmax, round(x / scale))) for x in values]


def restored(values, scale, qmax=7):
    return [q * scale for q in quantize(values, scale, qmax)]


def attention(query, keys, values):
    assert len(keys) == len(values) and len(query) > 0
    scores = [sum(a*b for a,b in zip(query,key)) / sqrt(len(query)) for key in keys]
    maximum = max(scores)
    exponents = [exp(x - maximum) for x in scores]
    probs = [x / sum(exponents) for x in exponents]
    output = [sum(prob * value[d] for prob,value in zip(probs,values))
              for d in range(len(values[0]))]
    return probs, output


if __name__ == '__main__':
    query, keys, values = [1.0], [[0.14],[0.26]], [[1.0],[3.0]]
    weights, original = attention(query, keys, values)
    _, quantized_k = attention(query, [restored(k, 0.2) for k in keys], values)
    assert isclose(original[0], 2.0599281035291435)
    assert quantized_k == [2.0]
    print('K-only example: probabilities=', [round(x, 6) for x in weights],
          'original output=', round(original[0], 6), 'quantized K output=', quantized_k)

    q = [1.0, 0.5]
    k = [[0.12, 1.05], [1.13, -0.18], [-0.32, 0.74]]
    v = [[0.2, 1.4], [1.2, -0.3], [-0.6, 0.8]]
    k_low = [restored(row, 0.2) for row in k]
    v_low = [restored(row, 0.2) for row in v]
    reference_weights, reference = attention(q,k,v)
    for label, ks, vs in [('original',k,v),('K only',k_low,v),('V only',k,v_low),('K and V',k_low,v_low)]:
        weights, out = attention(q,ks,vs)
        error = max(abs(a-b) for a,b in zip(out,reference))
        if label == 'V only':
            assert weights == reference_weights  # unchanged K gives unchanged scores
        print(f'{label}: output={[round(x, 6) for x in out]}, max output error={error:.6f}')

    # Same code interpreted with a new global scale corrupts stored values.
    old_scale, new_scale = 0.1, 0.2
    old_codes = quantize([0.5, -0.8], old_scale, qmax=127)
    valid_old = [q * old_scale for q in old_codes]
    invalid_old = [q * new_scale for q in old_codes]
    assert all(isclose(b, 2*a) for a,b in zip(valid_old,invalid_old))
    print('old codes:',old_codes,'correct old values:',valid_old,'wrong rescaled values:',invalid_old)

    elements = 2*32*8*128*4096
    metadata = elements // 128 * 2  # one FP16 scale per 128 scalar elements
    assert elements*2 == 512*2**20 and metadata == 4*2**20
    for bits in (16,8,4):
        data_bytes = elements*bits//8
        total = data_bytes + (metadata if bits < 16 else 0)
        print(f'{bits}-bit cache with toy metadata: {total/2**20:.0f} MiB')
    print('Attention and cache-scale checks passed. No real model quality or hardware speed was evaluated.')
