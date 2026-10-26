"""Toy block table: CPU only, not an inference engine or attention kernel."""
BLOCK_SIZE = 4
TABLE = [7, 2, 9]
physical_pool = {page: [None] * BLOCK_SIZE for page in TABLE}
tokens = list(range(10))


def address(position):
    logical_block, offset = divmod(position, BLOCK_SIZE)
    return TABLE[logical_block], offset


for position, token in enumerate(tokens):
    page, offset = address(position)
    physical_pool[page][offset] = (token + 100, token + 200)

recovered = [physical_pool[address(p)[0]][address(p)[1]] for p in range(len(tokens))]
assert recovered == [(token + 100, token + 200) for token in tokens]
assert address(3) == (7, 3)
assert address(4) == (2, 0)
assert address(8) == (9, 0)
allocated = len(TABLE) * BLOCK_SIZE
print("logical -> physical:", TABLE)
print("ordered logical K/V:", recovered)
print(f"valid tokens={len(tokens)}, allocated={allocated}, unused={allocated-len(tokens)}")
print("No sharing, asynchronous writes, reference counting or attention computation.")
