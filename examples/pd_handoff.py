"""CPU PD cache/ownership demonstration; no device/network benchmark."""
from copy import deepcopy
from dataclasses import dataclass
from causal_kv import empty_cache, forward_chunk, max_error


@dataclass
class Ticket:
    request: str
    generation: int
    target_reserved: bool = True
    transfer_ready: bool = False
    cancelled: bool = False
    committed: bool = False

    def commit(self, callback_generation):
        assert not self.cancelled and callback_generation == self.generation
        assert self.target_reserved and self.transfer_ready
        self.committed = True


def reject(action):
    try:
        action()
    except AssertionError:
        return
    raise AssertionError('Invalid handoff accepted')


if __name__ == '__main__':
    prompt, first_token = [2, 5, 1, 4], 7  # Forced token isolates cache semantics.
    source = empty_cache()
    forward_chunk(prompt, source)
    assert all(len(c['k']) == 4 for c in source)
    ticket = Ticket('A', 1)
    reject(lambda: ticket.commit(1))
    target = deepcopy(source)
    ticket.transfer_ready = True
    ticket.commit(1)
    actual = forward_chunk([first_token], target)
    reference = forward_chunk(prompt + [first_token], empty_cache())[-1:]
    assert max_error(actual, reference) < 1e-12
    assert all(len(c['k']) == 4 for c in source) and all(len(c['k']) == 5 for c in target)
    wrong = forward_chunk([first_token], deepcopy(target))
    assert max_error(wrong, reference) > 1e-6
    cancelled = Ticket('B', 2, transfer_ready=True, cancelled=True)
    reject(lambda: cancelled.commit(2))
    replacement = Ticket('B', 3, transfer_ready=True)
    reject(lambda: replacement.commit(2))
    transfer_ms = 512 * 2 ** 20 / (25 * 2 ** 30) * 1000
    assert 40 + transfer_ms + 2 + 4 == 66
    assert 40 + 30 + 4 == 74 and 40 + 4 < 66
    print('PASS: transferred prompt KV plus first-token input matches full forward')
    print('PASS: premature/cancelled/stale handoffs rejected; duplicate processing differs')
    print('Teaching first/second: colocated 70/74 ms, separate 40/66 ms')
