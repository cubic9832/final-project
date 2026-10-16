from typing import NamedTuple

RULE_VERSION = "datagen-1.0.0"
LABEL_BASIS = "가상_보유자집단_분포"
SYNTHETIC = "예"
INCOME_CHANGED = "예"
TAKEHOME_RATE = 0.82
REGISTRATION_RATE = 0.07
MONEY_UNIT = 1000


class Field(NamedTuple):
    name: str
    kind: str


# 컬럼을 추가할 때는 아래에 Field를 넣는다.
# driver는 시드 분포에서 샘플링하고, derived는 다른 값으로 계산한다.
# CSV 헤더 순서는 이 튜플 순서를 따른다.
OWNER_SCHEMA = (
    Field("프로필_식별자", "identifier"),
    Field("나이_세", "driver"),
    Field("연령대", "derived"),
    Field("성별", "driver"),
    Field("직업_유형", "driver"),
    Field("경력_년", "driver"),
    Field("경력_구분", "derived"),
    Field("가구원수_명", "driver"),
    Field("부양인원_명", "driver"),
    Field("개인_연간세전소득_원", "driver"),
    Field("개인_평균월실수령소득_원", "derived"),
    Field("가구_평균월실수령소득_원", "derived"),
    Field("개인_현금성자산_원", "driver"),
    Field("개인_기타금융자산_원", "driver"),
    Field("개인_주거보증금자산_원", "driver"),
    Field("개인_부동산자산_원", "driver"),
    Field("개인_총자산_차량제외_원", "derived"),
    Field("개인_대출잔액_원", "derived"),
    Field("개인_순자산_차량제외_원", "derived"),
    Field("개인_평균월주거비_원", "driver"),
    Field("개인_평균월기타생활소비_원", "driver"),
    Field("개인_평균월소비합계_원", "derived"),
    Field("개인_평균월대출상환액_원", "derived"),
    Field("개인_평균월저축액_원", "driver"),
    Field("개인_월잔여액_원", "derived"),
    Field("차량_이용목적", "driver"),
    Field("연간_주행거리_km", "driver"),
    Field("보유차량_라벨코드", "driver"),
    Field("보유차량_브랜드", "derived"),
    Field("보유차량_모델", "derived"),
    Field("보유차량_차체", "derived"),
    Field("보유차량_차급", "derived"),
    Field("데이터_구분", "driver"),
    Field("합성데이터_여부", "derived"),
    Field("라벨_근거", "derived"),
    Field("생성규칙_버전", "derived"),
    Field("난수_시드", "derived"),
)

PURCHASE_SCHEMA = (
    Field("프로필_식별자", "identifier"),
    Field("차량사양_식별자", "identifier"),
    Field("기존_모델", "driver"),
    Field("구매_모델", "derived"),
    Field("연식_표기", "driver"),
    Field("파워트레인", "driver"),
    Field("연료", "driver"),
    Field("트림", "driver"),
    Field("기본가격_원", "driver"),
    Field("선택옵션", "driver"),
    Field("옵션가격_원", "driver"),
    Field("옵션포함가격_원", "derived"),
    Field("등록비_가정_원", "derived"),
    Field("총구매비용_가정_원", "derived"),
    Field("본인구매자금_원", "derived"),
    Field("가족지원금_가정_원", "derived"),
    Field("차량할부원금_원", "derived"),
    Field("구매직전_현금_원", "derived"),
    Field("구매직후_현금_원", "derived"),
    Field("구매당시_연간세전소득_가정_원", "derived"),
    Field("현재_개인연간세전소득_원", "derived"),
    Field("소득변화_가정", "derived"),
    Field("할부기간_개월", "driver"),
    Field("차량할부_연금리_가정", "driver"),
    Field("차량_월원금상환액_원", "derived"),
    Field("차량_월이자_원", "derived"),
    Field("차량_월상환액_원", "derived"),
    Field("기존대출잔액_보정후_원", "driver"),
    Field("기존월상환액_보정후_원", "derived"),
    Field("기존월상환액_보정전_원", "derived"),
    Field("기존대출잔액_보정전_원", "driver"),
    Field("옵션수집범위", "driver"),
    Field("기본가격_출처_URL", "driver"),
    Field("기본가격_출처_페이지", "driver"),
)

SUMMARY_SCHEMA = (
    Field("차량_라벨코드", "derived"),
    Field("모델", "derived"),
    Field("차체", "derived"),
    Field("차급", "derived"),
    Field("보유자수", "derived"),
    Field("평균나이_세", "derived"),
    Field("연간세전소득_중앙값_원", "derived"),
    Field("연간세전소득_10백분위_원", "derived"),
    Field("연간세전소득_90백분위_원", "derived"),
    Field("평균현금성자산_원", "derived"),
    Field("평균월소비_원", "derived"),
    Field("평균월대출상환액_원", "derived"),
    Field("최빈연령대", "derived"),
    Field("최빈이용목적", "derived"),
)


def column_names(schema: tuple[Field, ...]) -> list[str]:
    return [field.name for field in schema]
