"""Render the reviewed official-lineup manifest; never writes to the database."""

import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / "data/vehicles/korea-official-models-20261027"
BASELINE = ROOT / "data/vehicles/catalog-expansion-round2-20261027"


def normalized_name(value):
    # Keep body, generation and powertrain tokens; only normalize typography.
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def write_rows(name, rows):
    (DIRECTORY / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (DIRECTORY / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_inventory():
    manifest = json.loads((DIRECTORY / "lineups.json").read_text(encoding="utf-8"))
    aliases = json.loads((BASELINE / "model-families.json").read_text(encoding="utf-8"))
    catalog = json.loads((BASELINE / "after.json").read_text(encoding="utf-8"))
    families = {
        aliases.get(f"{item['brand']}|{item['model']}", f"{item['brand']} {item['model']}")
        for item in catalog
    }
    overrides = json.loads((DIRECTORY / "name-aliases.json").read_text(encoding="utf-8"))
    family_index = {normalized_name(family): family for family in families}
    assert len(family_index) == len(families), "Ambiguous catalog family normalization"
    assert set(overrides.values()) <= families, "Alias must target an existing catalog family"
    rows = []
    for brand in manifest["brands"]:
        for model in brand["models"].split("|"):
            key = f"{brand['brand']} {model}"
            mapped = family_index.get(normalized_name(overrides.get(key, key)))
            rows.append({
                "brand": brand["brand"], "model_family": model,
                "verification": brand.get("verification", "OFFICIAL_KOREAN_LISTING"),
                "catalog_match": "FAMILY_PRESENT" if mapped else "NEW_FAMILY_CANDIDATE",
                "catalog_family": mapped or "",
                "match_method": "EXPLICIT_ALIAS" if key in overrides else "CASE_SPACE_NORMALIZED" if mapped and key != mapped else "EXACT" if mapped else "NO_CATALOG_EQUIVALENT",
                "source_url": brand["source"], "evidence_basis": brand["basis"],
                "checked_on": manifest["checked_on"],
            })
    assert len({(normalized_name(row["brand"]), normalized_name(row["model_family"])) for row in rows}) == len(rows)
    assert len({row["catalog_family"] for row in rows if row["catalog_family"]}) == sum(bool(row["catalog_family"]) for row in rows), "Multiple input rows map to the same family"
    assert all(row["source_url"].startswith("https://") for row in rows)
    write_rows("models", rows)
    new_rows = [row for row in rows if not row["catalog_family"]]
    write_rows("new-model-candidates", new_rows)
    write_rows("existing-model-matches", [row for row in rows if row["catalog_family"]])
    levels = Counter(row["verification"] for row in rows)
    present = sum(row["catalog_match"] == "FAMILY_PRESENT" for row in rows)
    lines = [
        "# 국내 공식 모델군 1차 목록 — 2026-10-27", "",
        f"공식 출처를 확보한 {len(manifest['brands'])}개 브랜드, {len(rows)}개 모델군 행이다. 국내 시장 전체 전수 목록은 아니다.", "",
        "## 검증 수준", "",
        f"- 국내 공식 메뉴·가격표·구성기 등재 확인: {levels['OFFICIAL_KOREAN_LISTING']}개",
        f"- 검색 색인으로만 확인하여 직접 재검증 필요: {levels['INDEX_ONLY']}개",
        f"- 현지화 소개 메뉴 확인, 국내 계약 가능 여부 추가 확인 필요: {levels['LOCALIZED_LINEUP']}개", "",
        "공식 등재가 실시간 주문·재고·납기를 보장하지 않는다. 모델군별 최신 가격표와 국내 계약 가능 여부를 확인한 뒤 수집 대상으로 확정한다.", "",
        "## 기존 카탈로그와 비교", "",
        f"기준은 round2 after.json의 {len(catalog)}개 구성, {len(families)}개 모델군이다. 중복 대조 후 {present}개 행은 기존 모델군이며, {len(new_rows)}개는 신규 모델군 후보다.", "",
        "신규 후보는 국내 판매·가격·제원까지 확정한 DB 투입 데이터가 아니다. FAMILY_PRESENT 역시 해당 모델의 모든 트림·가격대가 확보됐다는 의미가 아니다.", "",
        "## 중복 제거 결과", "",
        "기존 56개 연결·112개 미연결에서 영문 대소문자와 한글 대응 4개를 추가 확인했다. 공식 원본 168개 행은 보존하고 신규 후보 파일에서 기존 모델을 제외했다.", "",
        "|공식 목록 표기|기존 카탈로그|처리|", "|---|---|---|",
        "|GMC CANYON|GMC Canyon|대소문자 정규화|",
        "|GMC SIERRA|GMC Sierra|대소문자 정규화|",
        "|토요타 ALPHARD|토요타 알파드|명시적 영문·한글 별칭|",
        "|토요타 SIENNA|토요타 시에나|명시적 영문·한글 별칭|", "",
        f"신규 {len(new_rows)}개 중 국내 공식 목록 확인은 {sum(row['verification'] == 'OFFICIAL_KOREAN_LISTING' for row in new_rows)}개이며, 나머지는 검색 색인·현지화 소개 수준으로 국내 판매 확인이 더 필요하다.", "",
        "- `new-model-candidates.csv/json`: 기존 모델 제외 후 신규 수집 대상",
        "- `existing-model-matches.csv/json`: 기존 모델 연결 및 대응 방식",
        "- `name-aliases.json`: 검토한 이름 대응 규칙",
        "- 공식 목록 내부에서 정규화된 동일 이름 또는 같은 기존 모델군으로 중복 연결되는 행은 없음.",
        "- 브랜드를 넘어 이름을 합치거나 부분 문자열·유사도만으로 병합하지 않음.",
        "- G70 Shooting Brake, BMW 투어링, 쿠페·컨버터블 및 GLC/GLE Coupe 등 차체 파생형은 유지. 무쏘 EV, Escalade IQ, iX3 등 별도 모델 식별도 유지. 원본 목록의 파생형 통합 기준은 아래 참조.", "",
        "## 브랜드별 모델군과 공식 출처", "",
        "|브랜드|행 수|모델군|공식 출처|", "|---|---:|---|---|",
    ]
    for brand in manifest["brands"]:
        models = brand["models"].split("|")
        lines.append(f"|{brand['brand']}|{len(models)}|{', '.join(models)}|[공식 목록]({brand['source']})|")
    lines += ["", "## 미완료 범위", ""]
    for brand in manifest["pending_brands"]:
        lines.append(f"- {brand['brand']}: {brand['reason']}")
    lines += ["", "## 통합·제외 기준", ""]
    lines.extend(f"- {note}" for note in manifest["normalization_notes"])
    lines += ["", "## 다음 검수", "", "1. 미완료 브랜드의 국내 주문 가능 모델과 현재 가격표를 확보한다.", "2. 모델군별 차체·연료·좌석·최저/최고 가격을 공식 제원표로 확인한다.", "3. 기존 모델명을 수동 대응한 뒤 차체 × 가격대의 실제 빈 구간을 계산한다.", "4. 빈 구간을 채우는 모델·트림부터 가격·제원을 확보해 DB 추가 대상으로 검수한다.", "", "이번 작업은 목록 파일만 생성한다. DB·추천 조건·학습 모델은 변경하지 않는다.", ""]
    (DIRECTORY / "README.md").write_text("\n".join(lines), encoding="utf-8")
    with (DIRECTORY / "models.csv").open(encoding="utf-8-sig", newline="") as stream:
        assert list(csv.DictReader(stream)) == rows
    print(json.dumps({"brands": len(manifest["brands"]), "rows": len(rows), "levels": levels, "catalog_present": present}, ensure_ascii=False))


if __name__ == "__main__":
    build_inventory()
