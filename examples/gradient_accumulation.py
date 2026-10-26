"""Same-target gradient accumulation with unequal microbatches; standard library."""
from math import isclose


def mean_gradient(samples,weight):
    # L = mean((w*x-y)^2); dL/dw = mean(2*x*(w*x-y)).
    return sum(2*x*(weight*x-y) for x,y in samples)/len(samples)


if __name__ == '__main__':
    samples=[(x,2*x) for x in range(1,6)]
    batches=[samples[:2],samples[2:]]
    weight,lr=0.,0.01
    full=mean_gradient(samples,weight)
    weighted=sum(len(b)/len(samples)*mean_gradient(b,weight) for b in batches)
    naive=sum(mean_gradient(b,weight) for b in batches)/len(batches)
    assert isclose(full,weighted) and not isclose(full,naive)
    sequential=weight
    for batch in batches:
        sequential-=lr*mean_gradient(batch,sequential)
    one_step=weight-lr*full
    assert not isclose(sequential,one_step)
    # Ordinary two-rank DDP averages gradients: local loss-sum multiplier D/N
    # yields the global mean, including uneven valid-item counts.
    ranks,D=batches,2
    local_scaled=[D*len(rank)/len(samples)*mean_gradient(rank,weight) for rank in ranks]
    ddp_mean=sum(local_scaled)/D
    assert isclose(ddp_mean,full)
    assert isclose((2*1+6*3)/8,2.5)
    print('full batch gradient:',full,'weighted accumulation:',weighted,'incorrect unweighted mean:',naive)
    print('one update:',one_step,'update after each microbatch:',sequential)
    print('D/N local contributions before DDP mean:',local_scaled,'global mean:',ddp_mean)
    print('Gradient target checks passed. No autograd, actual DDP or GPU/NPU benchmark.')
