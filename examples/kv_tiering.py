"""CPU-only cache content/state demonstration; no device transfer benchmark."""
from copy import deepcopy
from causal_kv import empty_cache, forward_chunk, max_error


class TransferSlot:
    def __init__(self, data):
        self.device = deepcopy(data)
        self.host = None
        self.pending = False

    def start_offload(self):
        assert self.device is not None and not self.pending
        self.pending = True

    def finish_offload(self):
        assert self.pending
        self.host = deepcopy(self.device)
        self.pending = False

    def release_device(self):
        # Simplified single-owner slot; real systems also wait for all readers.
        assert not self.pending and self.host is not None
        self.device = None

    def restore(self):
        assert not self.pending and self.host is not None
        self.device = deepcopy(self.host)
        return self.device


def main():
    prompt, continuation = [2, 5, 1, 4], [7, 3]
    resident = empty_cache()
    forward_chunk(prompt, resident)
    slot = TransferSlot(resident)
    slot.start_offload()
    try:
        slot.release_device()
    except AssertionError:
        print('PASS: source reuse rejected before D2H completion')
    else:
        raise AssertionError('Pending transfer lost its source')
    slot.finish_offload()
    saved = deepcopy(slot.host)
    slot.release_device()
    restored = slot.restore()
    expected = forward_chunk(continuation, resident)
    actual = forward_chunk(continuation, restored)
    error = max_error(actual, expected)
    assert error < 1e-12
    assert slot.host == saved  # Restore must not alias the reusable host record.
    full = forward_chunk(prompt + continuation, empty_cache())[-2:]
    assert max_error(actual, full) < 1e-12
    # Evicting an idle prefix is exact if next use recomputes the full history.
    recomputed = forward_chunk(prompt + continuation, empty_cache())[-2:]
    assert max_error(recomputed, expected) < 1e-12
    # Silently deleting history without restoration changes the model result.
    missing_history = forward_chunk(continuation, empty_cache())
    bad = max_error(missing_history, expected)
    assert bad > 1e-5
    gib = 2 ** 30
    assert (512 * 2 ** 20) / (25 * gib) * 1000 == 20
    print(f'PASS: restored/resident/full results match, error={error:.3g}')
    print(f'PASS: lost-history negative case differs by {bad:.6g}')
    print('512 MiB at 25 GiB/s: 20 ms one-way ideal byte lower bound')


if __name__ == '__main__':
    main()
