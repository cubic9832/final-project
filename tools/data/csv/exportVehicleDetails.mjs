import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root=path.resolve(repositoryRoot, 'data/vehicles');
const data=JSON.parse(await fs.readFile(path.join(root,'normalized-vehicle-details.json'),'utf8'));
const shared=[['brand','브랜드'],['model','모델'],['powertrain','엔진_파워트레인'],['fuel','연료']];
const price=[...shared,['model_year','연식'],['trim','트림'],['price_won','판매가격_원'],
  ['price_before_tax_benefit_won','세제혜택전가격_원'],['price_after_tax_benefit_won','세제혜택후가격_원'],
  ['price_basis','가격기준'],['default_wheel_inches','기본휠_인치'],['wheel_basis','기본휠근거']];
const efficiency=[['drive','구동방식'],['wheel_inches','휠사양_인치'],['seating_capacity','좌석수'],['displacement_cc','배기량_cc'],
  ['combined_efficiency','복합연비_전비'],['city_efficiency','도심연비_전비'],['highway_efficiency','고속도로연비_전비'],
  ['efficiency_unit','연비_전비단위'],['curb_weight_kg','공차중량_kg'],['range_combined_km','복합주행거리_km'],
  ['range_city_km','도심주행거리_km'],['range_highway_km','고속도로주행거리_km']];
const source=[['source_url','출처_URL'],['source_page','출처페이지'],['source_file_key','출처파일키'],['checked_on','확인일']];
const outputs=[
  ['domestic-vehicle-details.csv',data.vehicle_details,[...price,...efficiency,
    ['join_status','가격_연비연결상태'],...source,['efficiency_source_url','연비출처_URL'],['efficiency_source_page','연비출처페이지']]],
  ['domestic-trim-prices.csv',data.trim_prices,[...price,...source,['verification','검증상태'],['price_evidence','가격표근거']]],
  ['domestic-efficiency-specifications.csv',data.efficiency_configurations,[...shared,['configuration','연비사양'],...efficiency,
    ...source,['verification','검증상태'],['evidence','제원표근거']]],
];
for (const [name,rows,columns] of outputs) {
  const matrix=[columns.map(([,label])=>label),...rows.map(row=>columns.map(([key])=>row[key]??null))];
  const values = matrix;
  const csv=values.map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
  await fs.writeFile(path.join(root,'csv',name),'\ufeff'+csv,'utf8');
  console.log(JSON.stringify({file:name,rows:rows.length,columns:columns.length}));
}
const stats={priceRows:data.trim_prices.length,efficiencyRows:data.efficiency_configurations.length,
  joinedRows:data.vehicle_details.filter(row=>row.join_status.includes('1건')).length,
  joinedWithPayablePrice:data.vehicle_details.filter(row=>row.join_status.includes('1건')&&row.price_won!==null).length,
  pricesMissing:data.trim_prices.filter(row=>row.price_won===null).length,
  priceModels:new Set(data.trim_prices.map(row=>row.brand+'|'+row.model)).size};
await fs.writeFile(path.join(root,'detail-statistics.json'),JSON.stringify(stats,null,2));
console.log(JSON.stringify(stats));
