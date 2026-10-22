import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households/synthetic/owner-funded');
for(const [input,output] of [['learning-rows.json','차량보유자_재무특성_보정학습데이터.csv'],['purchase-audit.json','보유차량_트림옵션_구매자금내역.csv'],['owner-group-summary.json','차량별_보유자특성_보정요약.csv']]) {
  const rows=JSON.parse(await fs.readFile(path.join(root,input),'utf8'));const keys=Object.keys(rows[0]);const chunks=[];
  for(let offset=0;offset<rows.length;offset+=1500) {
    const matrix=[keys,...rows.slice(offset,offset+1500).map(r=>keys.map(k=>r[k]??null))];
    const values = matrix;
    chunks.push(values.slice(offset===0?0:1).map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n'));
  }
  await fs.writeFile(path.join(root,output),'\ufeff'+chunks.join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({output,rows:rows.length,columns:keys.length}));
}
