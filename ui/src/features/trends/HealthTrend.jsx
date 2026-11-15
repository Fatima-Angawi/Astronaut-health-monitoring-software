/**
 * Trend chart card.
 *
 * The chart itself is the pre-rendered Figma artwork (two SVG paths) layered over a
 * y/x axis, so the visual design is preserved exactly. `note` states plainly that the
 * curve is illustrative rather than raw daily source data.
 */
export default function HealthTrend({
  title,
  subtitle,
  note,
  yLabels = [],
  xLabels = [],
  chartA,
  chartB,
  legend,
}) {
  return (
    <section className="trend">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <p className="trend-note">{note}</p>
      <div className="chart">
        <div className="y-axis">
          {yLabels.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <div className="chart-plot">
          <div className="chart-lines">
            <img className="chart-a" src={chartA} alt="" />
            {chartB && <img className="chart-b" src={chartB} alt="" />}
          </div>
          <div className="x-axis">
            {xLabels.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        </div>
      </div>
      {legend && (
        <div className="legend">
          {legend.map((item) => (
            <span key={item.label}>
              <img src={item.icon} alt="" />
              {item.label}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
