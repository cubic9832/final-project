import registry from './newVehicleSales.json' with { type: 'json' };

const records = new Map(registry.vehicles.map(record => [record.identity.id, record]));
const identityKeys = ['id', 'brand', 'model', 'trim', 'year'];

// Router history can retain an older recommendation response after a refresh.
// Refresh only display evidence for an exact identity; preserve ranking inputs.
export function resolveVehicleSales(item) {
  const current = records.get(item.vehicle.id);
  if (!current || !identityKeys.every(key => (item.vehicle[key] ?? null) === (current.identity[key] ?? null))) {
    return { verification: item.salesVerification, specifications: item.specifications };
  }
  const specifications = item.specifications ? { ...item.specifications } : undefined;
  if (specifications) {
    for (const [field, key] of [['price_won', 'price'], ['model_year', 'year'], ['seats', 'seats']]) {
      const fact = current[key];
      specifications[field] = {
        value: fact.value ?? '미확인', status: fact.status, basis: fact.basis,
        sources: fact.sources.map(url => ({ url, publisher: '판매 정보' })),
      };
    }
  }
  return { verification: current, specifications };
}
