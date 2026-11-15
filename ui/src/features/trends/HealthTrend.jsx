import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import useApi from "../../hooks/useApi";
import { getTrend } from "../../api";
import Async from "../../components/common/Async";
import { useAppState } from "../../state/context";

/**
 * Trend chart from /trends. `lines` are labelled reference lines; each label must carry the
 * Value ID that sets it (or say it is a team design / assumption). The dashed blue line is the
 * astronaut's own median from days 1-14, as returned by the API.
 */
export default function HealthTrend({ title, subtitle, metric, unit = "", domain, lines = [], window = 14 }) {
  const { astronautId, day } = useAppState();
  const from = Math.max(1, (day ?? 1) - window + 1);
  const state = useApi(() => getTrend(astronautId, metric, from, day), [astronautId, metric, from, day], day > 0);

  return (
    <section className="trend">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <Async state={state} empty={<p className="async-note">No data for this day yet.</p>}>
        {(d) => (
          <div className="trend-chart">
            <ResponsiveContainer>
              <LineChart data={d.items} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="mission_day" stroke="rgba(255,255,255,0.6)" fontSize={11} />
                <YAxis domain={domain ?? ["auto", "auto"]} stroke="rgba(255,255,255,0.6)" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: "#0b1430", border: "1px solid #2f324b" }}
                  formatter={(v) => [`${typeof v === "number" ? v.toFixed(2) : v} ${unit}`, title]}
                  labelFormatter={(l) => `Day ${l}`}
                />
                {d.baseline && (
                  <ReferenceLine
                    y={d.baseline.median}
                    stroke="#317dff"
                    strokeDasharray="4 4"
                    label={{ value: "own baseline", fill: "#317dff", fontSize: 10, position: "insideTopLeft" }}
                  />
                )}
                {lines.map((l) => (
                  <ReferenceLine
                    key={l.label}
                    y={l.y}
                    stroke={l.color ?? "#fc743b"}
                    strokeDasharray="2 4"
                    label={{ value: l.label, fill: l.color ?? "#fc743b", fontSize: 10, position: "insideBottomRight" }}
                  />
                ))}
                <Line type="monotone" dataKey="value" stroke="#69c860" strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Async>
    </section>
  );
}
