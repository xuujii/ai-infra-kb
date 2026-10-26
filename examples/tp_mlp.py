"""Two-rank tensor-parallel MLP, CPU arithmetic only, no real collectives."""
from math import isclose


def linear(x, w):
    return [sum(a*b for a,b in zip(x,col)) for col in zip(*w)]


def add(x,y):
    return [a+b for a,b in zip(x,y)]


def outer(x,y):
    return [[a*b for b in y] for a in x]


def backward_input(dy,w):
    return [sum(a*b for a,b in zip(row,dy)) for row in w]


if __name__ == '__main__':
    x=[1,2]
    w1=[[1,2,0,1],[0,1,3,2]]
    w2=[[1,0],[0,1],[1,1],[2,0]]
    dy=[2,-1]
    h=[max(0,v) for v in linear(x,w1)]
    y=linear(h,w2)
    columns=[[row[:2] for row in w1],[row[2:] for row in w1]]
    local_h=[[max(0,v) for v in linear(x,w)] for w in columns]
    partials=[linear(local_h[0],w2[:2]),linear(local_h[1],w2[2:])]
    assert local_h[0]+local_h[1] == h == [1,4,6,5]
    assert add(*partials) == y == [17,10]
    local_dh=[backward_input(dy,w2[:2]),backward_input(dy,w2[2:])]
    local_dx=[backward_input(local_dh[i],columns[i]) for i in range(2)]
    dh=backward_input(dy,w2)
    dx=backward_input(dh,w1)
    assert add(*local_dx) == dx == [4,10]
    # Weight gradients concatenate by the corresponding storage axis.
    dw1_full=outer(x,dh)
    dw1_parts=[outer(x,g) for g in local_dh]
    assert [a+b for a,b in zip(*dw1_parts)] == dw1_full
    assert outer(local_h[0],dy)+outer(local_h[1],dy) == outer(h,dy)
    # Independent finite-difference check of dX for scalar objective Y dot dY.
    def loss(value):
        output=linear([max(0,v) for v in linear(value,w1)],w2)
        return sum(a*b for a,b in zip(output,dy))
    eps=1e-5
    for i in range(2):
        plus,minus=list(x),list(x)
        plus[i]+=eps;minus[i]-=eps
        assert isclose((loss(plus)-loss(minus))/(2*eps),dx[i],abs_tol=1e-8)
    print('column outputs:',local_h,'row contributions:',partials,'complete output:',y)
    print('dH shards:',local_dh,'dX contributions:',local_dx,'complete dX:',dx)
    print('Forward, gradient sharding and finite differences passed; no communication performance measured.')
