"""Two-layer causal-attention teaching network; Python 3 standard library.

Compare complete, token-at-a-time, chunked, and shared-prefix execution.
No GPU, training, tokenizer, RoPE, or real serving engine; no speed claims.
"""
from copy import deepcopy
from math import exp, sin, sqrt, tanh

DIM, LAYERS = 4, 2


def project(vector, layer, kind):
    # Fixed, deliberately different Q/K/V matrices at each layer.
    return [sum(vector[j] * sin((j + 1) * (i + 2) + layer * 3 + kind)
                / DIM for j in range(DIM)) for i in range(DIM)]


def embed(token, position):
    # Toy position encoding: absolute positions must continue across chunks.
    return [sin((token + 1) * (i + 1)) + 0.05 * position * (i + 1)
            for i in range(DIM)]


def empty_cache():
    return [{"k": [], "v": []} for _ in range(LAYERS)]


def forward_chunk(tokens, cache):
    """Mutates each layer's cache; returns final-layer vectors for new inputs.

    Previous layer cache lengths represent the number of processed positions.
    Each new Q sees all past positions and only its own chunk prefix.
    """
    start = len(cache[0]["k"])
    assert all(len(c["k"]) == len(c["v"]) == start for c in cache)
    hidden = [embed(token, start + i) for i, token in enumerate(tokens)]
    for layer, c in enumerate(cache):
        queries = [project(x, layer, 0) for x in hidden]
        c["k"].extend(project(x, layer, 1) for x in hidden)
        c["v"].extend(project(x, layer, 2) for x in hidden)
        outputs = []
        for i, query in enumerate(queries):
            visible = start + i + 1  # absolute causal limit, not chunk length
            scores = [sum(q * k for q, k in zip(query, key)) / sqrt(DIM)
                      for key in c["k"][:visible]]
            maximum = max(scores)
            weights = [exp(value - maximum) for value in scores]
            denominator = sum(weights)
            attended = [sum(weights[j] * c["v"][j][d]
                            for j in range(visible)) / denominator
                        for d in range(DIM)]
            # A deterministic per-position transformation and residual.
            outputs.append([tanh(x + a) for x, a in zip(hidden[i], attended)])
        hidden = outputs
    return hidden


def max_error(a, b):
    assert len(a) == len(b)
    return max((abs(x - y) for u, v in zip(a, b) for x, y in zip(u, v)), default=0)


def run_chunks(tokens, sizes):
    assert sum(sizes) == len(tokens)
    cache, outputs, cursor = empty_cache(), [], 0
    for size in sizes:
        outputs.extend(forward_chunk(tokens[cursor:cursor + size], cache))
        cursor += size
        assert all(len(c["k"]) == cursor for c in cache)
    return outputs


if __name__ == "__main__":
    tokens = [2, 5, 1, 4, 7, 3, 6, 8]
    full = forward_chunk(tokens, empty_cache())
    for sizes in ([1] * 8, [3, 3, 2], [4, 4], [1, 3, 3, 1]):
        error = max_error(full, run_chunks(tokens, sizes))
        assert error < 1e-12
        print(f"chunks={sizes}: max error={error:.3g}")

    # Prefill four positions predicts E. Processing E predicts F, F predicts G.
    prompt, generated_inputs = tokens[:4], tokens[4:6]
    cache = empty_cache()
    logits_vector = forward_chunk(prompt, cache)[-1]
    assert max_error([logits_vector], [forward_chunk(prompt, empty_cache())[-1]]) < 1e-12
    for i, token in enumerate(generated_inputs):
        cached = forward_chunk([token], cache)[-1]
        baseline = forward_chunk(prompt + generated_inputs[:i + 1], empty_cache())[-1]
        assert max_error([cached], [baseline]) < 1e-12
    print("three prediction rounds: processed positions per layer 15 -> 6 (not speedup)")

    prefix = tokens[:4]
    prefix_cache = empty_cache()
    forward_chunk(prefix, prefix_cache)
    # Copies simulate private continuation; a real block manager may share
    # immutable prefix blocks instead. No hash/routing system implemented here.
    for suffix in ([7, 3], [9, 2, 6]):
        cached_suffix = forward_chunk(suffix, deepcopy(prefix_cache))
        full_suffix = forward_chunk(prefix + suffix, empty_cache())[len(prefix):]
        error = max_error(cached_suffix, full_suffix)
        assert error < 1e-12
        print(f"shared prefix + suffix={suffix}: max error={error:.3g}")
    assert all(len(c["k"]) == 4 for c in prefix_cache)

    # Identical later token IDs do not imply identical high-layer K/V.
    altered = empty_cache()
    forward_chunk([12] + prefix[1:], altered)
    difference = max_error(prefix_cache[1]["k"][1:], altered[1]["k"][1:])
    assert difference > 1e-6
    print(f"same later token IDs, changed ancestor context: layer-2 K difference={difference:.6g}")
    print("All causal-cache checks passed. No performance benchmark was run.")
