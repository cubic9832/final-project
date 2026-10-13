import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../../api/client.js';
import { getVehicles, selectPresetVehicles } from './vehicleApi.js';

const row = { id: 42, brand: '현대', name: '아반떼 하이브리드', trimName: '스마트', modelYear: 2026, conditionCode: 'NEW', classCode: 'COMPACT_SEDAN', fuelCode: 'HYBRID', price: 25550000, efficiencyValue: 21.1, efficiencyUnit: 'km/L', sourceUrl: 'https://www.hyundai.com/price.pdf' };

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

test('preset selects database IDs once each when multiple trims share a model', () => {
  const vehicles = [{ id: '12', name: '현대 아반떼 하이브리드' }, { id: '15', name: '현대 아반떼 하이브리드' }, { id: '3', name: '기아 레이' }, { id: '8', name: '기아 모닝' }];
  assert.deepEqual(selectPresetVehicles(['avante', 'ray', 'morning'], vehicles), ['12', '3', '8']);
});
