"""Weighted objectives, learning-rate stability and synthetic quality milestones."""
from math import isclose, ceil


def objective(theta, labels, weights=None):
    weights = weights or [1/len(labels)]*len(labels)
    assert len(weights) == len(labels) and isclose(sum(weights), 1)
    return sum(w*.5*(theta-y)**2 for y, w in zip(labels, weights))


def gradient(theta, labels, weights=None):
    weights = weights or [1/len(labels)]*len(labels)
    return sum(w*(theta-y) for y, w in zip(labels, weights))


def descent(lr, target=2/3, max_steps=100):
    theta = 4.0
    for step in range(1, max_steps+1):
        theta -= lr*(theta-target)
        if abs(theta-target) < 1e-4:
            return step, theta
    return None, theta


RUNS = {
    'baseline': (2000, 1.0, 0),
    'kernel': (2000, .6, 0),
    'recipe': (4000, .8, 0),
    'data': (1200, .9, 300),
}


def time_to_quality(required, step_time, preparation, interval, max_steps=5000):
    assert interval > 0 and step_time > 0
    if required is None:
        return None  # cannot call a planned ending a successful quality milestone
    checks = ceil(required/interval)
    confirmed = checks*interval
    if confirmed > max_steps:
        return None
    return dict(confirmed=confirmed, evaluations=checks,
                total=preparation+confirmed*step_time+checks*20)


def main():
    original, unique, preserved_weights = [0, 0, 2], [0, 2], [2/3, 1/3]
    for theta in [-1, 0, 2/3, 1, 3]:
        assert isclose(objective(theta, original), objective(theta, unique, preserved_weights))
        assert isclose(gradient(theta, original), gradient(theta, unique, preserved_weights), abs_tol=1e-12)
    assert isclose(gradient(2/3, original), 0, abs_tol=1e-12)
    assert not isclose(gradient(2/3, unique), 0, abs_tol=1e-12)
    assert isclose(gradient(.5, unique, [.75, .25]), 0, abs_tol=1e-12)
    assert gradient(.5, unique) != 0
    theta, eps = .3, 1e-5
    numeric = (objective(theta+eps, unique, [.75, .25])-objective(theta-eps, unique, [.75, .25]))/(2*eps)
    assert isclose(numeric, gradient(theta, unique, [.75, .25]), abs_tol=1e-10)
    slow, fast, unstable = descent(.2), descent(.5), descent(2.2)
    assert fast[0] < slow[0] and unstable[0] is None
    assert abs(unstable[1]-2/3) > abs(4-2/3)
    totals = {k:time_to_quality(*v, 500)['total'] for k, v in RUNS.items()}
    assert totals == dict(baseline=2080, kernel=1280, recipe=3360, data=1710)
    assert time_to_quality(*RUNS['data'], 500)['confirmed'] == 1500
    assert time_to_quality(*RUNS['data'], 1000)['total'] == 2140
    assert time_to_quality(None, 1, 0, 500) is None
    assert time_to_quality(6000, 1, 0, 500) is None
    train = {'doc-A', 'doc-B'}
    validation = {'doc-C', 'doc-B'}
    assert train & validation == {'doc-B'}  # exact overlap toy, not near-dedup
    print('PASS: dedup changes an unweighted objective; frequency weights preserve it')
    print('PASS: domain mixture gradient by finite difference; toy learning-rate stability')
    print('PASS: first confirmed quality milestone includes evaluation/preparation; missing target rejected')
    print('Synthetic totals at 500-step evaluation:', totals)
    print('No language model, data-quality predictor or real scaling-law fit')


if __name__ == '__main__':
    main()
