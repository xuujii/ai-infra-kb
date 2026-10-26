"""Dependency-checked ideal GPipe/1F1B schedules, not a distributed trainer.

Each F/B takes one time unit, no transfer/optimizer/startup cost.
Counts completed forward activations waiting for backward to finish;
excludes transient activation/workspace memory inside each operation.
"""


def schedule(stages,microbatches,kind):
    assert stages>0 and microbatches>0 and kind in ('gpipe','1f1b')
    orders=[]
    for stage in range(stages):
        if kind=='gpipe':
            order=[('F',i) for i in range(microbatches)]+[('B',i) for i in reversed(range(microbatches))]
        else:
            warm=min(microbatches,stages-stage-1)
            order=[('F',i) for i in range(warm)]
            for i in range(microbatches-warm):
                order.extend([('F',warm+i),('B',i)])
            order.extend(('B',i) for i in range(microbatches-warm,microbatches))
        orders.append([(stage,*task) for task in order])
    dependencies={}
    for stage,order in enumerate(orders):
        for i,key in enumerate(order):
            _,op,batch=key
            deps=[order[i-1]] if i else []
            if op=='F' and stage>0:
                deps.append((stage-1,'F',batch))
            if op=='B':
                deps.append((stage,'F',batch))
                if stage<stages-1:
                    deps.append((stage+1,'B',batch))
            dependencies[key]=deps
    done,visiting={},set()
    def resolve(key):
        if key in done:return done[key]
        assert key not in visiting, 'cycle / impossible schedule'
        visiting.add(key)
        start=max((resolve(d)[1] for d in dependencies[key]),default=0)
        done[key]=(start,start+1)
        visiting.remove(key)
        return done[key]
    for order in orders:
        for key in order:resolve(key)
    total=max(end for _,end in done.values())
    peaks=[]
    for order in orders:
        events=[]
        for i,key in enumerate(order):
            start,end=done[key]
            if i:assert start>=done[order[i-1]][1]
            assert all(start>=done[d][1] for d in dependencies[key])
            events.append((end,1 if key[1]=='F' else -1))
        active,peak=0,0
        for _,change in sorted(events):
            active+=change
            assert active>=0
            peak=max(peak,active)
        assert active==0
        peaks.append(peak)
    return orders,done,total,peaks


if __name__=='__main__':
    for stages in (1,2,4,8):
        for microbatches in (1,2,4,8,16):
            for kind in ('gpipe','1f1b'):
                _,_,total,peaks=schedule(stages,microbatches,kind)
                assert total==2*(microbatches+stages-1)
                if kind=='gpipe':assert peaks[0]==microbatches
                else:assert peaks[0]==min(stages,microbatches)
    for kind in ('gpipe','1f1b'):
        orders,times,total,peaks=schedule(2,4,kind)
        assert total==10 and peaks[0]==(4 if kind=='gpipe' else 2)
        print(kind,'total:',total,'saved-activation peaks:',peaks)
        for stage,order in enumerate(orders):
            slots=['.']*total
            for key in order:
                slots[times[key][0]]=key[1]+str(key[2]+1)
            print('stage',stage,':',' '.join(slots))
    print('Dependency and occupancy checks passed for 40 configurations. Not a hardware speed or memory benchmark.')
