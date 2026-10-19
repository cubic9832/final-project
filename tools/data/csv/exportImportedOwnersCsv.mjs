import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households/synthetic/imported-owners');
const domestic=path.resolve(repositoryRoot, 'data/households/synthetic/owner-funded');
for(const [input,output,template] of [
  ['learning-rows.json','수입차_보유자_재무특성_학습데이터.csv','learning-rows.json'],
  ['purchase-audit.json','수입차_트림옵션_구매자금내역.csv','purchase-audit.json'],
  ['owner-group-summary.json','수입차별_보유자특성_요약.csv','owner-group-summary.json']]) {
  const rows=JSON.parse(await fs.readFile(path.join(root,input),'utf8'));
  const sample=JSON.parse(await fs.readFile(path.join(domestic,template),'utf8'))[0];
  const keys=Object.keys(sample);const chunks=[];
  if(rows.some(row=>JSON.stringify(Object.keys(row))!==JSON.stringify(keys)))throw Error('Schema differs from domestic file');
  for(let offset=0;offset<rows.length;offset+=1500) {
    const matrix=[keys,...rows.slice(offset,offset+1500).map(r=>keys.map(k=>r[k]??null))];
    const values = matrix;
    chunks.push(values.slice(offset===0?0:1).map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n'));
  }
  await fs.writeFile(path.join(root,output),'\ufeff'+chunks.join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({output,rows:rows.length,columns:keys.length}));
}
