import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households/synthetic/ownership');
const rows=JSON.parse(await fs.readFile(path.join(root,'learning-rows.json'),'utf8'));
const catalog=JSON.parse(await fs.readFile(path.join(root,'vehicle-label-catalog.json'),'utf8'));
const fuels={GASOLINE:'가솔린',HYBRID:'하이브리드',LPG:'LPG',DIESEL:'디젤'};
const catalogRows=catalog.map(v=>({'차량_라벨코드':v.label_id,'브랜드':v.brand,'모델':v.model,'연료':fuels[v.fuel],
  '대표_트림':v.trim,'차체_가정분류':v.body,'차급_가정분류':v.segment,'대표가격_원':v.price_won,
  '복합연비_km_L':v.combined_efficiency,'가격_출처_URL':v.source_url,'가격_출처_페이지':v.source_page,
  '연비_출처_URL':v.efficiency_source_url,'연비_출처_페이지':v.efficiency_source_page}));
for(const [name,records] of [['20~50대_조건별_가상보유차량_학습데이터.csv',rows],['차량_라벨_목록.csv',catalogRows]]) {
  if(process.argv.includes('--learning-only') && records===catalogRows)continue;
  const keys=Object.keys(records[0]);const chunks=[];
  for(let offset=0;offset<records.length;offset+=1500) {
    const matrix=[keys,...records.slice(offset,offset+1500).map(r=>keys.map(k=>r[k]??null))];
    const values = matrix;
    chunks.push(values.slice(offset===0?0:1).map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n'));
  }
  await fs.writeFile(path.join(root,name),'\ufeff'+chunks.join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({name,rows:records.length,columns:keys.length}));
}
