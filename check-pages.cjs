const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const {fileURLToPath,pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const root=__dirname,methods=JSON.parse(fs.readFileSync(path.join(root,'methods.json'),'utf8')),articles=require('./article-content.cjs');
const ready=Object.keys(articles),destination=path.join(root,'overview.html');
const {pages:foundations,mapping:prereqMap}=require('./foundations.cjs');
const output=path.resolve(process.env.AI_INFRA_QA_DIR||path.join(root,'.qa'));fs.mkdirSync(output,{recursive:true});
const url=pathToFileURL(destination).href;
const files=[path.join(root,'index.html'),destination,...methods.map(m=>path.join(root,'details',m.id+'.html')),...Object.keys(foundations).map(id=>path.join(root,'details',id+'.html'))];
// Validate every relative page and fragment, including references back to the overview.
let linkCount=0;for(const file of files){const html=fs.readFileSync(file,'utf8'),markup=html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'');const ids=[...markup.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);assert.equal(ids.length,new Set(ids).size,file+' duplicate IDs');for(const [,href] of markup.matchAll(/href="([^"]+)"/g)){if(/^https?:/.test(href))continue;const parsed=new URL(href,pathToFileURL(file));const target=fileURLToPath(parsed);assert.ok(fs.existsSync(target),`${file}: ${href} missing`);if(parsed.hash){const id=decodeURIComponent(parsed.hash.slice(1));assert.ok(fs.readFileSync(target,'utf8').includes('id="'+id+'"'),`${file}: ${href} invalid fragment`);}linkCount++;}assert.ok(!/<script[^>]+src=|<link[^>]+rel="stylesheet"/.test(html),'Unexpected remote / external asset');}
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL||(process.platform==='win32'?'msedge':undefined),headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto(url);assert.equal(await page.locator('.lane').count(),4);assert.equal(await page.locator('.method-row:visible').count(),47);assert.equal(await page.locator('#memory,#communication,.method-card').count(),0);
  for(const m of methods)assert.ok(await page.locator(`.mini[href$="/${m.id}.html"],.extension .method-link[href$="/${m.id}.html"]`).count(),m.id+' has no flow entry');
  await page.screenshot({path:path.join(output,'pages-overview.png')});await page.locator('#I-A2').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pages-flow.png')});
  await page.locator('#search').fill('MC2');assert.equal(await page.locator('.method-row:visible').count(),1);assert.ok(await page.locator('#row-M027').isVisible());
  await page.locator('#reset-filters').click();await page.locator('#catalog [data-open-dimension="communication"]').click();const commCount=methods.filter(m=>m.tags.includes('communication')).length;assert.equal(await page.locator('.method-row:visible').count(),commCount);
  await page.locator('#phase-filter').selectOption('training');assert.equal(await page.locator('.method-row:visible').count(),methods.filter(m=>m.tags.includes('communication')&&m.stages.some(s=>s.startsWith('T-')||s==='X-RL')).length);
  await page.locator('#catalog [data-open-dimension="memory"]').click();assert.equal(await page.locator('.method-row:visible').count(),methods.filter(m=>m.tags.includes('memory')).length);
  await page.locator('#ready-only').click();assert.equal(await page.locator('.method-row:visible').count(),ready.length);
  await page.locator('#status-filter').selectOption('pending');assert.equal(await page.locator('.method-row:visible').count(),47-ready.length);
  await page.locator('#search').fill('xxxxxxxx不存在');assert.ok(await page.locator('#empty').isVisible());await page.locator('#empty-reset').click();
  await page.locator('#catalog').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pages-table.png')});
  // Actual page navigation, back to the originating table row, and browser history.
  await page.locator('#row-M027 th>a').click();assert.ok(page.url().endsWith('/M027.html'));assert.equal(await page.locator('article[data-status="ready"]').count(),1);assert.equal(await page.locator('article section').count(),9);assert.equal(await page.locator('[aria-current="page"]').count(),1);
  await page.screenshot({path:path.join(output,'pages-mc2-top.png')});await page.locator('#example').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pages-mc2-example.png')});
  assert.ok((await page.locator('.demo-result').textContent()).includes('14.0 ms'));await page.locator('[name="compute"]').fill('1');await page.locator('[name="comm"]').fill('5');assert.ok((await page.locator('.demo-result').textContent()).includes('21.0 ms'));
  await page.locator('.return-overview').click();assert.ok(page.url().endsWith('#row-M027'));assert.ok(await page.locator('#row-M027').isVisible());await page.goBack();assert.ok(page.url().endsWith('/M027.html'));
  // Sidebar search and independent page switching.
  await page.locator('#sidebar-search').fill('Paged');assert.equal(await page.locator('.side-method:visible').count(),1);await page.locator('.side-method:visible').click();assert.ok(page.url().endsWith('/M016.html'));
  assert.ok((await page.locator('.demo-result').textContent()).includes('96'));await page.locator('[name="block"]').selectOption('8');assert.ok((await page.locator('.demo-result').textContent()).includes('72'));
  await page.locator('#example').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pages-paging.png')});
  await page.goto(pathToFileURL(path.join(root,'details','M036.html')).href);assert.ok((await page.locator('.demo-result').textContent()).includes('14.00'));await page.locator('[name="ranks"]').selectOption('4');assert.ok((await page.locator('.demo-result').textContent()).includes('28.00'));
  await page.goto(pathToFileURL(path.join(root,'details','M007.html')).href);assert.ok((await page.locator('.demo-result').textContent()).includes('1024 MiB'));await page.locator('[name="seq"]').selectOption('8192');assert.ok((await page.locator('.demo-result').textContent()).includes('4096 MiB'));
  assert.ok(!(await page.locator('.prerequisites').innerText()).includes('undefined'));
  // Video-first template: existing lesson before prerequisites and text; no empty players elsewhere.
  const order=await page.evaluate(()=>({video:document.querySelector('.lesson-video').getBoundingClientRect().bottom,prerequisites:document.querySelector('.prerequisites').getBoundingClientRect().top,text:document.querySelector('article[data-status]').getBoundingClientRect().top}));
  assert.ok(order.video<order.prerequisites&&order.prerequisites<order.text);
  await page.waitForFunction(()=>document.getElementById('method-video').readyState>=1);assert.ok(Math.abs(await page.locator('#method-video').evaluate(v=>v.duration)-191.05)<.2);
  await page.locator('.video-chapters>summary').click();const chapter=page.locator('[data-video-time]').nth(4),chapterTime=Number(await chapter.getAttribute('data-video-time'));await chapter.click();await page.waitForFunction(t=>document.getElementById('method-video').currentTime>t+.3,chapterTime);await page.locator('#method-video').evaluate(v=>v.pause());await page.screenshot({path:path.join(output,'site-flash-video.png')});
  await page.locator('.prerequisites a[href="F001.html"]').click();assert.ok(page.url().endsWith('F001.html'));assert.equal(await page.locator('article[data-status="foundation"]').count(),1);assert.ok((await page.locator('article').innerText()).includes('29'));await page.locator('.related-links a[href="M007.html"]').click();
  await page.locator('#online').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'flash-online-explanation.png')});
  const next=page.locator('[data-softmax-next]');await next.click();assert.ok((await page.locator('.softmax-state').textContent()).includes('16.67'));await next.click();assert.ok((await page.locator('.softmax-state').textContent()).includes('12.5'));await next.click();assert.ok((await page.locator('.softmax-state').textContent()).includes('72.5/2.5=29'));assert.ok(await next.isDisabled());await page.locator('[data-softmax-prev]').click();assert.ok((await page.locator('.softmax-state').textContent()).includes('第3步'));
  assert.ok(!(await page.locator('.advanced-reading').getAttribute('open')));await page.locator('.advanced-reading>summary').click();assert.equal(await page.locator('.advanced-reading').getAttribute('open'),'');
  await page.goto(pathToFileURL(path.join(root,'details','M026.html')).href);assert.ok((await page.locator('.demo-result').textContent()).includes('7.0 ms'));
  // A complete tutorial must expose the scheduling tradeoff and keep sources/examples linked.
  await page.goto(pathToFileURL(path.join(root,'details','M022.html')).href);
  assert.ok((await page.locator('[data-demo="chunked"] .demo-result').textContent()).includes('D首轮完成：6 ms；P提示词处理完成：16 ms'));
  await page.locator('[name="prefill-chunks"]').selectOption('1');assert.ok((await page.locator('[data-demo="chunked"] .demo-result').textContent()).includes('D首轮完成：14 ms；P提示词处理完成：12 ms'));
  await page.locator('[name="prefill-chunks"]').selectOption('6');assert.ok((await page.locator('[data-demo="chunked"] .demo-result').textContent()).includes('D首轮完成：4 ms；P提示词处理完成：18 ms'));
  await page.locator('[name="prefill-chunks"]').selectOption('3');await page.locator('[data-demo="chunked"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'chunked-prefill-example.png')});
  for(const id of ['M014','M015','M022','M013']){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);assert.equal(await page.locator('.example-download a').count(),1);assert.ok((await page.locator('#sources').innerText()).includes('2026-10-08'));assert.equal(await page.locator('.video-pending').count(),1);}
  await page.goto(pathToFileURL(path.join(root,'details','M013.html')).href);await page.locator('#probability-example').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'speculative-probability-example.png')});
  // Check rendered structure and overflow on every finished article.
  await page.goto(pathToFileURL(path.join(root,'details','M004.html')).href);
  assert.ok((await page.locator('[data-demo="quant-rounding"] .demo-result').textContent()).includes('0 项截断；最大绝对误差 0.060'));
  await page.locator('[name="quant-scale"]').selectOption('0.1');assert.ok((await page.locator('[data-demo="quant-rounding"] .demo-result').textContent()).includes('2 项截断；最大绝对误差 0.500'));
  await page.locator('[name="quant-scale"]').selectOption('0.3');assert.ok((await page.locator('[data-demo="quant-rounding"] .demo-result').textContent()).includes('0 项截断；最大绝对误差 0.140'));
  await page.locator('[data-demo="quant-rounding"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'quantization-rounding-example.png')});
  await page.goto(pathToFileURL(path.join(root,'details','M005.html')).href);
  assert.ok((await page.locator('[data-demo="kv-quant-memory"] .demo-result').textContent()).includes('估计 260 MiB'));
  await page.locator('[name="kv-bits"]').selectOption('16');assert.ok((await page.locator('[data-demo="kv-quant-memory"] .demo-result').textContent()).includes('估计 512 MiB'));
  await page.locator('[name="kv-bits"]').selectOption('4');assert.ok((await page.locator('[data-demo="kv-quant-memory"] .demo-result').textContent()).includes('估计 132 MiB'));
  await page.locator('[data-demo="kv-quant-memory"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'kv-quantization-memory-example.png')});
  for(const id of ['M004','M005']){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);assert.equal(await page.locator('.example-download a').count(),1);assert.ok((await page.locator('#sources').innerText()).includes('2026-10-08'));assert.equal(await page.locator('.video-pending').count(),1);assert.equal(await page.locator('video').count(),0);}
  await page.setViewportSize({width:390,height:1050});await page.goto(pathToFileURL(path.join(root,'details','M004.html')).href);await page.locator('[data-demo="quant-rounding"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'quantization-mobile-example.png')});
  // Distributed tutorials: no invented video, and the schedule follows actual F/B dependencies.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M024','M039','M040']){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);assert.equal(await page.locator('.example-download a').count(),1);assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));assert.equal(await page.locator('.video-pending').count(),1);assert.equal(await page.locator('video').count(),0);}
  assert.ok((await page.locator('[data-demo="training-pipeline"] .demo-result').textContent()).includes('GPipe：10 时间单位，阶段0峰值 4 份；1F1B：10 时间单位，阶段0峰值 2 份'));
  const knownSlots={gpipe:{F1:0,F4:3,B4:6,B1:9},'1f1b':{F1:0,F2:1,B1:3,F3:4,B2:5,F4:6,B3:7,B4:9}};
  for(const [mode,tasks] of Object.entries(knownSlots))for(const [task,slot] of Object.entries(tasks))assert.equal(await page.locator(`[data-schedule-mode="${mode}"] [data-stage="0"][data-task="${task}"]`).getAttribute('data-slot'),String(slot));
  for(const stages of [2,4,8])for(const batches of [1,4,8,16]){
   await page.locator('[name="pipeline-stages"]').selectOption(String(stages));await page.locator('[name="pipeline-microbatches"]').selectOption(String(batches));
   const total=2*(batches+stages-1),peak=Math.min(stages,batches),text=await page.locator('[data-demo="training-pipeline"] .demo-result').textContent();
   assert.ok(text.includes(`GPipe：${total} 时间单位，阶段0峰值 ${batches} 份；1F1B：${total} 时间单位，阶段0峰值 ${peak} 份`));
   assert.ok(text.includes(`平均忙碌 ${(2*batches/total*100).toFixed(1)}%`));
   for(const mode of ['gpipe','1f1b']){
    const tasks=await page.locator(`[data-schedule-mode="${mode}"] .pipeline-task`).evaluateAll(els=>els.map(el=>({stage:Number(el.dataset.stage),slot:Number(el.dataset.slot),op:el.dataset.task[0],batch:Number(el.dataset.task.slice(1))})));
    assert.equal(tasks.length,2*stages*batches);const keys=new Map(tasks.map(t=>[`${t.stage}-${t.op}-${t.batch}`,t.slot]));assert.equal(keys.size,tasks.length);
    for(const t of tasks){if(t.op==='F'&&t.stage>0)assert.ok(t.slot>keys.get(`${t.stage-1}-F-${t.batch}`));if(t.op==='B'){assert.ok(t.slot>keys.get(`${t.stage}-F-${t.batch}`));if(t.stage<stages-1)assert.ok(t.slot>keys.get(`${t.stage+1}-B-${t.batch}`));}}
   }
  }
  await page.locator('[name="pipeline-stages"]').selectOption('2');await page.locator('[name="pipeline-microbatches"]').selectOption('4');await page.locator('#interactive').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pipeline-schedule-desktop.png')});
  await page.setViewportSize({width:390,height:1050});await page.locator('#interactive').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'pipeline-schedule-mobile.png')});
  for(const selector of ['#gpipe .article-table','#onef1b .article-table','.pipeline-grid .article-table'])assert.ok(await page.locator(selector).first().evaluate(e=>e.scrollWidth>e.clientWidth),'Mobile time table must scroll without breaking task labels');
  await page.setViewportSize({width:1440,height:1050});await page.goto(pathToFileURL(path.join(root,'details','M024.html')).href);await page.locator('#tp-rows').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'tensor-parallel-worked-example.png')});
  await page.goto(pathToFileURL(path.join(root,'details','M039.html')).href);await page.locator('#weighting').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'gradient-accumulation-weighting.png')});
  // Packing must isolate sample boundaries; host/copy/compute queues must obey readiness.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M020','M033','M023']){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);assert.equal(await page.locator('.example-download a').count(),1);assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));assert.equal(await page.locator('video').count(),0);}
  await page.goto(pathToFileURL(path.join(root,'details','M020.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('B1可读：B1。没有跨样本读取'));
  assert.equal(await page.locator('.packing-mask-grid [data-visible="true"]').count(),9);
  await page.locator('[name="pack-mask"]').selectOption('causal');assert.ok((await page.locator('.demo-result').textContent()).includes('B1可读：A1、A2、A3、B1。跨样本读取'));
  assert.equal(await page.locator('.packing-mask-grid [data-visible="true"]').count(),15);
  await page.locator('[name="pack-query"]').selectOption('4');assert.ok((await page.locator('.demo-result').textContent()).includes('B2可读：A1、A2、A3、B1、B2'));
  await page.locator('[name="pack-mask"]').selectOption('isolated');assert.ok((await page.locator('.demo-result').textContent()).includes('B2可读：B1、B2'));
  await page.locator('[name="pack-query"]').selectOption('2');assert.ok((await page.locator('.demo-result').textContent()).includes('A3可读：A1、A2、A3。没有跨样本'));
  await page.locator('[name="pack-query"]').selectOption('3');await page.locator('#mask').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'packing-boundary-desktop.png')});
  await page.setViewportSize({width:390,height:1050});await page.locator('#mask').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'packing-boundary-mobile.png')});
  await page.setViewportSize({width:1440,height:1050});await page.goto(pathToFileURL(path.join(root,'details','M033.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('串行 40 ms → 理想流水 28 ms；首批完成 10 ms'));
  assert.equal(await page.locator('[data-input-batch]').count(),12);
  const queueTasks=await page.locator('[data-input-batch]').evaluateAll(els=>els.map(e=>({batch:Number(e.dataset.inputBatch),stage:Number(e.dataset.inputStage),start:Number(e.dataset.start),end:Number(e.dataset.end)})));
  for(const t of queueTasks){if(t.stage)assert.ok(t.start>=queueTasks.find(x=>x.batch===t.batch&&x.stage===t.stage-1).end);if(t.batch)assert.ok(t.start>=queueTasks.find(x=>x.batch===t.batch-1&&x.stage===t.stage).end);}
  await page.locator('[name="input-prepare"]').selectOption('8');assert.ok((await page.locator('.demo-result').textContent()).includes('串行 60 ms → 理想流水 39 ms'));
  await page.locator('[name="input-prepare"]').selectOption('3');await page.locator('[name="input-transfer"]').selectOption('8');assert.ok((await page.locator('.demo-result').textContent()).includes('串行 68 ms → 理想流水 41 ms'));
  await page.locator('[name="input-transfer"]').selectOption('1');await page.locator('#timeline').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'input-pipeline-desktop.png')});
  await page.locator('.input-stage-chart summary').click();assert.ok((await page.locator('.input-stage-chart table').innerText()).includes('22–28 ms'));
  await page.setViewportSize({width:390,height:1050});await page.locator('[data-demo="input-pipeline"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'input-pipeline-mobile.png')});
  await page.goto(pathToFileURL(path.join(root,'details','M023.html')).href);assert.ok((await page.locator('.demo-result').textContent()).includes('串行 24 ms → 理想流水 20 ms；首批完成 8 ms'));assert.equal(await page.locator('[data-input-batch]').count(),6);
  await page.locator('[name="input-prepare"]').selectOption('8');assert.ok((await page.locator('.demo-result').textContent()).includes('串行 42 ms → 理想流水 30 ms；首批完成 14 ms'));
  await page.locator('[name="input-prepare"]').selectOption('2');await page.setViewportSize({width:1440,height:1050});await page.locator('#autoregressive').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'async-autoregressive-dependencies.png')});
  // Local fusion, compilation costs and fixed-address replay are distinct mechanisms.
  for(const id of ['M009','M018','M019']){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);assert.equal(await page.locator('.example-download a').count(),1);assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));assert.equal(await page.locator('.video-pending').count(),1);assert.equal(await page.locator('video').count(),0);}
  await page.goto(pathToFileURL(path.join(root,'details','M009.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('分离 10 MiB → 融合 6 MiB，减少 4 MiB（40%）'));
  await page.locator('[name="fusion-save"]').selectOption('yes');assert.ok((await page.locator('.demo-result').textContent()).includes('融合 8 MiB，减少 2 MiB（20%）'));
  await page.locator('[name="fusion-bytes"]').selectOption('4');assert.ok((await page.locator('.demo-result').textContent()).includes('分离 20 MiB → 融合 16 MiB'));
  await page.locator('#traffic').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'local-fusion-traffic.png')});
  await page.goto(pathToFileURL(path.join(root,'details','M018.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('累计节省 200 ms；严格回本至少 501 次'));
  await page.locator('[name="compile-calls"]').selectOption('100');assert.ok((await page.locator('.demo-result').textContent()).includes('累计多花 160 ms'));
  await page.locator('[name="compile-calls"]').selectOption('500');assert.ok((await page.locator('.demo-result').textContent()).includes('累计成本相同'));
  await page.locator('[name="compile-calls"]').selectOption('1000');await page.locator('[name="compile-variants"]').selectOption('4');assert.ok((await page.locator('.demo-result').textContent()).includes('累计多花 400 ms；严格回本至少 2001 次'));
  await page.locator('[name="compile-variants"]').selectOption('1');await page.locator('#amortization').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'compile-amortization-desktop.png')});
  await page.setViewportSize({width:390,height:1050});await page.locator('#amortization').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'compile-amortization-mobile.png')});await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M019.html')).href);
  assert.ok(await page.locator('[data-buffer-prev]').isDisabled());assert.ok((await page.locator('.demo-result').textContent()).includes('[-2,4]'));
  await page.locator('[data-buffer-next]').click();assert.ok((await page.locator('.demo-result').textContent()).includes('[6,8]'));
  await page.locator('[data-buffer-next]').click();assert.ok((await page.locator('.demo-result').textContent()).includes('[6,8]'));assert.ok((await page.locator('.buffer-state').textContent()).includes('[9,10]'));assert.ok((await page.locator('.buffer-state').textContent()).includes('变量现在指向B'));
  await page.locator('#buffers').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'graph-replay-buffer-desktop.png')});
  await page.locator('[data-buffer-next]').click();assert.ok((await page.locator('.demo-result').textContent()).includes('[18,20]'));assert.ok(await page.locator('[data-buffer-next]').isDisabled());
  await page.locator('[data-buffer-prev]').click();assert.ok((await page.locator('.demo-result').textContent()).includes('[6,8]'));
  await page.setViewportSize({width:390,height:1050});await page.locator('[data-demo="graph-buffer"]').evaluate(e=>e.scrollIntoView());await page.screenshot({path:path.join(output,'graph-replay-buffer-mobile.png')});
  // Cache costs, prefetch deadlines, and safe storage reuse are separate invariants.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M017','M038','M047']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
   assert.equal(await page.locator('.video-pending').count(),1);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M017.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('20 ms'));
  await page.locator('[name="tier-recompute"]').selectOption('12');
  assert.ok((await page.locator('.demo-result').textContent()).includes('下界已大于重算'));
  await page.locator('[name="tier-bandwidth"]').selectOption('50');
  assert.ok((await page.locator('.demo-result').textContent()).includes('10 ms'));
  await page.locator('[name="tier-mib"]').selectOption('1024');
  assert.equal(await page.locator('[data-tier-ms]').getAttribute('data-tier-ms'),'20');
  await page.locator('#traffic').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'kv-tier-cost-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="kv-tier-cost"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'kv-tier-cost-mobile.png')});
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M038.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('反向等待 5 ms'));
  assert.equal(await page.locator('[data-offload-start]').getAttribute('data-offload-start'),'9');
  assert.equal(await page.locator('[data-offload-end]').getAttribute('data-offload-end'),'17');
  await page.locator('[name="offload-lead"]').selectOption('10');
  assert.ok((await page.locator('.demo-result').textContent()).includes('反向等待 0 ms'));
  await page.locator('[name="offload-transfer"]').selectOption('16');
  assert.ok((await page.locator('.demo-result').textContent()).includes('反向等待 6 ms'));
  await page.locator('[name="offload-lead"]').selectOption('12');
  assert.ok((await page.locator('.demo-result').textContent()).includes('反向等待 4 ms'));
  for(const lead of ['3','10','12'])for(const duration of ['4','8','16']){
   await page.locator('[name="offload-lead"]').selectOption(lead);
   await page.locator('[name="offload-transfer"]').selectOption(duration);
   const expectedWait=Math.max(0,Number(duration)-Number(lead));
   assert.ok((await page.locator('.demo-result').textContent()).includes(`反向等待 ${expectedWait} ms`));
  }
  await page.locator('[name="offload-lead"]').selectOption('3');
  await page.locator('[name="offload-transfer"]').selectOption('8');
  await page.locator('#timeline').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'training-offload-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="offload-deadline"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'training-offload-mobile.png')});
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M047.html')).href);
  assert.ok((await page.locator('.demo-result').textContent()).includes('可安全复用'));
  assert.ok((await page.locator('.demo-result').textContent()).includes('10 MiB'));
  await page.locator('[name="memory-reader"]').selectOption('5');
  assert.ok((await page.locator('.demo-result').textContent()).includes('直接覆盖会破坏旧数据'));
  assert.ok((await page.locator('.demo-result').textContent()).includes('14 MiB'));
  assert.ok((await page.locator('.memory-demo-table').textContent()).includes('槽2（独立）'));
  await page.locator('#example').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'memory-lifetime-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="memory-lifetime"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'memory-lifetime-mobile.png')});

  // Independent communication models: semantics, handoff costs and expert load conservation.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M025','M028','M030']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M025.html')).href);
  assert.ok((await page.locator('.demo-result').innerText()).includes('关键路径6阶段'));
  assert.ok((await page.locator('.demo-result').innerText()).includes('教学整块树合计更低'));
  await page.locator('[name="comm-size"]').selectOption('67108864');
  assert.ok(Math.abs(Number(await page.locator('[data-comm-ring]').getAttribute('data-comm-ring'))-4.445)<1e-10);
  assert.ok((await page.locator('.demo-result').innerText()).includes('Ring合计更低'));
  await page.locator('[name="comm-ranks"]').selectOption('16');
  assert.ok((await page.locator('.demo-result').innerText()).includes('Ring 30轮'));
  await page.locator('[name="comm-size"]').selectOption('4096');
  await page.locator('[name="comm-alpha"]').selectOption('20');
  assert.ok((await page.locator('.demo-result').innerText()).includes('教学整块树合计更低'));
  await page.locator('#tree').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'collective-cost-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="collective-cost"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'collective-cost-mobile.png')});
  assert.ok(await page.locator('[data-demo="collective-cost"] .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth),'Communication total must fit at 390px');
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M028.html')).href);
  assert.equal(Number(await page.locator('[data-pd-mixed]').getAttribute('data-pd-mixed')),74);
  assert.equal(Number(await page.locator('[data-pd-separate]').getAttribute('data-pd-separate')),66);
  await page.locator('[name="pd-interference"]').selectOption('0');
  assert.ok((await page.locator('.demo-result').innerText()).includes('第二token更晚'));
  assert.equal(Number(await page.locator('[data-pd-mixed]').getAttribute('data-pd-mixed')),44);
  await page.locator('[name="pd-size"]').selectOption('2048');
  await page.locator('[name="pd-bandwidth"]').selectOption('8');
  assert.equal(Number(await page.locator('[data-pd-separate]').getAttribute('data-pd-separate')),296);
  await page.locator('[name="pd-size"]').selectOption('512');
  await page.locator('[name="pd-bandwidth"]').selectOption('25');
  await page.locator('[name="pd-interference"]').selectOption('30');
  await page.locator('#latency').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'pd-handoff-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="pd-handoff"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'pd-handoff-mobile.png')});
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M030.html')).href);
  for(const [layout,expected] of [['original',[100,20]],['moved',[90,30]],['replicated',[60,60]]]){
   await page.locator('[name="ep-layout"]').selectOption(layout);
   const loads=await page.locator('[data-ep-load]').evaluateAll(els=>els.map(e=>Number(e.dataset.epLoad)));
   assert.deepEqual(loads,expected);assert.equal(loads.reduce((a,b)=>a+b,0),120);
  }
  assert.ok((await page.locator('.demo-result').innerText()).includes('新增256 MiB'));
  await page.locator('[name="ep-hot"]').selectOption('20');
  assert.deepEqual(await page.locator('[data-ep-load]').evaluateAll(els=>els.map(e=>Number(e.dataset.epLoad))),[30,30]);
  await page.locator('[name="ep-layout"]').selectOption('moved');
  assert.deepEqual(await page.locator('[data-ep-load]').evaluateAll(els=>els.map(e=>Number(e.dataset.epLoad))),[30,30]);
  assert.ok((await page.locator('.demo-result').innerText()).includes('无新增权重副本'));
  await page.locator('[name="ep-hot"]').selectOption('80');
  await page.locator('[name="ep-layout"]').selectOption('replicated');
  await page.locator('#example').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'expert-placement-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="expert-placement"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'expert-placement-mobile.png')});

  // Governance, target-quality confirmation and fixed-behavior RL pipeline.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M029','M043','M046']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
   assert.equal(await page.locator('.video-pending').count(),1);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M029.html')).href);
  const serviceValues=async()=>[Number(await page.locator('.demo-result').getAttribute('data-service-wait')),Number(await page.locator('.demo-result').getAttribute('data-service-final')),Number(await page.locator('[data-service-b-finish]').getAttribute('data-service-b-finish'))];
  assert.deepEqual(await serviceValues(),[6,12,10]);
  await page.locator('[name="service-policy"]').selectOption('priority');
  assert.deepEqual(await serviceValues(),[2,12,2]);
  await page.locator('[name="service-long"]').selectOption('16');
  assert.deepEqual(await serviceValues(),[2,20,2]);
  await page.locator('[name="service-policy"]').selectOption('fcfs');
  assert.deepEqual(await serviceValues(),[34/3,20,18]);
  await page.locator('[name="service-long"]').selectOption('8');
  await page.locator('#priority').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'service-priority-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="service-priority"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'service-priority-mobile.png')});
  assert.ok(await page.locator('.coordination-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M043.html')).href);
  const qualityValues=async()=>[Number(await page.locator('[data-quality-total]').getAttribute('data-quality-total')),Number(await page.locator('[data-quality-confirmed]').getAttribute('data-quality-confirmed'))];
  assert.deepEqual(await qualityValues(),[2080,2000]);
  await page.locator('[name="quality-run"]').selectOption('kernel');
  assert.deepEqual(await qualityValues(),[1280,2000]);
  await page.locator('[name="quality-run"]').selectOption('recipe');
  assert.deepEqual(await qualityValues(),[3360,4000]);
  await page.locator('[name="quality-run"]').selectOption('data');
  assert.deepEqual(await qualityValues(),[1710,1500]);
  await page.locator('[name="quality-interval"]').selectOption('1000');
  assert.deepEqual(await qualityValues(),[2140,2000]);
  await page.locator('[name="quality-interval"]').selectOption('200');
  assert.deepEqual(await qualityValues(),[1500,1200]);
  await page.locator('[name="quality-interval"]').selectOption('500');
  await page.locator('#quality').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'time-to-quality-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="time-to-quality"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'time-to-quality-mobile.png')});
  assert.ok(await page.locator('.coordination-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M046.html')).href);
  const rlTimes=async()=>[Number(await page.locator('[data-rl-serial]').getAttribute('data-rl-serial')),Number(await page.locator('[data-rl-pipeline]').getAttribute('data-rl-pipeline'))];
  assert.deepEqual(await rlTimes(),[270,170]);
  await page.locator('[name="rl-batches"]').selectOption('5');
  assert.deepEqual(await rlTimes(),[450,250]);
  await page.locator('[name="rl-rollout"]').selectOption('80');
  assert.deepEqual(await rlTimes(),[650,450]);
  await page.locator('[name="rl-batches"]').selectOption('3');
  await page.locator('[name="rl-rollout"]').selectOption('40');
  await page.locator('[name="rl-training"]').selectOption('60');
  assert.deepEqual(await rlTimes(),[360,240]);
  await page.locator('[name="rl-training"]').selectOption('30');
  assert.equal(await page.locator('.rl-stage-chart .ckpt-lane i').count(),9);
  await page.locator('#pipeline').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'rl-stage-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="rl-stage-pipeline"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'rl-stage-mobile.png')});
  assert.ok(await page.locator('.coordination-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));

  // Compression representation, workload costs and result reuse gates.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M001','M044','M045']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
   assert.equal(await page.locator('.video-pending').count(),1);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M001.html')).href);
  const pruneCount=async()=>Number(await page.locator('[data-prune-multiplies]').getAttribute('data-prune-multiplies'));
  assert.equal(await pruneCount(),32);
  await page.locator('[name="prune-mode"]').selectOption('masked');
  assert.equal(await pruneCount(),64);
  assert.ok((await page.locator('.demo-result').innerText()).includes('mask不自动启用稀疏执行'));
  await page.locator('[name="prune-keep"]').selectOption('2');
  assert.equal(await pruneCount(),64);
  await page.locator('[name="prune-mode"]').selectOption('compact');
  assert.equal(await pruneCount(),16);
  await page.locator('[name="prune-keep"]').selectOption('8');
  assert.equal(await pruneCount(),64);
  await page.locator('[name="prune-keep"]').selectOption('4');
  await page.locator('#mlp').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'pruning-shape-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="pruning-shape"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'pruning-shape-mobile.png')});
  assert.ok(await page.locator('.workload-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M044.html')).href);
  const budgetTotal=async()=>Number(await page.locator('[data-budget-total]').getAttribute('data-budget-total'));
  assert.equal(await budgetTotal(),480);
  await page.locator('[name="budget-output"]').selectOption('100');
  assert.equal(await budgetTotal(),280);
  await page.locator('[name="budget-output"]').selectOption('200');
  await page.locator('[name="budget-prep"]').selectOption('150');
  assert.equal(await budgetTotal(),600);
  assert.ok((await page.locator('.demo-result').innerText()).includes('增加50.00 ms'));
  await page.locator('[name="budget-input"]').selectOption('1000');
  await page.locator('[name="budget-prep"]').selectOption('0');
  assert.equal(await budgetTotal(),550);
  await page.locator('[name="budget-input"]').selectOption('500');
  await page.locator('[name="budget-prep"]').selectOption('30');
  await page.locator('#budget').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'request-budget-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="request-budget"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'request-budget-mobile.png')});
  assert.ok(await page.locator('.workload-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M045.html')).href);
  const cacheHit=async()=>page.locator('.demo-result').getAttribute('data-cache-hit');
  assert.equal(await cacheHit(),'true');
  await page.locator('[name="cache-threshold"]').selectOption('0.99');
  assert.equal(await cacheHit(),'false');
  await page.locator('[name="cache-threshold"]').selectOption('0.9');
  for(const value of ['tenant','version','intent','expired','partial']){
   await page.locator('[name="cache-case"]').selectOption(value);
   assert.equal(await cacheHit(),'false');
  }
  await page.locator('[name="cache-case"]').selectOption('same');
  assert.equal(await cacheHit(),'true');
  await page.locator('[name="cache-threshold"]').selectOption('0.95');
  await page.locator('#semantic').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'result-cache-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="result-cache-gate"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'result-cache-mobile.png')});
  assert.ok(await page.locator('.workload-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));

  // Update semantics, checkpoint completion boundaries and startup coverage.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M041','M042','M032']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
   assert.equal(await page.locator('.video-pending').count(),1);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M041.html')).href);
  const optValues=async()=>[Number(await page.locator('[data-opt-separate]').getAttribute('data-opt-separate')),Number(await page.locator('[data-opt-fused]').getAttribute('data-opt-fused')),Number(await page.locator('[data-opt-launches]').getAttribute('data-opt-launches'))];
  assert.deepEqual(await optValues(),[40*1048576,28*1048576,192]);
  await page.locator('[name="opt-tensors"]').selectOption('1024');
  assert.deepEqual(await optValues(),[40*1048576,28*1048576,3072]);
  await page.locator('[name="opt-elements"]').selectOption('1024');
  assert.deepEqual(await optValues(),[40960,28672,3072]);
  await page.locator('[name="opt-elements"]').selectOption('1048576');
  await page.locator('[name="opt-tensors"]').selectOption('64');
  await page.locator('#traffic').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'optimizer-traffic-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="optimizer-traffic"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'optimizer-traffic-mobile.png')});
  assert.ok(await page.locator('.lifecycle-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M042.html')).href);
  const ckptValues=async()=>[Number(await page.locator('[data-ckpt-training]').getAttribute('data-ckpt-training')),Number(await page.locator('[data-ckpt-final]').getAttribute('data-ckpt-final')),Number(await page.locator('[data-ckpt-wait]').getAttribute('data-ckpt-wait'))];
  assert.deepEqual(await ckptValues(),[44,56,0]);
  await page.locator('[name="ckpt-write"]').selectOption('40');
  assert.deepEqual(await ckptValues(),[64,104,20]);
  await page.locator('[name="ckpt-interval"]').selectOption('4');
  assert.deepEqual(await ckptValues(),[42,82,0]);
  await page.locator('[name="ckpt-interval"]').selectOption('1');
  await page.locator('[name="ckpt-write"]').selectOption('12');
  assert.deepEqual(await ckptValues(),[54,66,6]);
  await page.locator('[name="ckpt-interval"]').selectOption('2');
  await page.locator('#timeline').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'checkpoint-timeline-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="checkpoint-timeline"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'checkpoint-timeline-mobile.png')});
  assert.ok(await page.locator('.lifecycle-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M032.html')).href);
  const startupValues=async()=>[Number(await page.locator('[data-startup-ready]').getAttribute('data-startup-ready')),Number(await page.locator('[data-startup-first]').getAttribute('data-startup-first'))];
  assert.deepEqual(await startupValues(),[7.1,.05]);
  await page.locator('[name="startup-cache"]').selectOption('miss');
  assert.deepEqual(await startupValues(),[14.6,.05]);
  await page.locator('[name="startup-cache"]').selectOption('hit');
  await page.locator('[name="startup-warm"]').selectOption('1');
  assert.deepEqual(await startupValues(),[6.7,.45]);
  await page.locator('[name="startup-bucket"]').selectOption('0');
  assert.deepEqual(await startupValues(),[6.7,.05]);
  await page.locator('[name="startup-warm"]').selectOption('0');
  assert.deepEqual(await startupValues(),[6.5,.45]);
  await page.locator('[name="startup-warm"]').selectOption('3');
  await page.locator('[name="startup-bucket"]').selectOption('2');
  await page.locator('#timeline').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'startup-readiness-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="startup-readiness"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'startup-readiness-mobile.png')});
  assert.ok(await page.locator('.lifecycle-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));

  // Sampling contract, trainable-state budget and mixed-adapter restoration.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M012','M034','M031']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.equal(await page.locator('.video-pending').count(),1);
   assert.equal(await page.locator('video').count(),0);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
  }
  await page.goto(pathToFileURL(path.join(root,'details','M012.html')).href);
  const sampleProbs=async()=>page.locator('[data-sample-prob]').evaluateAll(els=>els.map(e=>Number(e.dataset.sampleProb)));
  const expectedProbs=async expected=>{const actual=await sampleProbs();expected.forEach((v,i)=>assert.ok(Math.abs(actual[i]-v)<1e-12));};
  await expectedProbs([4/9,1/3,2/9,0]);
  assert.equal(await page.locator('[data-sample-token]').getAttribute('data-sample-token'),'B');
  await page.locator('[name="sample-k"]').selectOption('2');
  await page.locator('[name="sample-p"]').selectOption('0.5');
  await expectedProbs([1,0,0,0]);
  await page.locator('[name="sample-mask"]').selectOption('cd');
  await expectedProbs([0,0,1,0]);
  await page.locator('[name="sample-p"]').selectOption('1');
  await expectedProbs([0,0,2/3,1/3]);
  await page.locator('[name="sample-u"]').selectOption('0.9');
  assert.equal(await page.locator('[data-sample-token]').getAttribute('data-sample-token'),'D');
  await page.locator('[name="sample-mask"]').selectOption('empty');
  await expectedProbs([0,0,0,0]);
  assert.equal(await page.locator('[data-sample-token]').getAttribute('data-sample-token'),'');
  assert.ok((await page.locator('.demo-result').innerText()).includes('没有合法候选'));
  await page.locator('[name="sample-mask"]').selectOption('all');
  await page.locator('[name="sample-k"]').selectOption('4');
  await page.locator('[name="sample-p"]').selectOption('0.8');
  await page.locator('[name="sample-u"]').selectOption('0.5');
  await page.locator('[data-demo="sampling-policy"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'sampling-policy-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="sampling-policy"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'sampling-policy-mobile.png')});
  assert.ok(await page.locator('.adaptation-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M034.html')).href);
  const adapterBudget=async()=>[Number(await page.locator('[data-lora-trainable]').getAttribute('data-lora-trainable')),Number(await page.locator('[data-lora-total]').getAttribute('data-lora-total'))];
  assert.deepEqual(await adapterBudget(),[131072,33.5]);
  await page.locator('[name="lora-rank"]').selectOption('64');
  assert.deepEqual(await adapterBudget(),[524288,38]);
  await page.locator('[name="lora-base-byte"]').selectOption('0.5');
  assert.deepEqual(await adapterBudget(),[524288,14]);
  await page.locator('[name="lora-rank"]').selectOption('8');
  assert.deepEqual(await adapterBudget(),[65536,8.75]);
  assert.ok((await page.locator('.demo-result').innerText()).includes('低位元数据另计'));
  await page.locator('[name="lora-rank"]').selectOption('16');
  await page.locator('[name="lora-base-byte"]').selectOption('2');
  await page.locator('#budget').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'lora-budget-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="lora-budget"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'lora-budget-mobile.png')});
  assert.ok(await page.locator('.adaptation-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M031.html')).href);
  const mixedWork=async()=>page.locator('[data-multi-valid]').evaluate(e=>[Number(e.dataset.multiValid),Number(e.dataset.multiPadded)]);
  assert.deepEqual(await mixedWork(),[64,128]);
  await page.locator('[name="multi-rank"]').selectOption('1');
  assert.deepEqual(await mixedWork(),[48,64]);
  await page.locator('[name="multi-rank"]').selectOption('4');
  assert.deepEqual(await mixedWork(),[96,256]);
  await page.locator('[name="multi-restore"]').selectOption('wrong');
  assert.equal(await page.locator('.wrong-row').count(),2);
  assert.deepEqual(await page.locator('.wrong-row').allTextContents(),['Q(B)','R(A)']);
  assert.ok((await page.locator('.demo-result').innerText()).includes('错误写回'));
  await page.locator('[name="multi-rank"]').selectOption('2');
  await page.locator('[data-demo="multilora-rows"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'multilora-rows-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="multilora-rows"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'multilora-rows-mobile.png')});
  await page.locator('[name="multi-restore"]').selectOption('correct');
  assert.equal(await page.locator('.wrong-row').count(),0);

  // Architecture, sparse visibility and full-vocabulary loss workspace experiments.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M002','M003','M011']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.equal(await page.locator('.video-pending').count(),1);
   assert.equal(await page.locator('video').count(),0);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
  }
  await page.goto(pathToFileURL(path.join(root,'details','M002.html')).href);
  const architectureMiB=async()=>page.locator('[data-arch-mib]').evaluateAll(els=>els.map(e=>Number(e.dataset.archMib)));
  assert.deepEqual(await architectureMiB(),[2048,512,64,144]);
  assert.equal(await page.locator('.kv-head-map span').count(),32);
  await page.locator('[name="arch-kv"]').selectOption('1');
  assert.equal(await page.locator('[data-kv-head="0"]').count(),32);
  await page.locator('[name="arch-kv"]').selectOption('32');
  assert.equal(await page.locator('[data-kv-head="31"]').count(),1);
  await page.locator('[name="arch-length"]').selectOption('16384');
  await page.locator('[name="arch-byte"]').selectOption('1');
  assert.deepEqual(await architectureMiB(),[4096,1024,128,288]);
  await page.locator('[name="arch-length"]').selectOption('4096');
  await page.locator('[name="arch-byte"]').selectOption('2');
  await page.locator('[name="arch-kv"]').selectOption('8');
  await page.locator('#capacity').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'kv-architecture-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="kv-architecture"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'kv-architecture-mobile.png')});
  assert.ok(await page.locator('.structure-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M003.html')).href);
  const visibilityCounts=async()=>page.locator('[data-window-valid]').evaluate(e=>[Number(e.dataset.windowValid),Number(e.dataset.windowCover)]);
  assert.deepEqual(await visibilityCounts(),[21,28]);
  assert.equal(await page.locator('[data-window-visible="true"]').count(),21);
  await page.locator('[name="window-size"]').selectOption('1');
  assert.deepEqual(await visibilityCounts(),[8,16]);
  await page.locator('[name="window-size"]').selectOption('8');
  assert.deepEqual(await visibilityCounts(),[36,40]);
  await page.locator('[name="window-tile"]').selectOption('4');
  assert.deepEqual(await visibilityCounts(),[36,48]);
  await page.locator('[name="window-size"]').selectOption('3');
  assert.deepEqual(await visibilityCounts(),[21,48]);
  await page.locator('[name="window-tile"]').selectOption('1');
  assert.deepEqual(await visibilityCounts(),[21,21]);
  await page.locator('[name="window-tile"]').selectOption('2');
  await page.locator('[data-demo="sparse-window"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'sparse-window-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="sparse-window"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'sparse-window-mobile.png')});
  assert.ok(await page.locator('.sparse-window-grid .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M011.html')).href);
  const lossWorkspace=async()=>[Number(await page.locator('[data-loss-mib]').getAttribute('data-loss-mib')),Number(await page.locator('[data-loss-tiles]').getAttribute('data-loss-tiles'))];
  assert.deepEqual(await lossWorkspace(),[62.5,16]);
  await page.locator('[name="loss-vocab"]').selectOption('4096');
  assert.deepEqual(await lossWorkspace(),[2,512]);
  await page.locator('[name="loss-rows"]').selectOption('64');
  assert.deepEqual(await lossWorkspace(),[.5,2048]);
  await page.locator('[name="loss-rows"]').selectOption('4096');
  await page.locator('[name="loss-vocab"]').selectOption('128000');
  assert.deepEqual(await lossWorkspace(),[1000,1]);
  await page.locator('[name="loss-rows"]').selectOption('256');
  await page.locator('[name="loss-vocab"]').selectOption('32000');
  assert.deepEqual(await lossWorkspace(),[15.625,64]);
  await page.locator('#chunks').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'loss-workspace-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="loss-workspace"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'loss-workspace-mobile.png')});
  assert.ok(await page.locator('.structure-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));

  // Kernel experiments: reuse counts, global softmax normalization and expert tile coverage.
  await page.setViewportSize({width:1440,height:1050});
  for(const id of ['M006','M008','M010']){
   await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);
   assert.equal(await page.locator('.example-download a').count(),1);
   assert.ok((await page.locator('#sources').innerText()).includes('2026-10-10'));
   assert.equal(await page.locator('video').count(),0);
   assert.equal(await page.locator('.video-pending').count(),1);
  }
  await page.goto(pathToFileURL(path.join(root,'details','M006.html')).href);
  assert.equal(await page.locator('.gemm-output-grid span').count(),16);
  for(const [tile,reads] of [['2',64],['1',128],['4',32]]){
   await page.locator('[name="gemm-tile"]').selectOption(tile);
   assert.equal(Number(await page.locator('[data-gemm-reads]').getAttribute('data-gemm-reads')),reads);
   assert.ok((await page.locator('.demo-result').innerText()).includes('64次乘法和64次加法保持不变'));
  }
  assert.ok((await page.locator('.kernel-demo-table').innerText()).includes('192 B'));
  await page.locator('[name="gemm-tile"]').selectOption('2');
  await page.locator('#tiling').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'gemm-tiling-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="gemm-tiling"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'gemm-tiling-mobile.png')});
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M008.html')).href);
  const splitOutput=async()=>Number(await page.locator('[data-split-output]').getAttribute('data-split-output'));
  assert.ok(Math.abs(await splitOutput()-4.9)<1e-12);
  assert.ok((await page.locator('.kernel-demo-table').innerText()).includes('30.0%'));
  assert.ok((await page.locator('.kernel-demo-table').innerText()).includes('70.0%'));
  await page.locator('[name="kv-merge"]').selectOption('mean');
  assert.ok(Math.abs(await splitOutput()-167/42)<1e-12);
  assert.ok((await page.locator('.demo-result').innerText()).includes('直接平均不等价'));
  await page.locator('[name="kv-splits"]').selectOption('4');
  assert.equal(await splitOutput(),3.75);
  await page.locator('[name="kv-merge"]').selectOption('weighted');
  assert.ok(Math.abs(await splitOutput()-4.9)<1e-12);
  await page.locator('[name="kv-splits"]').selectOption('1');
  await page.locator('[name="kv-merge"]').selectOption('mean');
  assert.ok(Math.abs(await splitOutput()-4.9)<1e-12);
  await page.locator('[name="kv-splits"]').selectOption('2');
  await page.locator('[name="kv-merge"]').selectOption('weighted');
  await page.locator('[data-demo="splitkv-merge"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'splitkv-merge-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="splitkv-merge"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'splitkv-merge-mobile.png')});
  assert.ok(await page.locator('.kernel-demo-table .article-table').evaluate(e=>e.scrollWidth<=e.clientWidth));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto(pathToFileURL(path.join(root,'details','M010.html')).href);
  const covered=async()=>page.locator('[data-grouped-rows]').evaluate(e=>[Number(e.dataset.groupedRows),Number(e.dataset.uniformRows)]);
  assert.deepEqual(await covered(),[10,16]);
  for(const [tile,n] of [['1',8],['4',12]]){
   await page.locator('[name="moe-tile"]').selectOption(tile);assert.deepEqual(await covered(),[n,16]);
  }
  await page.locator('[name="moe-counts"]').selectOption('balanced');
  assert.deepEqual(await covered(),[16,16]);
  await page.locator('[name="moe-tile"]').selectOption('2');
  assert.deepEqual(await covered(),[8,8]);
  await page.locator('[name="moe-counts"]').selectOption('skewed');
  await page.locator('#padding').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'grouped-moe-desktop.png')});
  await page.setViewportSize({width:390,height:1050});
  await page.locator('[data-demo="grouped-rows"]').evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(output,'grouped-moe-mobile.png')});

  const widths=[];for(const id of [...ready,...Object.keys(foundations)]){await page.goto(pathToFileURL(path.join(root,'details',id+'.html')).href);if(ready.includes(id)){assert.equal(await page.locator('article[data-status="ready"]').count(),1);assert.equal(await page.locator('.prerequisites a').count(),prereqMap[id].length);assert.ok((await page.locator('article').innerText()).length>1000);assert.ok(await page.locator('article .inline-sources').count());assert.ok(await page.locator('article .code-example').count());}for(const width of [1440,820,390,320]){await page.setViewportSize({width,height:1050});const dims=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert.ok(dims.scroll<=dims.width,`${id} overflow ${JSON.stringify(dims)}`);widths.push({id,...dims});}}
  assert.equal(methods.filter(m=>!articles[m.id]).length,0);
  // Mobile directory and keyboard dismissal.
  await page.goto(pathToFileURL(path.join(root,'details','M007.html')).href);await page.locator('#menu-toggle').click();assert.ok(await page.locator('#directory').isVisible());await page.keyboard.press('Escape');assert.ok(!(await page.locator('#directory').isVisible()));await page.screenshot({path:path.join(output,'pages-article-mobile.png')});
  await page.goto(url);await page.locator('#reset-filters').click();for(const width of [1440,820,390,320]){await page.setViewportSize({width,height:1050});const dims=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert.ok(dims.scroll<=dims.width,'Overview overflow '+JSON.stringify(dims));widths.push({id:'overview',...dims});}await page.screenshot({path:path.join(output,'pages-overview-mobile.png')});
  await page.locator('#dimension-filter').selectOption('communication');const before=await page.locator('.method-row:visible').count();await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));assert.equal(await page.locator('.method-row:visible').count(),47);await page.evaluate(()=>window.dispatchEvent(new Event('afterprint')));assert.equal(await page.locator('.method-row:visible').count(),before);
  await page.goto(url+'#M016');assert.ok(await page.locator('#row-M016').isVisible());assert.equal(await page.locator('#dimension-filter').inputValue(),'all');
  // The documentation home and global search navigate to real independent articles.
  await page.setViewportSize({width:1440,height:1050});await page.goto(pathToFileURL(path.join(root,'index.html')).href);assert.equal(await page.locator('.reading-grid>a').count(),ready.length);assert.equal(await page.locator('.foundation-list>a').count(),Object.keys(foundations).length);await page.screenshot({path:path.join(output,'site-home.png')});
  await page.keyboard.press('Control+k');assert.ok(await page.locator('#search-dialog').isVisible());await page.locator('#global-search').fill('MC2');assert.ok(await page.locator('#search-results a[href="details/M027.html"]').isVisible());await page.locator('#search-results a[href="details/M027.html"]').click();assert.ok(page.url().endsWith('M027.html'));assert.equal(await page.locator('.video-pending').count(),1);assert.equal(await page.locator('video').count(),0);
  await page.locator('#open-search').click();await page.locator('#global-search').fill('HBM');assert.ok(await page.locator('#search-results a[href="../details/F002.html"]').count());await page.keyboard.press('Escape');assert.ok(!await page.locator('#search-dialog').isVisible());
  for(const width of [1440,820,390,320]){await page.goto(pathToFileURL(path.join(root,'index.html')).href);await page.setViewportSize({width,height:1050});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Home overflow');}
  await page.screenshot({path:path.join(output,'site-home-mobile.png')});const legacyEntry=path.resolve(root,'../llm-inference-training-two-tracks.html');if(fs.existsSync(legacyEntry)){await page.goto(pathToFileURL(legacyEntry).href+'#M016');await page.waitForURL('**/overview.html#M016');assert.ok(await page.locator('#row-M016').isVisible());}
  assert.deepEqual(errors,[]);console.log(JSON.stringify({pages:files.length,ready:ready.length,foundations:Object.keys(foundations).length,pending:47-ready.length,localLinksChecked:linkCount,interactions:'video-first layout, MP4 playback and chapters, global search and routes, home, filters, linked prerequisites, foundation links, softmax steps, formulas, demos, mobile menu, old bookmarks, print restore passed',responsiveChecks:widths.length+4,errors,screenshots:output},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
