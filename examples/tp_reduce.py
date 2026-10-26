"""Two-rank row-parallel Linear emulated on CPU.
Checks reduction identity, not real collectives or MC2 performance.
"""


def matmul(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


x = [[1, 2, 3, 4], [5, 6, 7, 8]]
w = [[1, 0, 2], [0, 1, 1], [2, 1, 0], [1, 2, 1]]
x0, x1 = [row[:2] for row in x], [row[2:] for row in x]
w0, w1 = w[:2], w[2:]
y0, y1 = matmul(x0, w0), matmul(x1, w1)
reduced = [[a + b for a, b in zip(row0, row1)] for row0, row1 in zip(y0, y1)]
assert reduced == matmul(x, w)
chunked = []
for row0, row1 in zip(x0, x1):
    partial0, partial1 = matmul([row0], w0)[0], matmul([row1], w1)[0]
    chunked.append([a + b for a, b in zip(partial0, partial1)])
assert chunked == reduced
print("rank 0 partial:", y0)
print("rank 1 partial:", y1)
print("sum of partials:", reduced)
print("M-axis chunks:", chunked)
print("Correctness only; real communication and overlap require a hardware backend.")
