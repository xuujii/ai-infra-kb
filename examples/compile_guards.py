"""Teaching guards/cache/bucketing model, not a real framework compiler."""
from math import floor


class TeachingCache:
    def __init__(self, dynamic_m=False):
        self.dynamic_m = dynamic_m
        self.variants = set()
        self.compilations = 0

    def call(self, m, dtype='float32', stride='contiguous'):
        assert m > 0
        # Toy dynamic contract: M in [1,4]. Larger M still specializes.
        shape_guard = 'M in [1,4]' if self.dynamic_m and 1 <= m <= 4 else m
        key = (shape_guard, dtype, stride)
        hit = key in self.variants
        if not hit:
            self.variants.add(key)
            self.compilations += 1
        return hit


def bucket_relu(rows):
    # No cross-row operation; padded outputs are removed.
    capacity = next((n for n in (1,2,4,8) if n >= len(rows)), None)
    assert capacity is not None
    padded = rows + [0]*(capacity-len(rows))
    output = [max(x, 0) for x in padded]
    return output[:len(rows)], capacity


def break_even(compilation_ms, eager_ms, compiled_ms):
    if compiled_ms >= eager_ms:
        return None
    return floor(compilation_ms/(eager_ms-compiled_ms))+1


if __name__ == '__main__':
    shapes = [1,1,2,4,2,1]
    exact, dynamic = TeachingCache(), TeachingCache(True)
    assert [exact.call(m) for m in shapes] == [False,True,False,False,True,True]
    assert [dynamic.call(m) for m in shapes] == [False,True,True,True,True,True]
    assert exact.compilations == 3 and dynamic.compilations == 1
    assert not exact.call(1, stride='transposed')
    assert not dynamic.call(8)
    assert not dynamic.call(2, dtype='float16')
    result, capacity = bucket_relu([-2,3,1])
    assert result == [0,3,1] and capacity == 4
    assert break_even(200, 1, .6) == 501
    assert break_even(200, 1, 1.1) is None
    assert 200+.6*100 > 100 and 200+.6*1000 < 1000
    print('Toy shapes:', shapes, 'exact variants: 3; dynamic-range variants: 1')
    print('dtype/stride/range changes reject reuse; bucket valid output:', result)
    print('Break-even: 501 calls. Does not predict torch.compile compilation counts or speed.')
