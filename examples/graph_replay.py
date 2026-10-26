"""Fixed-buffer replay and asynchronous submission model. No CUDA/ACL calls."""


class BufferReplay:
    def __init__(self, buffer):
        self.captured_input = buffer
        self.output = [0]*len(buffer)

    def replay(self):
        for i, value in enumerate(self.captured_input):
            self.output[i] = 2*value
        return self.output


def queued_end(tasks, submit_us, compute_us):
    host_end, device_end = 0, 0
    for _ in range(tasks):
        host_end += submit_us
        device_end = max(host_end, device_end)+compute_us
    return device_end


def replay_end(tasks, graph_submit_us, compute_us):
    return graph_submit_us+tasks*compute_us


if __name__ == '__main__':
    variable = [-1,2]
    original = variable
    graph = BufferReplay(variable)
    output = graph.replay()
    assert output == [-2,4]
    snapshot = output.copy()
    variable[:] = [3,4]
    assert graph.replay() == [6,8]
    assert snapshot == [-2,4] and output == [6,8]  # old view overwritten
    variable = [9,10]  # rebind name, keep captured reference unchanged
    assert graph.replay() == [6,8]
    original[:] = variable
    assert graph.replay() == [18,20]
    assert graph.captured_input is original and graph.captured_input is not variable
    assert queued_end(10,4,1) == 41 and replay_end(10,4,1) == 14
    assert queued_end(10,4,10) == replay_end(10,4,10) == 104
    print('outputs: [-2,4] -> [6,8] -> [6,8] after rebinding -> [18,20] after copy')
    print('10 tasks, host 4us: device 1us gives 41 vs 14us; device 10us gives 104 vs 104us.')
    print('Buffer, output-overwrite and queue checks passed. Not a hardware benchmark.')
