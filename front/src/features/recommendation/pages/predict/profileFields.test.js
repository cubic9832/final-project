import test from 'node:test';
import assert from 'node:assert/strict';
import { emptyProfile, numericFields, toModelProfile, validateProfile } from './profileFields.js';

function validValues() {
  return { ...Object.fromEntries(numericFields.map(({ key, min = 0 }) => [key, String(Math.max(min, 1))])),
    '성별': '남성', '직업_유형': '근로자', '차량_이용목적': '여가' };
}

test('money inputs convert ten-thousand won to won without changing yearly or monthly meaning', () => {
  const values = { ...validValues(), '개인_연간세전소득_원': '5000', '개인_평균월저축액_원': '50.25', '나이_세': '30' };
  assert.deepEqual(validateProfile(values), {});
  const profile = toModelProfile(values);
  assert.equal(profile['개인_연간세전소득_원'], 50000000);
  assert.equal(profile['개인_평균월저축액_원'], 502500);
  assert.equal(profile['나이_세'], 30);
  assert.equal(profile['성별'], '남성');
});

test('blank, nonfinite, negative and fractional count inputs cannot be submitted', () => {
  assert.ok(Object.keys(validateProfile(emptyProfile)).length > 0);
  const errors = validateProfile({ ...validValues(), '개인_현금성자산_원': '-1', '개인_연간세전소득_원': 'Infinity', '가구원수_명': '1.5' });
  assert.ok(errors['개인_현금성자산_원']);
  assert.ok(errors['개인_연간세전소득_원']);
  assert.ok(errors['가구원수_명']);
});
