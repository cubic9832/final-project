import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/households');
const data=JSON.parse(await fs.readFile(path.join(root,'official-household-statistics.json'),'utf8'));
const outputs={financial_profiles:'household-financial-profiles.csv',financial_metrics:'household-financial-metrics.csv',
  expenditure_profiles:'household-income-expenditure-quintiles.csv',expenditure_metrics:'household-income-expenditure-metrics.csv'};
await fs.mkdir(path.join(root,'csv'),{recursive:true});
for(const [key,name] of Object.entries(outputs)) {
  const rows=data[key];const columns=Object.keys(rows[0]);
  const matrix=[columns,...rows.map(row=>columns.map(column=>row[column]??null))];
  const values = matrix;
  const csv=values.map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
  await fs.writeFile(path.join(root,'csv',name),'\ufeff'+csv,'utf8');
  console.log(JSON.stringify({file:name,rows:rows.length,columns:columns.length}));
}
