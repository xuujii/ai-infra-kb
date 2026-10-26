// Check the exported website as a GitHub Pages project at /ai-infra-kb/.
// Case-sensitive names and decoded non-ASCII paths are checked even on Windows.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'dist'),prefix='/ai-infra-kb/',base='https://pages.example.invalid'+prefix;
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const files=walk(root),relative=f=>path.relative(root,f).split(path.sep).join('/');
const names=new Set(files.map(relative)),html=files.filter(f=>f.endsWith('.html'));
const markup=f=>fs.readFileSync(f,'utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'');
const anchors=new Map(html.map(f=>[relative(f),new Set([...markup(f).matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]))]));
let links=0,bytes=0;
for(const file of files){
 const name=relative(file),size=fs.statSync(file).size;bytes+=size;
 assert.ok(size<100*1024*1024,name+' exceeds normal GitHub file size');
 assert.ok(!/(^|\/)(node_modules|\.git|\.qa|audio)(\/|$)|(^|\/)\.env|\.wav$|\.log$|\.zip$|\.cjs$|\.ps1$|\.rendering\.mp4$/.test(name),'Unexpected publication file: '+name);
 if(/\.(html|md|json|py|vtt|srt)$/.test(name)){
  const text=fs.readFileSync(file,'utf8');
  assert.ok(!/[A-Z]:[\\/]Users[\\/]|file:\/\/\/[A-Z]:|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(text),'Local path or credential-like data: '+name);
 }
 if(!name.endsWith('.html'))continue;
 const page=markup(file);
 for(const [,raw] of page.matchAll(/\b(?:href|src|poster)="([^"]+)"/g)){
  const href=raw.replace(/&amp;/g,'&');
  if(/^(?:https?:|mailto:|data:)/i.test(href))continue;
  const url=new URL(href,base+name),decoded=decodeURIComponent(url.pathname);
  assert.equal(url.origin,new URL(base).origin,name+': unexpected origin');
  assert.ok(decoded.startsWith(prefix),name+': escaped project path '+href);
  const target=decoded.slice(prefix.length);
  assert.ok(names.has(target),name+': missing or wrongly cased '+href);
  if(url.hash)assert.ok(anchors.get(target)?.has(decodeURIComponent(url.hash.slice(1))),name+': missing anchor '+href);
  links++;
 }
}
const methods=require('./methods.json'),articles=require('./article-content.cjs'),{pages:foundations}=require('./foundations.cjs');
assert.equal(html.filter(f=>/^details\/M\d+\.html$/.test(relative(f))).length,methods.length);
for(const m of methods)assert.ok(names.has('details/'+m.id+'.html'));
for(const [id,v] of Object.entries(require('./videos.json'))){
 for(const key of ['src','poster','subtitles','transcript','timeline'])if(v[key])assert.ok(names.has(v[key]),id+': missing '+key);
 assert.ok(fs.readFileSync(path.join(root,'details',id+'.html'),'utf8').includes('../'+v.src),id+': video not embedded');
}
assert.ok(bytes<1024**3,'Published site exceeds Pages size limit');
console.log(JSON.stringify({files:files.length,pages:html.length,methods:methods.length,articles:Object.keys(articles).length,foundations:Object.keys(foundations).length,projectLinksChecked:links,totalMiB:Number((bytes/1024**2).toFixed(2))},null,2));
