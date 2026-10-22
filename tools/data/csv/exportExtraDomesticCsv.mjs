import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households/synthetic/domestic-extra-90000');
const templateRoot=path.resolve(repositoryRoot, 'data/households/synthetic/owner-funded');
for(const [input,output] of [['learning-rows.json','국내차_보유자_추가90000_학습데이터.csv'],['purchase-audit.json','국내차_추가90000_트림옵션_구매자금내역.csv'],['owner-group-summary.json','국내차_추가90000_보유자특성_요약.csv']]) {
  const rows=JSON.parse(await fs.readFile(path.join(root,input),'utf8'));
  const template=JSON.parse(await fs.readFile(path.join(templateRoot,input),'utf8'))[0];
  const keys=Object.keys(template);const chunks=[];
  for(let offset=0;offset<rows.length;offset+=1500) {
    const part=rows.slice(offset,offset+1500);
    if(part.some(r=>JSON.stringify(Object.keys(r))!==JSON.stringify(keys)))throw Error('Schema mismatch');
    const matrix=[keys,...part.map(r=>keys.map(k=>r[k]??null))];
    const values = matrix;
    chunks.push(values.slice(offset===0?0:1).map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n'));
    if((offset+part.length)%15000===0)console.log(JSON.stringify({output,processed:offset+part.length}));
  }
  await fs.writeFile(path.join(root,output),'\ufeff'+chunks.join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({saved:output,rows:rows.length,columns:keys.length}));
}
