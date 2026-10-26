// Produce only public website files; exclude development scripts and intermediate media.
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const root=__dirname,dest=path.join(root,'dist');
execFileSync(process.execPath,[path.join(root,'build.cjs'),'--no-legacy'],{stdio:'inherit'});
fs.mkdirSync(dest,{recursive:true});
function copy(relative){const source=path.join(root,relative),target=path.join(dest,relative);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);}
for(const f of ['index.html','overview.html','.nojekyll'])copy(f);
for(const f of fs.readdirSync(path.join(root,'details')))if(f.endsWith('.html'))copy('details/'+f);
for(const f of fs.readdirSync(path.join(root,'examples')))if(f.endsWith('.py'))copy('examples/'+f);
const videos=JSON.parse(fs.readFileSync(path.join(root,'videos.json'),'utf8'));
for(const v of Object.values(videos)){
 for(const key of ['src','poster','subtitles','transcript'])if(v[key])copy(v[key]);
 if(v.timeline)copy(v.timeline);
 const dir=path.dirname(v.src);if(fs.existsSync(path.join(root,dir,'index.html')))copy(dir+'/index.html');
}
console.log('Public website exported to '+dest);
