"""CPU tiling/read-count and gradient checks; not a GPU/NPU benchmark."""
def transpose(a):
    return [list(x) for x in zip(*a)]


def direct(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def tiled(a, b, tile):
    m, k, n = len(a), len(b), len(b[0])
    assert tile > 0 and all(len(row) == k for row in a)
    out, reads = [[0.0] * n for _ in range(m)], 0
    for i0 in range(0, m, tile):
        rows = list(range(i0, min(i0 + tile, m)))
        for j0 in range(0, n, tile):
            cols = list(range(j0, min(j0 + tile, n)))
            acc = [[0.0] * len(cols) for _ in rows]
            for k0 in range(0, k, tile):
                ks = list(range(k0, min(k0 + tile, k)))
                aa = [[a[i][q] for q in ks] for i in rows]
                bb = [[b[q][j] for j in cols] for q in ks]
                reads += len(rows) * len(ks) + len(ks) * len(cols)
                for ri in range(len(rows)):
                    for cj in range(len(cols)):
                        for q in range(len(ks)):
                            acc[ri][cj] += aa[ri][q] * bb[q][cj]
            for ri, i in enumerate(rows):
                for cj, j in enumerate(cols):
                    out[i][j] = acc[ri][cj]
    return out, reads


def error(a, b):
    return max(abs(x - y) for aa, bb in zip(a, b) for x, y in zip(aa, bb))


def loss(a, b):
    return sum(x * x / 2 for row in direct(a, b) for x in row)


if __name__ == '__main__':
    a = [[i * 4 + j for j in range(4)] for i in range(4)]
    b = [[(i + j) % 5 - 2 for j in range(4)] for i in range(4)]
    for t, expected_reads in [(1, 128), (2, 64), (4, 32)]:
        result, reads = tiled(a, b, t)
        assert result == direct(a, b) and reads == expected_reads
        print('tile', t, 'logical input reads', reads, 'output writes', 16)
    a = [[(i * 5 + j - 5) / 10 for j in range(5)] for i in range(3)]
    b = [[(i + j - 3) / 7 for j in range(2)] for i in range(5)]
    for t in (1, 2, 4, 8):
        assert error(tiled(a, b, t)[0], direct(a, b)) < 1e-12
    dy = direct(a, b)
    dx = tiled(dy, transpose(b), 2)[0]
    dw = tiled(transpose(a), dy, 2)[0]
    for matrix, gradient in [(a, dx), (b, dw)]:
        for i, row in enumerate(matrix):
            for j, old in enumerate(row):
                row[j] = old + 1e-6
                plus = loss(a, b)
                row[j] = old - 1e-6
                minus = loss(a, b)
                row[j] = old
                assert abs((plus - minus) / 2e-6 - gradient[i][j]) < 1e-8
    print('PASS: non-divisible shapes, dX and dW finite differences')
