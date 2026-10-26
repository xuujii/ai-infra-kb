"""Request-budget arithmetic, routing and stop contracts. No LLM or tokenizer."""
from math import isclose


def cost(n, g, preparation=0):
    assert n >= 0 and g >= 0 and preparation >= 0
    return preparation+.05*n+.0001*n*n+2*g


def route_cost(small_fraction, small=1, large=5, router=.1):
    assert 0 <= small_fraction <= 1
    return router+small_fraction*small+(1-small_fraction)*large


def fallback_cost(fallback_fraction, small=1, large=5, router=.1):
    assert 0 <= fallback_fraction <= 1
    return router+small+fallback_fraction*large


def generate(tokens, maximum):
    assert maximum > 0
    output = []
    for token in tokens:
        # Toy counts EOS as a generated token; not a particular backend contract.
        output.append(token)
        if token == '<EOS>':
            return output, 'eos'
        if len(output) == maximum:
            return output, 'length'
    return output, 'source_exhausted'  # not an automatic complete answer


def evidence_select(query, documents):
    # Explicit keyword matching is only a negative-case teaching device.
    return [d for d in documents if query in d]


def main():
    assert cost(1000, 200) == 550
    assert cost(500, 200, 30) == 480
    assert cost(500, 100, 30) == 280
    assert cost(500, 200, 150) == 600
    assert isclose(route_cost(.7), 2.3)
    assert isclose(fallback_cost(.4), 3.1)
    assert fallback_cost(1) > 5  # full fallback pays both models plus router
    stream = ['complete', '<EOS>', 'unused']
    a = generate(stream, 5)
    b = generate(stream, 20)
    assert a == b and a[1] == 'eos'
    cut = generate(['{', '"answer":', '"yes"', '}', '<EOS>'], 3)
    assert cut[1] == 'length' and '}' not in cut[0]
    assert generate(['partial'], 10)[1] == 'source_exhausted'
    docs = ['Service A supports refund.', 'Service B does not support refund.', 'Unrelated weather.']
    selected = evidence_select('Service B', docs)
    assert selected == [docs[1]]
    assert 'not' in selected[0]
    bad_compression = selected[0].replace('not ', '')
    assert bad_compression != selected[0] and 'not' not in bad_compression
    bad_truncation = selected[0][:10]
    assert 'not' not in bad_truncation and 'refund' not in bad_truncation
    print('PASS: budget arithmetic; lower input can lose when preparation is too expensive')
    print('PASS: routing 2.3 versus fallback 3.1 under explicit cost assumptions')
    print('PASS: EOS versus length truncation; raising a cap after EOS adds no steps')
    print('PASS: context-selection example and lost-negation/truncation negative cases')
    print('No retrieval model, semantic compressor, learned router or device timing')


if __name__ == '__main__':
    main()
