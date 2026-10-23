import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

const root = path.resolve(repositoryRoot, 'data/vehicles');
const output = path.join(root, 'csv');
const manifest = JSON.parse(await fs.readFile(path.join(root, 'official-model-manifest.json'), 'utf8'));
const sample = JSON.parse(await fs.readFile(path.join(root, 'domestic-new-vehicles-2026-10-14.json'), 'utf8'));
const uniqueDocs = new Map();
for (const model of manifest.models) {
  for (const doc of model.documents) {
    const key = doc.url + (doc.postFileKey ?? '');
    if (!uniqueDocs.has(key)) uniqueDocs.set(key, { ...doc, brands: new Set(), models: new Set() });
    uniqueDocs.get(key).brands.add(model.brand);
    uniqueDocs.get(key).models.add(model.model);
  }
}
const status = value => ({ extracted: '추출 완료', failed: '수집 실패', 'sources-extracted': '등록 자료 추출 완료', incomplete: '일부 자료 누락' }[value] ?? value);
const kind = value => ({ price: '가격표', catalog: '카탈로그', 'shared-price': '종합 가격표', 'price-page': '가격 웹페이지', 'model-page': '모델 웹페이지' }[value] ?? value);
const modelRows = [['브랜드','모델 표기','차량 상태','자료 수집 상태','등록 자료 수','성공 자료 수','확인일','공식 모델 URL','사양 연결 검증 상태'],
  ...manifest.models.map(m => [m.brand,m.model,'신차',status(m.status),m.documents.length,m.documents.filter(d => d.status === 'extracted').length,m.checkedOn,m.modelUrl,'전체 트림 미검증'])];
const specificationRows = [['브랜드','모델','트림','차량 상태','연식','연료','가격_원','휠_인치','배기량_cc','복합연비_km_per_L','도심연비_km_per_L','고속도로연비_km_per_L','출처_URL','확인일','문서판본','가격기준','연비기준'],
  ...sample.vehicles.map(v => [v.brand,v.model,v.trim,'신차',v.modelYear,{GASOLINE:'가솔린',HYBRID:'하이브리드'}[v.fuel] ?? v.fuel,v.priceWon,v.wheelInches,v.displacementCc,v.combinedKmPerLiter,v.cityKmPerLiter,v.highwayKmPerLiter,v.sourceUrl,v.checkedOn,v.documentEdition,v.fuel === 'HYBRID' ? '세제혜택 후 기본 판매가; 옵션·취득세·등록비·탁송료 제외' : '기본 판매가; 옵션·취득세·등록비·탁송료 제외',v.model==='셀토스' && v.wheelInches===19 ? '2WD; 19인치 빌트인 캠 통합 신고값' : (v.model==='셀토스' ? '2WD; 기본 휠; 빌트인 캠 미선택' : '기본 휠; 빌트인 캠 미선택')])];
const documentRows = [['자료_ID','브랜드','모델 표기 목록','자료 종류','추출 상태','확인일','출처_URL','다운로드_파일키','파일명','오류'],];
const pageRows = [['자료_ID','브랜드','모델 표기 목록','자료 종류','페이지','출처_URL','다운로드_파일키','확인일','원문','검증 상태']];
let id = 0;
for (const doc of uniqueDocs.values()) {
  const docId = `DOC${String(++id).padStart(3,'0')}`;
  const brands = [...doc.brands].join('; ');
  const models = [...doc.models].join('; ');
  documentRows.push([docId,brands,models,kind(doc.kind),status(doc.status),manifest.checkedOn,doc.url,doc.postFileKey ?? '',doc.filename ?? doc.url.split('/').at(-1),doc.error ?? '']);
  if (doc.status !== 'extracted') continue;
  const raw = JSON.parse(await fs.readFile(path.join(root,doc.extractedPath),'utf8'));
  const pages = raw.pages ?? [{page:null,text:raw.text ?? ''}];
  for (const page of pages) pageRows.push([docId,brands,models,kind(doc.kind),page.page,doc.url,doc.postFileKey ?? '',manifest.checkedOn,page.text,'원문 추출; 사양 연결 전']);
}

await fs.mkdir(output,{recursive:true});
for (const [filename,matrix] of [['domestic-new-models.csv',modelRows],['verified-vehicle-specifications.csv',specificationRows],['official-source-documents.csv',documentRows],['official-source-pages.csv',pageRows]]) {
  const values = matrix;
  const csv = values.map(row => row.map(v => '"' + String(v ?? '').replaceAll('"','""') + '"').join(',')).join('\r\n') + '\r\n';
  await fs.writeFile(path.join(output,filename),'\ufeff'+csv,'utf8');
  console.log(JSON.stringify({file:filename,rows:matrix.length-1,columns:matrix[0].length}));
}
