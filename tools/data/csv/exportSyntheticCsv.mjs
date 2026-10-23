import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households/synthetic/generated');
const tables=JSON.parse(await fs.readFile(path.join(root,'dataset.json'),'utf8'));
const korean=process.argv.includes('--korean');
const labels=korean?JSON.parse(await fs.readFile(path.join(root,'..','korean_labels.json'),'utf8')):null;
const outputDir=path.join(root,korean?'csv-ko':'csv');
const translate=(key,value)=>{
  if(!korean)return value??null;
  if(typeof value==='boolean')return value?'예':'아니오';
  if(labels.values[key]) {
    if(!Object.hasOwn(labels.values[key],value))throw Error(`Missing value translation ${key}: ${value}`);
    return labels.values[key][value];
  }
  return value??null;
};
await fs.mkdir(outputDir,{recursive:true});
for(const [name,rows] of Object.entries(tables)) {
  const columns=Object.keys(rows[0]);const chunks=[];
  if(korean&&columns.some(key=>!labels.columns[key]))throw Error(`Missing column translation ${name}`);
  const headers=columns.map(key=>korean?labels.columns[key]:key);
  if(new Set(headers).size!==headers.length)throw Error(`Duplicate headers ${name}`);
  for(let offset=0;offset<rows.length;offset+=2000) {
    const matrix=[headers,...rows.slice(offset,offset+2000).map(row=>columns.map(key=>translate(key,row[key])))];
    const values = matrix;
    chunks.push(values.slice(offset===0?0:1).map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(',')).join('\r\n'));
  }
  await fs.writeFile(path.join(outputDir,(korean?labels.files[name]:name)+'.csv'),'\ufeff'+chunks.join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({table:name,rows:rows.length,columns:columns.length}));
}
