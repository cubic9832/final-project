"""Summarize collection coverage and index evidence without guessing numeric joins."""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = (Path(__file__).resolve().parents[3] / 'data/vehicles')


def main():
    manifest = json.loads((ROOT / 'official-model-manifest.json').read_text(encoding='utf-8'))
    models = manifest['models']
    documents = {doc['extractedPath']: doc for model in models for doc in model['documents']
                 if doc.get('status') == 'extracted'}
    evidence = []
    for model in models:
        sections = []
        for doc in model['documents']:
            if doc.get('status') != 'extracted':
                continue
            raw = json.loads((ROOT / doc['extractedPath']).read_text(encoding='utf-8'))
            pages = raw.get('pages', [{'page': None, 'text': raw.get('text', '')}])
            for page in pages:
                lines = page['text'].splitlines()
                price = [(i, line) for i, line in enumerate(lines)
                         if re.search(r'\d{1,3}(?:,\d{3}){2}|\d,\d{3}만', line)]
                efficiency = [(i, line) for i, line in enumerate(lines)
                              if re.search(r'복합연비|정부 신고|표준연비|전비|km/ℓ|km/L|km/kWh|주행거리', line)]
                if price or efficiency:
                    sections.append({'kind': doc['kind'], 'sourceUrl': doc['url'],
                        'extractedPath': doc['extractedPath'], 'page': page['page'],
                        'priceEvidence': [{'line': i + 1, 'context': '\n'.join(lines[max(0, i - 3):i + 4])} for i, _ in price],
                        'efficiencyEvidence': [{'line': i + 1, 'context': '\n'.join(lines[max(0, i - 2):min(len(lines), i + 14)])} for i, _ in efficiency]})
        evidence.append({'brand': model['brand'], 'model': model['model'],
                         'verification': '사양 연결 전 원문 근거; 가격 후보에 옵션·공급가액도 포함될 수 있음',
                         'sections': sections})
    (ROOT / 'official-vehicle-evidence.json').write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    counts = Counter(model['brand'] for model in models)
    incomplete = [model for model in models if model['status'] != 'sources-extracted']
    page_count = sum(len(json.loads((ROOT / path).read_text(encoding='utf-8')).get('pages', [])) for path in documents)
    lines = ['# 국내 신차 공식 자료 수집 결과', '', f"확인일: {manifest['checkedOn']}", '',
             '중고차·상용 트럭·버스·택시 전용·통학 전용은 제외했다. 국내 판매 사이트의 브랜드 기준이며 모든 차량이 국내 생산이라는 뜻은 아니다.', '',
             f'- 모델 표기 {len(models)}개: 파워트레인·특별 모델·구형/신형 표기가 별도 항목일 수 있다.',
             f'- 중복 URL/다운로드 키를 제외한 원자료 {len(documents)}건, PDF {page_count}페이지를 추출했다.',
             f'- 모든 등록 자료 추출 성공: {len(models) - len(incomplete)}개 모델 표기.',
             '- 정규화 검증: 전체 트림의 가격·엔진·구동·휠·연비 연결은 아직 완료하지 않았다.',
             '- DB 자동 반영은 하지 않았다. 자료 추출 성공은 신차 계약 가능 여부를 보장하지 않는다.', '',
             '| 브랜드 | 모델 표기 수 |', '| --- | ---: |']
    lines += [f'| {brand} | {count} |' for brand, count in counts.items()]
    lines += ['', '## 자료가 누락되거나 실패한 모델', '']
    for model in incomplete:
        lines.append(f"- {model['brand']} {model['model']}")
        for doc in model['documents']:
            if doc.get('status') != 'extracted':
                lines.append(f"  - {doc['url']}: {doc.get('error', '미확인')}")
    lines += ['', '## 모델별 자료', '', '| 브랜드 | 모델 | 상태 | 자료 수 |', '| --- | --- | --- | ---: |']
    lines += [f"| {m['brand']} | {m['model']} | {m['status']} | {len(m['documents'])} |" for m in models]
    (ROOT / 'COLLECTION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'models': len(models), 'documents': len(documents), 'pdfPages': page_count,
                      'incomplete': len(incomplete)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
