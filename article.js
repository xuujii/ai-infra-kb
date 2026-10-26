(()=>{
 function number(el,name){const input=el.querySelector(`[name="${name}"]`);const n=Number(input.value);return Number.isFinite(n)&&n>0?Math.min(100,n):1;}
 function draw(el){
  const out=el.querySelector('.demo-result');
  if(el.dataset.demo==='service-priority'){
   const high=el.querySelector('[name="service-policy"]').value==='priority',a=Number(el.querySelector('[name="service-long"]').value),jobs=high?[['B',2],['C',2],['A',a]]:[['A',a],['B',2],['C',2]];let time=0,totalWait=0;
   const rows=jobs.map(([name,duration])=>{const start=time;time+=duration;totalWait+=start;return `<tr><td>${name}</td><td ${name==='B'?`data-service-b-finish="${time}"`:''}>${start}→${time} ms</td><td>${start} ms</td></tr>`;});
   el.querySelector('.coordination-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="非抢占任务执行与等待"><table><thead><tr><th>执行顺序</th><th>执行区间</th><th>等待</th></tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
   out.dataset.serviceWait=String(totalWait/3);out.dataset.serviceFinal=String(time);out.textContent=`平均等待${(totalWait/3).toFixed(2)} ms，全部完成${time} ms。${high?'B/C更早完成，A等待变长。':'A先执行，B/C排在它之后。'}两种顺序的总工作量相同。`;return;
  }
  if(el.dataset.demo==='time-to-quality'){
   const key=el.querySelector('[name="quality-run"]').value,interval=Number(el.querySelector('[name="quality-interval"]').value),plans={baseline:[2000,1,0],kernel:[2000,.6,0],recipe:[4000,.8,0],data:[1200,.9,300]},[need,step,prep]=plans[key],checks=Math.ceil(need/interval),confirmed=checks*interval,total=prep+confirmed*step+checks*20,baseline=2000+Math.ceil(2000/interval)*20;
   el.querySelector('.coordination-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="合成质量曲线达标账本"><table><thead><tr><th>观察项</th><th>教学数量</th></tr></thead><tbody><tr><td>每步训练</td><td>${step} s</td></tr><tr><td>数据准备</td><td>${prep} s</td></tr><tr><td>假设达标步</td><td>${need}</td></tr><tr><td>首次确认步</td><td data-quality-confirmed="${confirmed}">${confirmed}</td></tr><tr><td>评估累计</td><td>${checks*20} s</td></tr><tr><td>当前达标总时间</td><td data-quality-total="${total}">${total} s</td></tr><tr><td>A同间隔总时间</td><td>${baseline} s</td></tr></tbody></table></div>`;
   out.textContent=`在第${confirmed}步确认，计准备与评估共${total} s；${confirmed>need?`门槛在第${need}步已达到，但未及时评估。`:'本例评估恰逢门槛。'}${total>baseline?'单步或数据变化没有让本例更早确认达标。':'仍须用真实质量曲线验证方案。'}`;return;
  }
  if(el.dataset.demo==='rl-stage-pipeline'){
   const n=Number(el.querySelector('[name="rl-batches"]').value),r=Number(el.querySelector('[name="rl-rollout"]').value),t=Number(el.querySelector('[name="rl-training"]').value),durations=[r,20,t],available=[0,0,0],lanes=[[],[],[]];
   for(let batch=1;batch<=n;batch++){let previous=0;for(let stage=0;stage<3;stage++){const start=Math.max(available[stage],previous),end=start+durations[stage];lanes[stage].push([start,end,batch]);available[stage]=previous=end;}}
   const total=available[2],serial=n*(r+20+t),names=['生成','评分','训练'],classes=['ckpt-compute','ckpt-stage','ckpt-write'];
   el.querySelector('.rl-stage-chart').innerHTML=`<div role="img" aria-label="生成、评分、训练按批次流水；展开下方读取具体时刻">${lanes.map((segments,i)=>`<div class="ckpt-lane"><span>${names[i]}</span><div>${segments.map(([a,b,k])=>`<i class="${classes[i]}" style="left:${a/total*100}%;width:${(b-a)/total*100}%" title="批${k}：${a}–${b} ms"><span class="sr-only">批${k}：${a}–${b} ms</span></i>`).join('')}</div></div>`).join('')}<p class="ckpt-scale">0 ms <span>${total} ms</span></p></div><details><summary>逐批依赖时刻</summary><p>${Array.from({length:n},(_,i)=>`批${i+1}：${lanes.map((s,j)=>`${names[j]} ${s[i][0]}–${s[i][1]}`).join('，')} ms`).join('；')}</p></details>`;
   el.querySelector('.coordination-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="外层排程总时间"><table><thead><tr><th>教学排程</th><th>全部完成</th></tr></thead><tbody><tr><td>逐批串行</td><td data-rl-serial="${serial}">${serial} ms</td></tr><tr><td>三资源流水</td><td data-rl-pipeline="${total}">${total} ms</td></tr></tbody></table></div>`;
   out.textContent=`本排程固定行为版本，流水完成${total} ms；批内依赖和每个资源内的顺序都保留。它展示重叠机会，不证明等质量RL提速。`;return;
  }
  if(el.dataset.demo==='pruning-shape'){
   const keep=Number(el.querySelector('[name="prune-keep"]').value),compact=el.querySelector('[name="prune-mode"]').value==='compact',h=compact?keep:8,params=8*h;
   el.querySelector('.workload-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="剪枝结构与dense乘法"><table><thead><tr><th>观察项</th><th>原模型</th><th>当前表示</th></tr></thead><tbody><tr><td>W1 / W2</td><td>4×8 / 8×4</td><td>4×${h} / ${h}×4</td></tr><tr><td>矩阵参数槽</td><td>64</td><td data-prune-params="${params}">${params}</td></tr><tr><td>dense乘法/token</td><td>64</td><td data-prune-multiplies="${params}">${params}</td></tr><tr><td>保留路径乘法</td><td>64</td><td>${8*keep}</td></tr></tbody></table></div>`;
   out.textContent=compact?`保留${keep}个单元并配对改写两矩阵，dense乘法按shape计${params}次。质量需另与未剪模型评测。`:`保留${keep}个单元，但仍是原shape普通dense计算，按shape计64次乘法；mask不自动启用稀疏执行。`;return;
  }
  if(el.dataset.demo==='request-budget'){
   const n=Number(el.querySelector('[name="budget-input"]').value),g=Number(el.querySelector('[name="budget-output"]').value),c=Number(el.querySelector('[name="budget-prep"]').value),linear=.05*n,attention=.0001*n*n,decode=2*g,total=c+linear+attention+decode,saving=550-total;
   el.querySelector('.workload-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="任务工作量教学成本"><table><thead><tr><th>教学分项</th><th>ms</th></tr></thead><tbody><tr><td>策略准备</td><td>${c}</td></tr><tr><td>输入线性项</td><td>${linear.toFixed(2)}</td></tr><tr><td>输入平方项</td><td>${attention.toFixed(2)}</td></tr><tr><td>生成项</td><td>${decode}</td></tr><tr><td>当前总计</td><td data-budget-total="${total}">${total.toFixed(2)}</td></tr><tr><td>基线总计</td><td>550.00</td></tr></tbody></table></div>`;
   out.textContent=saving>=0?`教学总时间减少${saving.toFixed(2)} ms；仍需确认相同任务质量与完成率。`:`教学总时间增加${(-saving).toFixed(2)} ms；减少输入未能抵消准备成本。`;return;
  }
  if(el.dataset.demo==='result-cache-gate'){
   const threshold=Number(el.querySelector('[name="cache-threshold"]').value),scenario=el.querySelector('[name="cache-case"]').value,checks=[['相似度通过',.96>=threshold],['访问范围一致',scenario!=='tenant'],['知识版本一致',scenario!=='version'],['业务意图相同',scenario!=='intent'],['仍在TTL内',scenario!=='expired'],['结果完整',scenario!=='partial']],hit=checks.every(([,ok])=>ok);
   el.querySelector('.workload-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="结果缓存候选有效性"><table><thead><tr><th>复用条件</th><th>本例检查</th></tr></thead><tbody>${checks.map(([name,ok])=>`<tr><td>${name}</td><td>${ok?'通过':'不通过'}</td></tr>`).join('')}</tbody></table></div>`;
   out.dataset.cacheHit=String(hit);out.textContent=hit?'本教学合同全部通过，可以返回已缓存结果；没有执行新一轮Decode。':'拒绝复用候选，走正常生成路径。高相似度不能覆盖版本、访问、时效或完整性条件。';return;
  }
  if(el.dataset.demo==='optimizer-traffic'){
   const n=Number(el.querySelector('[name="opt-elements"]').value),t=Number(el.querySelector('[name="opt-tensors"]').value),separate=40*n,fused=28*n;
   el.querySelector('.lifecycle-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="FP32更新逻辑访问账本"><table><thead><tr><th>教学路径</th><th>逻辑MiB</th><th>假设调用</th></tr></thead><tbody><tr><td>三个分离循环</td><td data-opt-separate="${separate}">${(separate/2**20).toFixed(3)}</td><td data-opt-launches="${3*t}">${3*t}</td></tr><tr><td>整组融合循环</td><td data-opt-fused="${fused}">${(fused/2**20).toFixed(3)}</td><td>1</td></tr></tbody></table></div>`;
   out.textContent='本账本逻辑访问减少30%；增加Tensor数只改变假设调用数，不改变同样元素总量的字节。这不是端到端加速比。';return;
  }
  if(el.dataset.demo==='checkpoint-timeline'){
   const interval=Number(el.querySelector('[name="ckpt-interval"]').value),write=Number(el.querySelector('[name="ckpt-write"]').value),compute=[],stages=[],writes=[];let time=0,writeEnd=0,wait=0;
   for(let i=1;i<=4;i++){compute.push([time,time+10,`step ${i}`]);time+=10;if(i%interval===0){const start=Math.max(time,writeEnd);wait+=start-time;stages.push([start,start+2,`快照${i}`]);time=start+2;writeEnd=time+write;writes.push([time,writeEnd,`写入${i}`]);}}
   const final=Math.max(time,writeEnd),sync=40+stages.length*(2+write),row=(name,segments,cls)=>`<div class="ckpt-lane"><span>${name}</span><div>${segments.map(([a,b,label])=>`<i class="${cls}" style="left:${a/final*100}%;width:${(b-a)/final*100}%" title="${label}：${a}–${b} ms"><span class="sr-only">${label}：${a}–${b} ms</span></i>`).join('')}</div></div>`;
   el.querySelector('.checkpoint-chart').innerHTML=`<div role="img" aria-label="训练、快照复制和后台写入时间线，详细时刻见下方">${row('训练',compute,'ckpt-compute')}${row('复制',stages,'ckpt-stage')}${row('写入',writes,'ckpt-write')}<p class="ckpt-scale">0 ms <span>${final} ms</span></p></div><details><summary>各快照的确切时刻</summary><p>${stages.map(([a,b],i)=>`快照${i+1}复制 ${a}–${b} ms，写入 ${writes[i][0]}–${writes[i][1]} ms`).join('；')}</p></details>`;
   el.querySelector('.lifecycle-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="检查点完成与等待"><table><thead><tr><th>观察点</th><th>ms</th></tr></thead><tbody><tr><td>同步全部完成</td><td>${sync}</td></tr><tr><td>异步训练结束</td><td data-ckpt-training="${time}">${time}</td></tr><tr><td>异步最后写完</td><td data-ckpt-final="${final}">${final}</td></tr><tr><td>等缓冲累计</td><td data-ckpt-wait="${wait}">${wait}</td></tr></tbody></table></div>`;
   out.textContent=`训练在${time} ms结束，最后写入在${final} ms结束。${wait?'后台慢，下一次复制等待空闲缓冲。':'前一次写入在下次复制前已完成。'}退出前仍需确认最后提交。`;return;
  }
  if(el.dataset.demo==='startup-readiness'){
   const hit=el.querySelector('[name="startup-cache"]').value==='hit',warm=Number(el.querySelector('[name="startup-warm"]').value),bucket=Number(el.querySelector('[name="startup-bucket"]').value),compile=hit?.5:8,ready=6+compile+.2*warm,covered=bucket<warm,first=covered?.05:.45;
   el.querySelector('.lifecycle-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="启动与首请求时间"><table><thead><tr><th>阶段或观察点</th><th>秒</th></tr></thead><tbody><tr><td>读取 / 安装</td><td>6.00</td></tr><tr><td>${hit?'载入兼容产物':'编译'}</td><td>${compile.toFixed(2)}</td></tr><tr><td>运行时预热</td><td>${(.2*warm).toFixed(2)}</td></tr><tr><td>启动到ready</td><td data-startup-ready="${ready}">${ready.toFixed(2)}</td></tr><tr><td>首请求</td><td data-startup-first="${first}">${first.toFixed(2)}</td></tr><tr><td>稳态执行</td><td>0.05</td></tr></tbody></table></div>`;
   out.textContent=`桶${bucket}${covered?'已覆盖，首请求只执行稳态工作。':'未预热，首请求还需0.4秒懒初始化。'}编译缓存命中省准备时间，不自动改变稳态执行速度。`;return;
  }
  if(el.dataset.demo==='sampling-policy'){
   const mask=el.querySelector('[name="sample-mask"]').value,k=Number(el.querySelector('[name="sample-k"]').value),threshold=Number(el.querySelector('[name="sample-p"]').value),u=Number(el.querySelector('[name="sample-u"]').value),original=[.4,.3,.2,.1],names=['A','B','C','D'],legal=original.map((_,i)=>mask==='all'||mask==='cd'&&i>=2),mass=original.reduce((a,p,i)=>a+(legal[i]?p:0),0),masked=original.map((p,i)=>mass&&legal[i]?p/mass:0),candidates=names.map((_,i)=>i).filter(i=>masked[i]>0).sort((a,b)=>masked[b]-masked[a]||a-b).slice(0,k),kmass=candidates.reduce((a,i)=>a+masked[i],0),kept=[];let cumulative=0;
   for(const i of candidates){kept.push(i);cumulative+=masked[i]/kmass;if(cumulative+1e-12>=threshold)break;}
   const remaining=kept.reduce((a,i)=>a+masked[i],0),final=masked.map((p,i)=>kept.includes(i)?p/remaining:0);let cdf=0,selected='';for(let i=0;i<4;i++){cdf+=final[i];if(u<cdf){selected=names[i];break;}}
   el.querySelector('.adaptation-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="过滤与最终采样概率"><table><thead><tr><th>token</th><th>原概率</th><th>约束后</th><th>最终</th></tr></thead><tbody>${names.map((name,i)=>`<tr><td>${name}</td><td>${original[i].toFixed(3)}</td><td>${masked[i].toFixed(3)}</td><td data-sample-prob="${final[i]}">${final[i].toFixed(3)}</td></tr>`).join('')}</tbody></table></div>`;
   out.dataset.sampleToken=selected;out.dataset.sampleSet=kept.map(i=>names[i]).join(',');
   out.textContent=mass?`剩余候选${kept.map(i=>names[i]).join('/')}；u=${u}落在${selected}的CDF区间，选出${selected}。改变过滤参数会改变分布，不是执行提速。`:'没有合法候选：停止本例采样并报告空集合，不擅自选择默认token。';return;
  }
  if(el.dataset.demo==='lora-budget'){
   const rank=Number(el.querySelector('[name="lora-rank"]').value),bytes=Number(el.querySelector('[name="lora-base-byte"]').value),count=rank*8192,base=4096**2*bytes/2**20,states=count*12/2**20,total=base+states,ratio=4096**2/count;
   el.querySelector('.adaptation-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="单矩阵LoRA参数与状态容量"><table><thead><tr><th>对象</th><th>参数量</th><th>MiB</th></tr></thead><tbody><tr><td>全参训练参照</td><td>16777216</td><td>192</td></tr><tr><td>冻结基座</td><td>16777216</td><td>${base}</td></tr><tr><td>LoRA训练状态</td><td data-lora-trainable="${count}">${count}</td><td>${states}</td></tr><tr><td>后两项合计</td><td>不含其他对象</td><td data-lora-total="${total}">${total}</td></tr></tbody></table></div>`;
   out.textContent=`可训练参数为该全矩阵的1/${ratio}；基座+适配训练状态${total} MiB${bytes===.5?'，低位元数据另计':''}。前向和所需输入梯度仍经过基座；不是${ratio}倍step加速。`;return;
  }
  if(el.dataset.demo==='multilora-rows'){
   const rank=Number(el.querySelector('[name="multi-rank"]').value),wrong=el.querySelector('[name="multi-restore"]').value==='wrong',identity=['P(A)','Q(B)','R(A)','S(无)'],packed=[{request:'P',adapter:'A',row:0},{request:'R',adapter:'A',row:2},{request:'Q',adapter:'B',row:1}],valid=32+16*rank,padded=2*4*Math.max(1,rank)*8;
   el.querySelector('.adaptation-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="分组行与原始请求映射"><table><thead><tr><th>分组输入</th><th>应回写行</th><th>实际接收行</th></tr></thead><tbody>${packed.map((r,i)=>`<tr><td>${r.request}(${r.adapter})</td><td>${r.row}</td><td class="${wrong&&i!==r.row?'wrong-row':''}">${identity[wrong?i:r.row]}</td></tr>`).join('')}</tbody></table></div>`;
   out.dataset.multiValid=valid;out.dataset.multiPadded=padded;out.dataset.multiWrong=wrong;
   out.textContent=`有效低秩分支${valid} FLOP，统一max-rank槽位参照${padded} FLOP。${wrong?'错误写回把R(A)增量加给Q(B)，Q(B)增量加给R(A)。':'保留原行索引，分组后的增量仍加给各自请求。'}不是硬件加速比。`;return;
  }
  if(el.dataset.demo==='kv-architecture'){
   const length=Number(el.querySelector('[name="arch-length"]').value),bytes=Number(el.querySelector('[name="arch-byte"]').value),kv=Number(el.querySelector('[name="arch-kv"]').value),common=length*32*bytes/2**20,rows=[['MHA',32,common*2*32*128],['GQA',8,common*2*8*128],['MQA',1,common*2*128],['MLA',0,common*(512+64)]];
   el.querySelector('.structure-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="各结构原始缓存容量"><table><thead><tr><th>结构</th><th>保存参数</th><th>MiB</th></tr></thead><tbody>${rows.map(([name,heads,mib])=>`<tr class="${heads===kv?'selected-architecture':''}"><td>${name}${heads===kv?' ←':''}</td><td>${heads?heads+'组K/V':'512+64维'}</td><td data-arch="${name}" data-arch-mib="${mib}">${mib}</td></tr>`).join('')}</tbody></table></div>`;
   const group=32/kv;el.querySelector('.kv-head-map').innerHTML=Array.from({length:32},(_,h)=>`<span data-kv-head="${Math.floor(h/group)}">Q${h} → KV${Math.floor(h/group)}</span>`).join('');
   out.textContent=`选中${kv}个KV头：每组${group}个查询头共享，缓存${common*2*kv*128} MiB。查询头仍为32个；容量减少不是同倍率速度保证。`;return;
  }
  if(el.dataset.demo==='sparse-window'){
   const w=Number(el.querySelector('[name="window-size"]').value),tile=Number(el.querySelector('[name="window-tile"]').value),allowed=(i,j)=>j<=i&&j>=i-w+1,blocks=new Set();let valid=0;
   for(let i=0;i<8;i++)for(let j=0;j<8;j++)if(allowed(i,j)){valid++;blocks.add(Math.floor(i/tile)+','+Math.floor(j/tile));}
   const cover=blocks.size*tile*tile;
   el.querySelector('.sparse-window-grid').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="窗口可见性和分块覆盖"><table><thead><tr><th>Q/K</th>${Array.from({length:8},(_,j)=>`<th>${j}</th>`).join('')}</tr></thead><tbody>${Array.from({length:8},(_,i)=>`<tr><th>${i}</th>${Array.from({length:8},(_,j)=>{const keep=allowed(i,j),covered=blocks.has(Math.floor(i/tile)+','+Math.floor(j/tile));return `<td data-window-visible="${keep}" class="${keep?'window-valid':covered?'window-edge':'window-skipped'}" title="Q${i}/K${j}：${keep?'可见':covered?'块内mask':'整块跳过'}">${keep?'●':covered?'·':'—'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
   out.dataset.windowValid=valid;out.dataset.windowCover=cover;
   out.textContent=`有效${valid}对 / 完整因果36对；${blocks.size}个块覆盖${cover}个坐标，含${cover-valid}个边界余量。窗口改变可见性，tile改变执行组织。`;return;
  }
  if(el.dataset.demo==='loss-workspace'){
   const c=Number(el.querySelector('[name="loss-rows"]').value),b=Number(el.querySelector('[name="loss-vocab"]').value),full=4096*128000*2/2**20,row=c*128000*2/2**20,dual=c*b*2/2**20,tiles=Math.ceil(4096/c)*Math.ceil(128000/b),fmt=n=>Number(n.toFixed(4));
   el.querySelector('.structure-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="完整和分块logits临时容量"><table><thead><tr><th>方案</th><th>临时表shape</th><th>MiB</th></tr></thead><tbody><tr><td>完整</td><td>4096×128000</td><td>1000</td></tr><tr><td>仅行分块</td><td>${c}×128000</td><td>${fmt(row)}</td></tr><tr><td>行列分块</td><td>${c}×${b}</td><td data-loss-mib="${dual}">${fmt(dual)}</td></tr></tbody></table></div>`;
   out.dataset.lossTiles=tiles;
   out.textContent=`单块临时表1000→${fmt(dual)} MiB；前向覆盖全表需${tiles}块。仍遍历完整词表，Loss与梯度定义不变；保存统计、反向重算和更多小任务也有代价。`;return;
  }
  if(el.dataset.demo==='gemm-tiling'){
   const t=Number(el.querySelector('[name="gemm-tile"]').value),blocks=(4/t)**2,reads=128/t,workspace=12*t*t,colors=['#e4f0e8','#dce8f6','#ece5f3','#f3e8d9'];
   el.querySelector('.gemm-output-grid').innerHTML=Array.from({length:16},(_,idx)=>{const i=Math.floor(idx/4),j=idx%4,group=Math.floor(i/t)*(4/t)+Math.floor(j/t);return `<span style="background:${colors[group%colors.length]};border-top-width:${i%t===0?3:1}px;border-left-width:${j%t===0?3:1}px">Y${i}${j}</span>`;}).join('');
   el.querySelector('.kernel-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="分块读取与工作区"><table><tbody><tr><th>输出块数</th><td>${blocks}</td></tr><tr><th>输入元素读取</th><td data-gemm-reads="${reads}">${reads} 次</td></tr><tr><th>输出写入</th><td>16 个元素</td></tr><tr><th>单块工作区</th><td>${workspace} B</td></tr></tbody></table></div>`;
   out.textContent=`tile=${t}，输入读取128→${reads}次；64次乘法和64次加法保持不变。工作区随tile增大，输出块并行数减少。`;return;
  }
  if(el.dataset.demo==='splitkv-merge'){
   const count=Number(el.querySelector('[name="kv-splits"]').value),mode=el.querySelector('[name="kv-merge"]').value,scores=[0,Math.log(2),Math.log(3),Math.log(4)],values=[1,2,4,8],states=[];
   for(let part=0;part<count;part++){const start=part*4/count,end=(part+1)*4/count,ss=scores.slice(start,end),vv=values.slice(start,end),m=Math.max(...ss),weights=ss.map(s=>Math.exp(s-m)),ell=weights.reduce((a,b)=>a+b,0),u=weights.reduce((a,w,i)=>a+w*vv[i],0);states.push({start,end,m,ell,u,local:u/ell});}
   const m=Math.max(...states.map(s=>s.m)),mass=states.map(s=>Math.exp(s.m-m)*s.ell),total=mass.reduce((a,b)=>a+b,0),correct=states.reduce((a,s,i)=>a+mass[i]/total*s.local,0),actual=mode==='mean'?states.reduce((a,s)=>a+s.local,0)/count:correct,fmt=n=>n.toFixed(6),wrong=Math.abs(actual-4.9)>1e-9;
   el.querySelector('.kernel-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="各历史片段局部输出和全局权重"><table><thead><tr><th>片段位置</th><th>局部输出</th><th>全局质量比例</th></tr></thead><tbody>${states.map((s,i)=>`<tr><td>${s.start}–${s.end-1}</td><td>${fmt(s.local)}</td><td>${(mass[i]/total*100).toFixed(1)}%</td></tr>`).join('')}</tbody></table></div>`;
   out.dataset.splitOutput=actual;
   out.textContent=`完整输出4.900000，本次合并${fmt(actual)}。${wrong?`直接平均不等价，误差${fmt(Math.abs(actual-4.9))}。`:(count===1?'只有一个片段，无跨段合并。':'保留归一化统计，正确恢复全局权重。')}`;return;
  }
  if(el.dataset.demo==='grouped-rows'){
   const counts=el.querySelector('[name="moe-counts"]').value==='balanced'?[2,2,2,2]:[3,4,1,0],t=Number(el.querySelector('[name="moe-tile"]').value),capacity=Math.ceil(Math.max(...counts)/t)*t,covered=counts.map(n=>Math.ceil(n/t)*t),grouped=covered.reduce((a,b)=>a+b,0),uniform=capacity*4;
   el.querySelector('.kernel-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="各专家有效行与tile覆盖"><table><thead><tr><th>专家</th><th>有效调用</th><th>分组覆盖行</th></tr></thead><tbody>${counts.map((n,i)=>`<tr><td>E${i}</td><td>${n}</td><td>${covered[i]}</td></tr>`).join('')}</tbody></table></div>`;
   out.dataset.groupedRows=grouped;out.dataset.uniformRows=uniform;
   out.textContent=`8次有效调用；统一补齐${uniform}行，分组覆盖${grouped}行。${grouped<uniform?`少覆盖${uniform-grouped}行，但仍有${grouped-8}行边界余量。`:'两者覆盖行数相同，需再看启动与调度成本。'}这不是实测加速比。`;return;
  }
  if(el.dataset.demo==='collective-cost'){
   const ranks=Number(el.querySelector('[name="comm-ranks"]').value),bytes=Number(el.querySelector('[name="comm-size"]').value),alpha=Number(el.querySelector('[name="comm-alpha"]').value)/1000,payload=bytes/(25*2**30)*1000,rounds=2*(ranks-1),depth=2*Math.log2(ranks),ringLatency=rounds*alpha,ringBytes=2*(ranks-1)/ranks*payload,treeLatency=depth*alpha,treeBytes=depth*payload,ring=ringLatency+ringBytes,tree=treeLatency+treeBytes,fmt=n=>n.toFixed(4);
   el.querySelector('.comm-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="简化通信成本，可横向滚动"><table><thead><tr><th>模型</th><th>延迟项</th><th>字节项</th><th>合计 / ms</th></tr></thead><tbody><tr><td>Ring</td><td>${fmt(ringLatency)}</td><td>${fmt(ringBytes)}</td><td data-comm-ring="${ring}">${fmt(ring)}</td></tr><tr><td>教学整块树</td><td>${fmt(treeLatency)}</td><td>${fmt(treeBytes)}</td><td data-comm-tree="${tree}">${fmt(tree)}</td></tr></tbody></table></div>`;
   out.textContent=`Ring ${rounds}轮；教学整块树关键路径${depth}阶段。此模型下${ring<tree?'Ring合计更低':'教学整块树合计更低'}；实际库需用对应消息和拓扑测量。`;return;
  }
  if(el.dataset.demo==='pd-handoff'){
   const mib=Number(el.querySelector('[name="pd-size"]').value),bw=Number(el.querySelector('[name="pd-bandwidth"]').value),wait=Number(el.querySelector('[name="pd-interference"]').value),transfer=mib/1024/bw*1000,firstMixed=40+wait,secondMixed=firstMixed+4,secondSeparate=40+transfer+2+4,fmt=n=>Number(n.toFixed(3));
   el.querySelector('.comm-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="两种部署的首token与第二token时间"><table><thead><tr><th>时刻 / ms</th><th>混部</th><th>分离</th></tr></thead><tbody><tr><td>首token</td><td>${firstMixed}</td><td>40</td></tr><tr><td>第二token</td><td data-pd-mixed="${secondMixed}">${secondMixed}</td><td data-pd-separate="${secondSeparate}">${fmt(secondSeparate)}</td></tr><tr><td>首个生成间隔</td><td>4</td><td>${fmt(transfer+6)}</td></tr></tbody></table></div>`;
   out.textContent=`KV传输下界 ${fmt(transfer)} ms，加协调2 ms。${secondSeparate<secondMixed?'分离的第二token更早':secondSeparate===secondMixed?'第二token时刻相同':'分离的第二token更晚'}；首token后的交接停顿仍需观察。`;return;
  }
  if(el.dataset.demo==='expert-placement'){
   const hot=Number(el.querySelector('[name="ep-hot"]').value),layout=el.querySelector('[name="ep-layout"]').value,replicated=layout==='replicated';let loads,descriptions;
   if(replicated){loads=[hot/2+20,hot/2+20];descriptions=[`E0:${hot/2} + E1:20`,`E0′:${hot/2} + E2:10 + E3:10`];}
   else if(layout==='moved'){loads=[hot+10,30];descriptions=[`E0:${hot} + E2:10`,'E1:20 + E3:10'];}
   else{loads=[hot+20,20];descriptions=[`E0:${hot} + E1:20`,'E2:10 + E3:10'];}
   el.querySelector('.comm-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="各rank的专家调用与负载"><table><thead><tr><th>rank</th><th>专家调用</th><th>总量</th></tr></thead><tbody>${loads.map((load,rank)=>`<tr><td>r${rank}</td><td>${descriptions[rank]}</td><td data-ep-rank="${rank}" data-ep-load="${load}">${load}</td></tr>`).join('')}</tbody></table></div>`;
   out.textContent=`总调用 ${hot+40}次保持不变；最忙卡 ${Math.max(...loads)}次。${replicated?'物理副本4→5，新增256 MiB权重（未计暂存）。':'物理专家共4份，无新增权重副本。'}调用数降低不等于同比实测加速。`;return;
  }
  if(el.dataset.demo==='kv-tier-cost'){
   const mib=Number(el.querySelector('[name="tier-mib"]').value),bandwidth=Number(el.querySelector('[name="tier-bandwidth"]').value),recompute=Number(el.querySelector('[name="tier-recompute"]').value),transfer=mib/1024/bandwidth*1000,fmt=n=>Number(n.toFixed(3));
   el.querySelector('.memory-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="回迁与重算教学成本"><table><thead><tr><th>方案</th><th>本次代价</th></tr></thead><tbody><tr><td>主机命中后回迁</td><td data-tier-ms="${transfer}">${fmt(transfer)} ms 下界</td></tr><tr><td>淘汰后重新Prefill</td><td>${recompute} ms 自设耗时</td></tr></tbody></table></div>`;
   out.textContent=`${mib} MiB ÷ ${bandwidth} GiB/s = ${fmt(transfer)} ms。${transfer<recompute?'此假设下回迁字节下界小于重算耗时；不保证实际回迁更快。':transfer===recompute?'两项教学成本相等，仍需比较额外开销。':'仅搬运下界已大于重算耗时，不能按“命中就划算”判断。'}`;return;
  }
  if(el.dataset.demo==='offload-deadline'){
   const lead=Number(el.querySelector('[name="offload-lead"]').value),transfer=Number(el.querySelector('[name="offload-transfer"]').value),deadline=12,start=deadline-lead,end=start+transfer,wait=Math.max(0,end-deadline),total=Math.max(deadline,end),percent=n=>n/total*100;
   el.querySelector('.offload-chart').innerHTML=`<div class="time-chart"><div class="time-row"><span>独立计算</span><div class="time-track"><span class="time-block" style="left:0;width:${percent(deadline)}%">0–12</span></div></div><div class="time-row"><span>H2D回迁</span><div class="time-track"><span class="time-block comm" data-offload-start="${start}" data-offload-end="${end}" style="left:${percent(start)}%;width:${percent(transfer)}%">${start}–${end}</span></div></div><small>0 → ${total} ms；反向原计划在12 ms开始。</small></div>`;
   out.textContent=`${start} ms开始回迁，${end} ms完成；反向等待 ${wait} ms，实际最早 ${Math.max(deadline,end)} ms开始。${wait?'回迁未能全部覆盖。':'本例按时到达，但提前驻留也占设备容量。'}`;return;
  }
  if(el.dataset.demo==='memory-lifetime'){
   const end=Number(el.querySelector('[name="memory-reader"]').value),safe=end<=3,total=safe?10:14;
   el.querySelector('.memory-demo-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="工作区生命周期与槽位"><table><thead><tr><th>对象</th><th>存活区间</th><th>安全槽位</th></tr></thead><tbody><tr><td>A · 4 MiB</td><td>[0,${end})</td><td>槽0</td></tr><tr><td>B · 6 MiB</td><td>[1,4)</td><td>槽1</td></tr><tr><td>C · 4 MiB</td><td>[3,5)</td><td>${safe?'槽0（复用）':'槽2（独立）'}</td></tr></tbody></table></div>`;
   out.textContent=`${safe?'A/C生命周期不重叠，可安全复用。':'A/C在[3,5)重叠，直接覆盖会破坏旧数据。'}保持本例排程的固定槽预留：${total} MiB。`;return;
  }
  if(el.dataset.demo==='packing-mask'){
   const labels=['A1','A2','A3','B1','B2'],docs=[0,0,0,1,1],isolated=el.querySelector('[name="pack-mask"]').value==='isolated',query=Number(el.querySelector('[name="pack-query"]').value);
   const visible=j=>j<=query&&(!isolated||docs[j]===docs[query]);
   el.querySelector('.packing-mask-grid').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="查询与Key可见性，可横向滚动"><table><thead><tr><th scope="col">查询 / Key</th>${labels.map(l=>`<th scope="col">${l}</th>`).join('')}</tr></thead><tbody>${labels.map((l,i)=>`<tr class="${i===query?'selected-query':''}"><th scope="row">${l}</th>${labels.map((_,j)=>{const allowed=j<=i&&(!isolated||docs[j]===docs[i]);return `<td data-query="${i}" data-key="${j}" data-visible="${allowed}" class="${allowed?'allowed':'blocked'}" aria-label="${l}读取${labels[j]}：${allowed?'允许':'屏蔽'}">${allowed?'●':'·'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
   const keys=labels.filter((_,j)=>visible(j)),leaks=labels.filter((_,j)=>visible(j)&&docs[j]!==docs[query]);
   out.textContent=`${labels[query]}可读：${keys.join('、')}。${leaks.length?`跨样本读取了${leaks.join('、')}，未保持独立样本语义。`:'没有跨样本读取。'}`;return;
  }
  if(el.dataset.demo==='input-pipeline'){
   const n=Number(el.querySelector('[name="input-batches"]').value),p=Number(el.querySelector('[name="input-prepare"]').value),h=Number(el.querySelector('[name="input-transfer"]')?.value||0),g=Number(el.querySelector('[name="input-compute"]').value),durations=[p,h,g],ends=[0,0,0],jobs=[];
   for(let batch=0;batch<n;batch++){let ready=0;const stages=durations.map((duration,stage)=>{const start=Math.max(ends[stage],ready),end=start+duration;ends[stage]=end;ready=end;return {start,end,duration};});jobs.push(stages);}
   const total=ends[2],serial=n*(p+h+g),labels=['CPU准备','输入复制','设备计算'];
   el.querySelector('.input-stage-chart').innerHTML=`<div class="time-chart input-flow-chart">${durations.map((duration,stage)=>duration?`<div class="time-row"><span>${labels[stage]}</span><div class="time-track">${jobs.map((times,batch)=>{const t=times[stage];return `<span class="time-block input-stage-${stage}" data-input-batch="${batch}" data-input-stage="${stage}" data-start="${t.start}" data-end="${t.end}" style="left:${t.start/total*100}%;width:${t.duration/total*100}%" title="批次${batch+1} ${labels[stage]}：${t.start}–${t.end} ms">${batch+1}</span>`;}).join('')}</div></div>`:'').join('')}<small>0 → ${total} ms；数字是批次编号，悬停查看起止时间。</small></div>`;
   el.querySelector('.input-stage-chart').innerHTML+=`<details class="advanced-reading"><summary>查看每批起止时间</summary><div class="article-table" tabindex="0" role="region" aria-label="每批输入阶段时间，可横向滚动"><table><thead><tr><th>批次</th><th>CPU准备</th><th>输入复制</th><th>设备计算</th></tr></thead><tbody>${jobs.map((times,batch)=>`<tr><td>${batch+1}</td>${times.map((t,stage)=>`<td>${stage===1&&h===0?'本例未计':`${t.start}–${t.end} ms`}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
   out.textContent=`串行 ${serial} ms → 理想流水 ${total} ms；首批完成 ${jobs[0][2].end} ms。流水没有减少每批的实际工作。`;return;
  }
  if(el.dataset.demo==='fusion-traffic'){
   const n=Number(el.querySelector('[name="fusion-elements"]').value),width=Number(el.querySelector('[name="fusion-bytes"]').value),save=el.querySelector('[name="fusion-save"]').value==='yes',unit=n*width/2**20,split=5*unit,fused=(save?4:3)*unit;
   const fmt=x=>Number(x.toFixed(6)).toString();
   el.querySelector('.fusion-paths').innerHTML=`<p><strong>分离执行</strong></p><div class="flow-strip"><span>读X、B</span><b>→</b><span>算A</span><b>→</b><span class="hbm-trip">写A，再读A</span><b>→</b><span>算ReLU，写Y</span></div><p><strong>融合执行</strong></p><div class="flow-strip"><span>读X、B</span><b>→</b><span class="onchip-step">片上计算A与ReLU</span><b>→</b><span>${save?'写A与Y':'只写Y'}</span></div>`;
   out.textContent=`逻辑读写：分离 ${fmt(split)} MiB → 融合 ${fmt(fused)} MiB，减少 ${fmt(split-fused)} MiB（${((1-fused/split)*100).toFixed(0)}%）。${save?'A仍需物化，但省掉融合内部的再次读取。':'A不需物化。'}`;return;
  }
  if(el.dataset.demo==='compile-amortization'){
   const cost=Number(el.querySelector('[name="compile-cost"]').value),variants=Number(el.querySelector('[name="compile-variants"]').value),calls=Number(el.querySelector('[name="compile-calls"]').value),prepare=cost*variants,eager=calls,steady=.6*calls,total=prepare+steady,delta=eager-total,threshold=Math.floor(prepare/.4)+1;
   el.querySelector('.compile-cost-table').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="编译总成本对照，可横向滚动"><table><thead><tr><th>路径</th><th>准备成本</th><th>执行成本</th><th>合计</th></tr></thead><tbody><tr><td>未编译</td><td>0 ms</td><td>${eager} ms</td><td>${eager} ms</td></tr><tr><td>编译</td><td>${prepare} ms</td><td>${steady} ms</td><td>${total} ms</td></tr></tbody></table></div>`;
   out.textContent=`${delta>0?`累计节省 ${delta} ms`:(delta<0?`累计多花 ${-delta} ms`:'累计成本相同')}；严格回本至少 ${threshold} 次执行。`;return;
  }
  if(el.dataset.demo==='graph-buffer'){
   const steps=[
    {title:'1 · 捕获时：变量和图都引用缓冲A',variable:'A',a:'[-1,2]',b:'尚未创建',output:'[-2,4]',text:'重放执行Y=2X，读取A的内容。'},
    {title:'2 · 就地改内容：新输入写进原地址A',variable:'A',a:'[3,4]',b:'尚未创建',output:'[6,8]',text:'地址未变，内容改变；重放对新输入重新计算。'},
    {title:'3 · 只改变量绑定：变量现在指向B',variable:'B',a:'[3,4]',b:'[9,10]',output:'[6,8]',text:'图仍引用A。把变量绑定到B，不会自动更换已捕获的地址。'},
    {title:'4 · 将B的数据复制到A，再重放',variable:'B',a:'[9,10]',b:'[9,10]',output:'[18,20]',text:'原地址A收到新内容，图现在计算得到新的输出。'}
   ];
   const step=Number(el.dataset.step||0),state=steps[step];
   el.querySelector('.buffer-state').innerHTML=`<div class="softmax-state"><strong>${state.title}</strong><p>${state.text}</p><div class="article-table" tabindex="0" role="region" aria-label="固定缓冲状态，可横向滚动"><table><thead><tr><th>变量目前指向</th><th>图读取A</th><th>B内容</th></tr></thead><tbody><tr><td>${state.variable}</td><td>${state.a}</td><td>${state.b}</td></tr></tbody></table></div><span>${step+1} / ${steps.length}</span></div>`;
   out.textContent=`本次重放输出：${state.output}。图读取的地址仍是A。`;
   const prev=el.querySelector('[data-buffer-prev]'),next=el.querySelector('[data-buffer-next]');prev.disabled=step===0;next.disabled=step===steps.length-1;
   if(!el.dataset.controlsBound){prev.addEventListener('click',()=>{el.dataset.step=Math.max(0,Number(el.dataset.step||0)-1);draw(el);});next.addEventListener('click',()=>{el.dataset.step=Math.min(steps.length-1,Number(el.dataset.step||0)+1);draw(el);});el.dataset.controlsBound='true';}return;
  }
  if(el.dataset.demo==='training-pipeline'){
   const stages=Number(el.querySelector('[name="pipeline-stages"]').value),m=Number(el.querySelector('[name="pipeline-microbatches"]').value);
   function plan(kind){
    const orders=[],dependencies=new Map(),done=new Map();
    const key=(stage,op,batch)=>`${stage}-${op}-${batch}`;
    for(let stage=0;stage<stages;stage++){
     const order=[];const push=(op,batch)=>order.push({stage,op,batch,key:key(stage,op,batch)});
     if(kind==='gpipe'){for(let i=0;i<m;i++)push('F',i);for(let i=m-1;i>=0;i--)push('B',i);}
     else{const warm=Math.min(m,stages-stage-1);for(let i=0;i<warm;i++)push('F',i);for(let i=0;i<m-warm;i++){push('F',warm+i);push('B',i);}for(let i=m-warm;i<m;i++)push('B',i);}
     orders.push(order);
     order.forEach((task,i)=>{const deps=i?[order[i-1].key]:[];if(task.op==='F'&&stage>0)deps.push(key(stage-1,'F',task.batch));if(task.op==='B'){deps.push(key(stage,'F',task.batch));if(stage<stages-1)deps.push(key(stage+1,'B',task.batch));}dependencies.set(task.key,deps);});
    }
    const visiting=new Set();
    function resolve(k){if(done.has(k))return done.get(k);if(visiting.has(k))throw Error('Invalid teaching schedule dependency cycle');visiting.add(k);const start=Math.max(0,...dependencies.get(k).map(d=>resolve(d).end)),value={start,end:start+1};done.set(k,value);visiting.delete(k);return value;}
    orders.flat().forEach(t=>resolve(t.key));const total=Math.max(...[...done.values()].map(t=>t.end));
    const peaks=orders.map(order=>{let active=0,peak=0;const events=order.map(t=>[done.get(t.key).end,t.op==='F'?1:-1]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);for(const [,change] of events){active+=change;peak=Math.max(peak,active);}return peak;});
    const grid=orders.map(order=>{const slots=Array(total).fill(null);order.forEach(t=>slots[done.get(t.key).start]=t);return slots;});return {total,peaks,grid};
   }
   const g=plan('gpipe'),f=plan('1f1b');
   const chart=(model,label,kind)=>`<div class="pipeline-grid" data-schedule-mode="${kind}"><h4>${label} · 各阶段已保存激活峰值：${model.peaks.join(' / ')} 份</h4><div class="article-table" tabindex="0" role="region" aria-label="${label}时间表，可横向滚动"><table style="width:${84+model.total*44}px;min-width:100%"><thead><tr><th scope="col" style="width:84px">阶段 / 槽</th>${Array.from({length:model.total},(_,i)=>`<th scope="col" style="width:44px">${i}</th>`).join('')}</tr></thead><tbody>${model.grid.map((slots,stage)=>`<tr><th scope="row">阶段${stage}</th>${slots.map((task,slot)=>task?`<td class="pipeline-task ${task.op==='B'?'backward':'forward'}" data-stage="${stage}" data-slot="${slot}" data-task="${task.op}${task.batch+1}">${task.op}${task.batch+1}</td>`:'<td class="pipeline-idle">·</td>').join('')}</tr>`).join('')}</tbody></table></div></div>`;
   el.querySelector('.training-schedule-result').innerHTML=chart(g,'GPipe','gpipe')+chart(f,'1F1B','1f1b');
   out.textContent=`GPipe：${g.total} 时间单位，阶段0峰值 ${g.peaks[0]} 份；1F1B：${f.total} 时间单位，阶段0峰值 ${f.peaks[0]} 份；平均忙碌 ${(2*m/f.total*100).toFixed(1)}%。`;return;
  }
  if(el.dataset.demo==='quant-rounding'){
   const scale=Number(el.querySelector('[name="quant-scale"]').value),values=[-1.2,-.46,0,.74,1.2];let maximum=0,clipped=0;
   const rows=values.map(x=>{const raw=Math.round(x/scale),q=Math.max(-7,Math.min(7,raw)),restored=q*scale,error=Math.abs(x-restored);maximum=Math.max(maximum,error);if(raw!==q)clipped++;return `<tr><td>${x.toFixed(2)}</td><td>${q}</td><td>${restored.toFixed(2)}</td><td>${error.toFixed(3)}</td><td>${raw===q?'未截断':'超出量程，已截断'}</td></tr>`;}).join('');
   el.querySelector('.quantization-values').innerHTML=`<div class="article-table" tabindex="0" role="region" aria-label="量化数值对照，可横向滚动"><table><thead><tr><th scope="col">原始值</th><th scope="col">码</th><th scope="col">还原值</th><th scope="col">误差</th><th scope="col">范围判断</th></tr></thead><tbody>${rows}</tbody></table></div>`;
   out.textContent=`可表示量程 ±${(7*scale).toFixed(1)}；${clipped} 项截断；最大绝对误差 ${maximum.toFixed(3)}。`;return;
  }
  if(el.dataset.demo==='kv-quant-memory'){
   const bits=Number(el.querySelector('[name="kv-bits"]').value),elements=2*32*8*128*4096,data=elements*bits/8/2**20,metadata=bits<16?elements/128*2/2**20:0,total=data+metadata;
   out.textContent=`元素数据 ${data} MiB + 尺度 ${metadata} MiB = 估计 ${total} MiB；16位基线 512 MiB，容量下降 ${((1-total/512)*100).toFixed(1)}%。`;return;
  }
  if(el.dataset.demo==='chunked'){
   const n=Number(el.querySelector('[name="prefill-chunks"]').value),duration=12/n;let clock=0,decode=0,first=0,prefill=0;const steps=[];
   const append=(label,time)=>{const start=clock;clock+=time;steps.push(`${label} ${start}–${clock} ms`);};
   for(let i=0;i<n;i++){append(`P${i+1}`,duration);if(i===n-1)prefill=clock;if(decode<3){append(`D${++decode}`,2);if(decode===1)first=clock;}}
   while(decode<3){append(`D${++decode}`,2);if(decode===1)first=clock;}
   el.querySelector('.chunked-sequence').innerHTML=`<div class="flow-strip">${steps.map(text=>`<span>${text}</span>`).join('<b aria-hidden="true">→</b>')}</div>`;
   out.textContent=`D首轮完成：${first} ms；P提示词处理完成：${prefill} ms；全部工作完成：${clock} ms。`;return;
  }
  if(el.dataset.demo==='softmax'){
   const step=Number(el.dataset.step||0);
   const states=[['第1步 · 完整计算的目标','指数强度 [1,2,4,3]，V=[10,20,30,40]。整体加权和 290，整体指数和 10，目标输出 290/10=29。'],['第2步 · 先处理第1块','第1块强度 [1,2] 除以 2，变成 [0.5,1]。ℓ=1.5，U=25。先保存它们；25/1.5≈16.67 只是当前块结果，尚不是最终输出。'],['第3步 · 最大值变大，修正旧累积','第2块出现强度 4，统一基准从 2 变成 4。旧 ℓ、U 都乘 0.5：ℓ=0.75，U=12.5。旧贡献还在，只是尺度变了。'],['第4步 · 加上第2块，完成归一化','新块 [4,3] 除以 4 → [1,0.75]。ℓ=0.75+1+0.75=2.5；U=12.5+1×30+0.75×40=72.5；最终 O=72.5/2.5=29。']];
   const state=el.querySelector('.softmax-state');state.innerHTML=`<strong>${states[step][0]}</strong><p>${states[step][1]}</p><span>${step+1} / ${states.length}</span>`;el.querySelector('[data-softmax-prev]').disabled=step===0;el.querySelector('[data-softmax-next]').disabled=step===states.length-1;return;
  }
  if(el.dataset.demo==='attention'){const seq=Number(el.querySelector('[name="seq"]').value);out.textContent=`${seq} × ${seq} × 32 × 2 字节 = ${(seq*seq*32*2/2**20).toFixed(0)} MiB`;}
  if(el.dataset.demo==='paging'){
   const b=Number(el.querySelector('[name="block"]').value),lengths=[17,33,8];const allocated=lengths.reduce((n,l)=>n+Math.ceil(l/b)*b,0),used=58;
   el.querySelector('.page-blocks').innerHTML=lengths.map((l,i)=>`<div class="page-block-row"><span>${'ABC'[i]} / ${l} token</span>${Array.from({length:Math.ceil(l/b)},(_,j)=>`<span class="kv-block">${Math.min(b,l-j*b)} / ${b}</span>`).join('')}</div>`).join('');
   out.textContent=`分页分配 ${allocated} 槽位，内部空闲 ${allocated-used}；最大长度预留 192 槽位，空闲 134。`;
  }
  if(el.dataset.demo==='zero'){const d=Number(el.querySelector('[name="ranks"]').value);out.textContent=`每卡常驻估计：DP 112 GB；ZeRO-1 ${(7*(4+12/d)).toFixed(2)} GB；ZeRO-2 ${(7*(2+14/d)).toFixed(2)} GB；ZeRO-3 ${(112/d).toFixed(2)} GB。`;}
  if(el.dataset.demo==='pipeline'){
   const n=number(el,'chunks'),c=number(el,'compute'),t=number(el,'comm');let previous=0;
   const sends=Array.from({length:n},(_,i)=>{const start=Math.max((i+1)*c,previous);previous=start+t;return {start,end:previous};});const serial=n*(c+t),total=previous;
   const blocks=(communication)=>Array.from({length:n},(_,i)=>{const start=communication?sends[i].start:i*c,duration=communication?t:c;return `<span class="time-block${communication?' comm':''}" style="left:${start/total*100}%;width:${duration/total*100}%" title="${communication?'传':'算'} ${i+1}: ${start.toFixed(1)}–${(start+duration).toFixed(1)} ms">${communication?'传':'算'}${i+1}</span>`;}).join('');
   el.querySelector('.time-chart').innerHTML=`<div class="time-row"><span>计算</span><div class="time-track">${blocks(false)}</div></div><div class="time-row"><span>通信</span><div class="time-track">${blocks(true)}</div></div><small>时间 0 → ${total.toFixed(1)} ms；每块通信等待对应计算和前一次通信完成。</small>`;
   out.textContent=`串行 ${serial.toFixed(1)} ms → 理想重叠 ${total.toFixed(1)} ms；耗时下降 ${((serial-total)/serial*100).toFixed(1)}%，加速比 ${(serial/total).toFixed(2)}×。`;
  }
 }
 document.querySelectorAll('.learning-demo').forEach(el=>{el.addEventListener('input',()=>draw(el));el.addEventListener('change',()=>draw(el));if(el.dataset.demo==='softmax'){el.querySelector('[data-softmax-prev]').addEventListener('click',()=>{el.dataset.step=Math.max(0,Number(el.dataset.step||0)-1);draw(el);});el.querySelector('[data-softmax-next]').addEventListener('click',()=>{el.dataset.step=Math.min(3,Number(el.dataset.step||0)+1);draw(el);});}draw(el);});
})();
