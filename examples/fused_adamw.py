"""AdamW execution semantics and logical traffic, stdlib CPU only.
This is not a device kernel or an 8-bit optimizer implementation.
"""
from copy import deepcopy
from math import sqrt, isclose


def state(values, lr=0.01, decay=0.1):
    return dict(theta=list(values), m=[0.0]*len(values),
                v=[0.0]*len(values), steps=[0]*len(values), lr=lr, decay=decay)


def update(s, grad, fused, overflow=False, coupled=False):
    if overflow:
        return
    b1, b2, eps = 0.9, 0.999, 1e-8
    active = [i for i, g in enumerate(grad) if g is not None]
    # grad=None skips a parameter entirely; a numeric zero does not.
    g = [None if x is None else x + (s['decay']*s['theta'][i] if coupled else 0)
         for i, x in enumerate(grad)]
    def moment(i):
        s['steps'][i] += 1
        s['m'][i] = b1*s['m'][i] + (1-b1)*g[i]
    def variance(i):
        s['v'][i] = b2*s['v'][i] + (1-b2)*g[i]*g[i]
    def parameter(i):
        t = s['steps'][i]
        mh = s['m'][i]/(1-b1**t)
        vh = s['v'][i]/(1-b2**t)
        decay = 0 if coupled else s['decay']
        s['theta'][i] = s['theta'][i]*(1-s['lr']*decay) - s['lr']*mh/(sqrt(vh)+eps)
    if fused:
        for i in active:
            moment(i)
            variance(i)
            parameter(i)
    else:
        for i in active:
            moment(i)
        for i in active:
            variance(i)
        for i in active:
            parameter(i)


def quantize(values):
    peak = max(map(abs, values), default=0)
    if peak == 0:
        return [0]*len(values), 0.0, [0.0]*len(values)
    scale = peak/127
    codes = [max(-127, min(127, round(x/scale))) for x in values]
    return codes, scale, [q*scale for q in codes]


def main():
    first = state([1, -2])
    update(first, [.1, -.2], True)
    assert all(isclose(x, y, abs_tol=2e-9) for x, y in zip(first['theta'], [.989, -1.988]))
    # Two independently configured parameter groups; compare every state field.
    for lr, decay in [(0.01, .1), (.002, 0)]:
        a, b = state([1, -2, .5], lr, decay), state([1, -2, .5], lr, decay)
        for grads, overflow in [([.1, -.2, None], False), ([0, None, .3], False),
                                ([.4, .8, .2], True), ([None, .15, 0], False)]:
            before = deepcopy(a)
            update(a, grads, False, overflow)
            update(b, grads, True, overflow)
            assert a == b
            if overflow:
                assert a == before
            for i, g in enumerate(grads):
                if g is None:
                    assert all(a[k][i] == before[k][i] for k in ['theta', 'm', 'v', 'steps'])
        assert a['steps'] == [2, 2, 2]
    zero, absent = state([1]), state([1])
    update(zero, [0], True)
    update(absent, [None], True)
    assert zero['theta'] == [.999] and absent['theta'] == [1]
    assert zero['steps'] == [1] and absent['steps'] == [0]
    correct, wrong = state([1]), state([1])
    update(correct, [.1], True)
    update(wrong, [.1], True, coupled=True)
    assert correct['m'] != wrong['m'] and correct['theta'] != wrong['theta']
    for values in [[0, 0], [.1, -.3, 1], [100, .01, -.02]]:
        codes, scale, restored = quantize(values)
        assert all(abs(x-y) <= scale/2+1e-12 for x, y in zip(values, restored))
        assert all(-127 <= q <= 127 for q in codes)
    assert quantize([100, .01])[2][1] == 0
    n = 1_048_576
    assert (12+12+16)*n == 40*n
    assert (16+12)*n == 28*n
    print('PASS: multi-step AdamW parameters/moments/clocks, groups, None/zero, overflow, coupled-L2 negative case')
    print('PASS: uniform signed-state quantization and outlier example; not real 8-bit Adam')
    print('Logical FP32 traffic for 1,048,576 elements: separate 40 MiB, fused 28 MiB; no device timing')


if __name__ == '__main__':
    main()
