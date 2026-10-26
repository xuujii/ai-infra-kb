// Run the standalone CPU teaching examples; no accelerator or Python packages required.
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const python=process.env.AI_INFRA_PYTHON||(process.platform==='win32'?'python':'python3');
const examples=fs.readdirSync(path.join(__dirname,'examples')).filter(f=>f.endsWith('.py')).sort();
for(const file of examples){
 const result=spawnSync(python,[path.join(__dirname,'examples',file)],{encoding:'utf8',timeout:120000,windowsHide:true});
 if(result.error||result.status!==0){
  console.error(file,result.error?.message||result.stderr||result.stdout);process.exit(1);
 }
 console.log('PASS '+file);
}
console.log(JSON.stringify({examples:examples.length,hardwareTests:false}));
