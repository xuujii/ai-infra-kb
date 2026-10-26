"""Exact-result identity, TTL/completion and semantic candidate gates; no Redis."""
from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import json


def identity(request):
    fields = ['tenant', 'scope', 'messages', 'model', 'adapter', 'generation',
              'knowledge', 'tool_dependency', 'policy']
    canonical = {k: request[k] for k in fields}
    # Dict property order is normalized. Ordered message lists are preserved.
    return sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class ResultCache:
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.entries = OrderedDict()

    def put(self, request, result, now, ttl, complete=True):
        if not complete or ttl <= 0 or request.get('fresh_sample', False):
            return False
        key = identity(request)
        self.entries[key] = dict(result=deepcopy(result), expires=now+ttl)
        self.entries.move_to_end(key)
        while len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return True

    def get(self, request, now):
        if request.get('fresh_sample', False):
            return None
        key = identity(request)
        entry = self.entries.get(key)
        if entry is None:
            return None
        if now >= entry['expires']:
            del self.entries[key]
            return None
        self.entries.move_to_end(key)
        return deepcopy(entry['result'])


def semantic_gate(candidate, request, similarity, threshold, now):
    for field in ['tenant', 'scope', 'model', 'knowledge', 'policy', 'intent']:
        if candidate[field] != request[field]:
            return False
    return candidate['complete'] and now < candidate['expires'] and similarity >= threshold


def request():
    return dict(tenant='A', scope='staff', messages=[{'role':'system', 'content':'Answer with evidence.'},
                {'role':'user', 'content':'What is the refund policy?'}], model='model-v1', adapter='none',
                generation={'temperature':0, 'format':'text'}, knowledge='kb-v1',
                tool_dependency='static', policy='cache-v1', fresh_sample=False, intent='refund')


def main():
    r, cache = request(), ResultCache()
    answer = {'text':'v1 answer'}
    assert cache.put(r, answer, 0, 10)
    answer['text'] = 'mutated outside cache'
    assert cache.get(r, 1) == {'text':'v1 answer'}
    for field, value in [('tenant', 'B'), ('scope', 'public'), ('model', 'model-v2'),
                         ('adapter', 'adapter-v2'), ('knowledge', 'kb-v2'), ('policy', 'cache-v2'),
                         ('tool_dependency', 'tool-result-v2'), ('generation', {'temperature':1})]:
        changed = deepcopy(r)
        changed[field] = value
        assert cache.get(changed, 1) is None
    swapped = deepcopy(r)
    swapped['messages'].reverse()
    assert identity(swapped) != identity(r)
    reserialized = dict(reversed(list(r.items())))
    assert identity(reserialized) == identity(r)
    returned = cache.get(r, 2)
    returned['text'] = 'client mutation'
    assert cache.get(r, 3) == {'text':'v1 answer'}
    fresh = deepcopy(r)
    fresh['fresh_sample'] = True
    assert cache.get(fresh, 3) is None and not cache.put(fresh, 'sample', 3, 10)
    assert not cache.put(r, 'half-stream', 3, 10, complete=False)
    assert cache.get(r, 9) == {'text':'v1 answer'} and cache.get(r, 10) is None
    candidate = {k:r[k] for k in ['tenant', 'scope', 'model', 'knowledge', 'policy', 'intent']}
    candidate.update(expires=20, complete=True)
    assert semantic_gate(candidate, r, .96, .95, 10)
    assert not semantic_gate(candidate, r, .96, .99, 10)
    for field, value in [('tenant', 'B'), ('knowledge', 'kb-v2'), ('intent', 'cancel')]:
        changed = deepcopy(r)
        changed[field] = value
        assert not semantic_gate(candidate, changed, .999, .95, 10)
    assert not semantic_gate(candidate, r, 1, .95, 20)
    assert not semantic_gate({**candidate, 'complete':False}, r, 1, .95, 10)
    # A v1 request finishes after the current knowledge is v2: keep its original key.
    started = deepcopy(r)
    current = deepcopy(r)
    current['knowledge'] = 'kb-v2'
    assert cache.put(started, 'late v1 result', 20, 10)
    assert cache.get(current, 21) is None
    assert cache.get(started, 21) == 'late v1 result'
    third = deepcopy(r)
    third['model'] = 'model-v3'
    cache.put(current, 'v2', 20, 10)
    cache.put(third, 'v3', 20, 10)
    assert len(cache.entries) == 2 and cache.get(started, 21) is None
    assert 5+(1-.6)*1000 == 405
    assert 5+(1-.001)*1000 == 1004
    print('PASS: full ordered identity, dependency isolation, fresh-sample bypass, immutable result copies')
    print('PASS: TTL boundary, incomplete-result rejection, LRU bounded capacity')
    print('PASS: high similarity does not override intent, tenant, version or expiry')
    print('PASS: late old-version write cannot become a new-version cache entry')
    print('No real embeddings, production permission service, Redis or measured speed')


if __name__ == '__main__':
    main()
