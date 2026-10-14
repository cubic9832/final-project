// 모델 검증 지표 비교 막대 차트 (이전 버전 vs 현재 버전)
// 차트 라이브러리 없이 CSS 막대로 그린다. 막대에 마우스를 올리거나 Tab으로 이동하면 값이 보인다.
import './ModelMetricChart.css';

export default function ModelMetricChart({ metrics, previousLabel, currentLabel }) {
  // 막대 높이 기준: 0 ~ 1 (지표가 모두 0~1 범위)
  const toHeight = (value) => `${Math.round(value * 100)}%`;

  return (
    <figure className="metric-chart">
      <figcaption className="metric-chart-header">
        <strong>검증 지표 비교</strong>
        <span className="metric-chart-legend">
          <span><i className="metric-chart-swatch is-previous" aria-hidden="true" />{previousLabel}</span>
          <span><i className="metric-chart-swatch is-current" aria-hidden="true" />{currentLabel}</span>
        </span>
      </figcaption>

      <div className="metric-chart-plot" aria-hidden="true">
        {metrics.map((metric) => (
          <div className="metric-chart-group" key={metric.name}>
            <div className="metric-chart-bars">
              <span
                className="metric-chart-bar is-previous"
                style={{ height: toHeight(metric.previous) }}
                data-tooltip={`${previousLabel} ${metric.name} ${metric.previous.toFixed(2)}`}
              />
              <span
                className="metric-chart-bar is-current"
                style={{ height: toHeight(metric.current) }}
                data-tooltip={`${currentLabel} ${metric.name} ${metric.current.toFixed(2)}`}
              >
                {/* 현재 버전 값만 막대 위에 직접 표시 */}
                <em>{metric.current.toFixed(2)}</em>
              </span>
            </div>
            <span className="metric-chart-label">{metric.name}</span>
          </div>
        ))}
      </div>

      {/* 화면 읽기 프로그램용 표 (차트 내용과 같음) */}
      <table className="metric-chart-table">
        <caption>검증 지표 비교 (예시값)</caption>
        <thead>
          <tr>
            <th scope="col">지표</th>
            <th scope="col">{previousLabel}</th>
            <th scope="col">{currentLabel}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.name}>
              <th scope="row">{metric.name}</th>
              <td>{metric.previous.toFixed(2)}</td>
              <td>{metric.current.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
