import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../../shared/api/client.js';
import { getVehicles, searchVehicleIds, selectPresetVehicles, toVehicle } from './vehicleApi.js';

const row = { id: 42, brand: '현대', name: '아반떼 하이브리드', trimName: '스마트', modelYear: 2026, conditionCode: 'NEW', classCode: 'COMPACT_SEDAN', fuelCode: 'HYBRID', price: 25550000, efficiencyValue: 21.1, efficiencyUnit: 'km/L', sourceUrl: 'https://www.hyundai.com/price.pdf' };

test('catalog images use local WebP for examples and missing photos while preserving user photos', () => {
  assert.equal(toVehicle(row).imageUrl, '/images/recommendations/cutouts/avante.webp');
  assert.equal(toVehicle({ ...row, isExample: true, imageUrl: 'https://manufacturer.example/old.jpg' }).imageUrl, '/images/recommendations/cutouts/avante.webp');
  assert.equal(toVehicle({ ...row, isExample: false, imageUrl: '/uploads/my-car.jpg' }).imageUrl, '/uploads/my-car.jpg');
  assert.equal(toVehicle({ ...row, brand: '미등록', imageUrl: '/uploads/other.jpg', isExample: true }).imageUrl, '/uploads/other.jpg');
});

test('API catalog converts won to screen units and excludes incompatible running costs', async () => {
  const adapter = client.defaults.adapter;
  client.defaults.adapter = async (config) => {
    assert.equal(config.url, '/vehicles');
    return { data: { data: [row, { ...row, id: 43, fuelCode: 'ELECTRIC', efficiencyUnit: 'km/kWh' }, { ...row, id: 44, efficiencyValue: null }] }, status: 200, config };
  };
  try {
    const vehicles = await getVehicles();
    assert.equal(vehicles.length, 1);
    assert.equal(vehicles[0].price, 2555);
    assert.equal(vehicles[0].id, '42');
    assert.equal(vehicles[0].sourceUrl, row.sourceUrl);
  } finally { client.defaults.adapter = adapter; }
});

test('API failures propagate instead of returning sample vehicles', async () => {
  const adapter = client.defaults.adapter;
  client.defaults.adapter = async () => { throw new Error('offline'); };
  try { await assert.rejects(getVehicles(), /offline/); }
  finally { client.defaults.adapter = adapter; }
});

test('keyword search sends q and returns relevance-ordered IDs as screen IDs', async () => {
  const adapter = client.defaults.adapter;
  client.defaults.adapter = async (config) => {
    assert.equal(config.url, '/vehicles');
    assert.deepEqual(config.params, { q: '현대 하이브리드' });
    return { data: { data: [{ ...row, id: 7 }, { ...row, id: 3 }] }, status: 200, config };
  };
  try { assert.deepEqual(await searchVehicleIds('현대 하이브리드'), ['7', '3']); }
  finally { client.defaults.adapter = adapter; }
});

test('preset selects database IDs once each when multiple trims share a model', () => {
  const vehicles = [{ id: '12', name: '현대 아반떼 하이브리드' }, { id: '15', name: '현대 아반떼 하이브리드' }, { id: '3', name: '기아 레이' }, { id: '8', name: '기아 모닝' }];
  assert.deepEqual(selectPresetVehicles(['avante', 'ray', 'morning'], vehicles), ['12', '3', '8']);
});
