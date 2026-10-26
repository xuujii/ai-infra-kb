(()=>{
 const rows=[...document.querySelectorAll('.method-row')];
 const search=document.getElementById('search');
 const phase=document.getElementById('phase-filter'),dimension=document.getElementById('dimension-filter'),kind=document.getElementById('kind-filter'),status=document.getElementById('status-filter');
 const normalize=text=>text.normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
 const haystacks=new Map(rows.map(row=>[row,normalize(row.dataset.search)]));
 function filter(){const words=normalize(search.value).split(' ').filter(Boolean);let count=0;rows.forEach(row=>{const ok=words.every(word=>haystacks.get(row).includes(word))&&(phase.value==='all'||row.dataset.phases.split(' ').includes(phase.value))&&(dimension.value==='all'||row.dataset.tags.split(' ').includes(dimension.value))&&(kind.value==='all'||row.dataset.kind===kind.value)&&(status.value==='all'||row.dataset.status===status.value);row.hidden=!ok;if(ok)count++;});document.getElementById('result-count').textContent=`${count} / ${rows.length} 个方法`;document.getElementById('empty').hidden=count!==0;document.querySelectorAll('[data-open-dimension]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.openDimension===dimension.value)));save();}
 function reset(){search.value='';[phase,dimension,kind,status].forEach(el=>el.value='all');filter();}
 function save(){try{sessionStorage.setItem('ai-infra-overview-filters',JSON.stringify({search:search.value,phase:phase.value,dimension:dimension.value,kind:kind.value,status:status.value}));}catch{}}
 try{const saved=JSON.parse(sessionStorage.getItem('ai-infra-overview-filters'));if(saved){search.value=saved.search||'';[[phase,'phase'],[dimension,'dimension'],[kind,'kind'],[status,'status']].forEach(([el,key])=>{if([...el.options].some(o=>o.value===saved[key]))el.value=saved[key];});}}catch{}
 search.addEventListener('input',filter);[phase,dimension,kind,status].forEach(el=>el.addEventListener('change',filter));document.getElementById('reset-filters').addEventListener('click',reset);document.getElementById('empty-reset').addEventListener('click',reset);
 function reveal(id){
  if(/^M\d{3}$/.test(id))id='row-'+id;
  const target=document.getElementById(id);if(!target)return;
  if(target.classList.contains('method-row')&&target.hidden)reset();
  for(let el=target.parentElement;el;el=el.parentElement)if(el.tagName==='DETAILS')el.open=true;
  target.tabIndex=-1;target.focus({preventScroll:true});requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'auto'}));
 }
 document.addEventListener('click',e=>{const a=e.target.closest('a[href^="#"]');if(!a)return;const id=a.getAttribute('href').slice(1);if(!document.getElementById(id))return;e.preventDefault();history.pushState(null,'','#'+id);reveal(id);});
 document.querySelectorAll('[data-open-dimension]').forEach(button=>button.addEventListener('click',()=>{reset();dimension.value=button.dataset.openDimension;filter();history.pushState(null,'','#catalog');reveal('catalog');}));
 document.getElementById('ready-only').addEventListener('click',()=>{reset();status.value='ready';filter();});
 window.addEventListener('hashchange',()=>reveal(decodeURIComponent(location.hash.slice(1))));window.addEventListener('popstate',()=>reveal(decodeURIComponent(location.hash.slice(1))));
 filter();if(location.hash)reveal(decodeURIComponent(location.hash.slice(1)));
 let printState;window.addEventListener('beforeprint',()=>{printState={details:[...document.querySelectorAll('details')].map(el=>[el,el.open]),hidden:rows.filter(row=>row.hidden)};printState.details.forEach(([el])=>el.open=true);rows.forEach(row=>row.hidden=false);document.getElementById('empty').hidden=true;});window.addEventListener('afterprint',()=>{if(!printState)return;printState.details.forEach(([el,open])=>el.open=open);rows.forEach(row=>row.hidden=printState.hidden.includes(row));filter();printState=null;});document.getElementById('print-btn').addEventListener('click',()=>window.print());
})();
