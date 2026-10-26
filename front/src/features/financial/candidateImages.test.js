import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { test } from 'node:test';
import { candidateImage } from './pages/recommendations/candidatePresentation.js';

const catalog = JSON.parse(readFileSync(new URL('../../../../data/vehicles/candidate-catalog-specifications-v1.json', import.meta.url), 'utf8'));

test('추천 가능한 모든 차량 사양이 실제 로컬 이미지로 연결된다', () => {
  for (const vehicle of catalog) {
    const image = candidateImage(vehicle);
    assert.ok(image, `${vehicle.brand} ${vehicle.model}: 이미지 누락`);
    assert.ok(existsSync(new URL(`../../../public${image.src}`, import.meta.url)), `${image.src}: 파일 누락`);
  }
});

test('전기차·GT·왜건을 다른 외형 이미지와 혼동하지 않는다', () => {
  for (const [brand, first, second] of [
    ['기아', '레이', '레이 EV'], ['기아', 'EV3', 'EV3 GT'],
    ['현대', '코나', '코나 Electric'], ['제네시스', 'G80', 'Electrified G80'],
    ['BMW', '3시리즈', '3시리즈 투어링'],
  ]) {
    assert.notEqual(candidateImage({ brand, model: first }).src, candidateImage({ brand, model: second }).src);
  }
  assert.equal(candidateImage({ brand: '미등록 브랜드', model: 'K5' }), undefined);
});
