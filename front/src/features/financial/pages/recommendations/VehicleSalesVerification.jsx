const money = new Intl.NumberFormat('ko-KR');
export default function VehicleSalesVerification({ verification, vehicle }) {
  if (!verification) return <p>취향 참고용 · 판매 정보 확인 전 · 예산 적합성 미평가</p>;
  const price = verification.price;
  return <section className="vehicle-sales-verification" aria-label={`${vehicle.model} 판매 정보 확인 상태`}>
    {(verification.designation.value !== vehicle.model || verification.year.value) && <p>{verification.designation.value}{verification.year.value && ` · ${verification.year.value}년형`}</p>}
    <p>{verification.domestic.value}</p>
    <p>{price.value != null
      ? `${price.status === 'official-reference' ? '공식 시작가' : price.status === 'estimated-price' ? '추정 가격' : '참고 가격'} ${money.format(price.value)}원`
      : '가격 미확인 · 상세 확인 내용 참고'}</p>
    <p>취향 비교용 차량</p>

  </section>;
}
