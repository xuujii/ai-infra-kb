"""CPU copies model saved-activation offload semantics, not CUDA/NPU timing."""
from math import tanh
from copy import deepcopy


def loss(w, v, x, target):
    y = v * tanh(w * x)
    return 0.5 * (y - target) ** 2


def forward(w, v, x, target):
    h = tanh(w * x)
    return {'h': h, 'x': x, 'v': v, 'error': v * h - target,
            'parameter_version': 0}


def backward(saved, version=0):
    assert saved['parameter_version'] == version
    dw = saved['error'] * saved['v'] * (1 - saved['h'] ** 2) * saved['x']
    dv = saved['error'] * saved['h']
    return dw, dv


def finite_difference(w, v, x, target, coordinate):
    eps = 1e-6
    args_plus, args_minus = [w, v, x, target], [w, v, x, target]
    args_plus[coordinate] += eps
    args_minus[coordinate] -= eps
    return (loss(*args_plus) - loss(*args_minus)) / (2 * eps)


def main():
    w, v, x, target = 0.6, -0.8, 1.3, 0.25
    device_saved = forward(w, v, x, target)
    resident_grad = backward(device_saved)
    host_saved = deepcopy(device_saved)  # Here copy completion is synchronous.
    del device_saved
    restored_saved = deepcopy(host_saved)
    restored_grad = backward(restored_saved)
    numerical = tuple(finite_difference(w, v, x, target, i) for i in range(2))
    assert resident_grad == restored_grad
    assert max(abs(a - b) for a, b in zip(restored_grad, numerical)) < 1e-9
    try:
        backward(restored_saved, version=1)
    except AssertionError:
        print('PASS: incompatible parameter version rejected')
    else:
        raise AssertionError('Wrong parameter version accepted')
    wrong = deepcopy(restored_saved)
    wrong['v'] = v - 0.1  # Demonstrates why using updated weights is wrong.
    assert abs(backward(wrong)[0] - numerical[0]) > 1e-3
    for lead, transfer, expected in [(3, 8, 5), (10, 8, 0), (12, 16, 4)]:
        deadline = 12
        start = deadline - lead
        finish = start + transfer
        assert max(0, finish - deadline) == expected
    print('PASS: restored activation gradients match resident and finite differences')
    print('dw, dv =', restored_grad)
    print('PASS: ideal prefetch waits are 5 ms, 0 ms, 4 ms')


if __name__ == '__main__':
    main()
