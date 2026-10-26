"""Uniform integer quantization teaching example, Python 3 standard library.

Uses symmetric range [-7,7] for four bits (one code unused), round-to-even.
This is not FP8, GPTQ, AWQ, QAT, or a GPU/NPU performance benchmark.
"""
from math import isclose


def quantize(values, scale, qmin=-7, qmax=7):
    assert scale > 0
    return [min(qmax, max(qmin, round(value / scale))) for value in values]


def dequantize(codes, scale):
    return [value * scale for value in codes]


def dot(a, b):
    assert len(a) == len(b)
    return sum(x * y for x, y in zip(a, b))


def pack_int4(codes):
    """Two's-complement nibbles: two signed four-bit codes per byte."""
    assert len(codes) % 2 == 0
    assert all(-8 <= code <= 7 for code in codes)
    return bytes((codes[i] & 15) | ((codes[i + 1] & 15) << 4)
                 for i in range(0, len(codes), 2))


def unpack_int4(data):
    result = []
    for byte in data:
        for code in (byte & 15, byte >> 4):
            result.append(code - 16 if code >= 8 else code)
    return result


if __name__ == '__main__':
    values = [-1.2, -0.46, 0, 0.74, 1.2]
    for scale in (0.1, 0.2, 0.3):
        codes = quantize(values, scale)
        restored = dequantize(codes, scale)
        error = max(abs(a - b) for a, b in zip(values, restored))
        print(f'scale={scale}: codes={codes}, restored={[round(x, 6) for x in restored]}, max error={error:.6f}')
    assert quantize(values, 0.2) == [-6, -2, 0, 4, 6]
    assert isclose(abs(values[-1] - dequantize(quantize(values, 0.1), 0.1)[-1]), 0.5)

    x, w, scale = [0.32, -0.82, 1.12, 0.62], [1.23, -0.44, 0.78, 0.15], 0.2
    qx, qw = quantize(x, scale), quantize(w, scale)
    integer_accumulator = dot(qx, qw)
    both_quantized = integer_accumulator * scale * scale
    weight_only = dot(x, dequantize(qw, scale))
    assert isclose(dot(x, w), 1.721)
    assert integer_accumulator == 47 and isclose(both_quantized, 1.88)
    assert isclose(both_quantized, dot(dequantize(qx, scale), dequantize(qw, scale)))
    packed = pack_int4(qw)
    assert len(packed) == 2 and unpack_int4(packed) == qw
    # Verify the full signed code range, not just positive values.
    signed_codes = list(range(-8, 8))
    assert unpack_int4(pack_int4(signed_codes)) == signed_codes
    print(f'original dot={dot(x, w):.6f}, weight-only={weight_only:.6f}, both={both_quantized:.6f}')
    print(f'weight codes={qw}, packed bytes={packed.hex()}, restored codes={unpack_int4(packed)}')

    small = [0.2, -0.3, 0.4]
    common = dequantize(quantize(small, 8 / 7), 8 / 7)
    separate = dequantize(quantize(small, 0.4 / 7), 0.4 / 7)
    assert common == [0, 0, 0]
    assert sum((a-b)**2 for a,b in zip(small,separate)) < sum(a*a for a in small)
    print('outlier shared-scale:', common, 'small-group scale:', [round(v, 6) for v in separate])
    print('Numeric and packing checks passed. Python lists are not low-bit storage; only packed bytes demonstrate packing.')
