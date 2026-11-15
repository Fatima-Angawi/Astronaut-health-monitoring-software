import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import useApi from "../../hooks/useApi";
import { getEnvironmentDaily } from "../../api";
import Async from "./Async";
import DataSourceBadge from "./DataSourceBadge";

/** Daily cabin or radiation values (/environment/daily), with where they come from. */
export default function EnvTrend({ metric, source, unit, from, to }) {
  const state = useApi(() => getEnvironmentDaily(metric, from, to), [metric, from, to], to > 0);
  return (
    <section className="trend">
      <div>
        <h3>{metric}</h3>
        <p>
          {unit} · {source}
        </p>
      </div>
      <Async state={state}>
        {(d) => {
          const rows = d.items.filter((r) => r.source === source);
          const real = rows.some((r) => r.is_real);
          return (
            <>
              <DataSourceBadge kind={real ? "nasa" : "simulated"} label={real ? `NASA · ${rows[0]?.value_id ?? ""}` : "Simulated"} />
              <div className="trend-chart">
                <ResponsiveContainer>
                  <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -4 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="mission_day" stroke="rgba(255,255,255,0.6)" fontSize={11} />
                    <YAxis stroke="rgba(255,255,255,0.6)" fontSize={11} domain={["auto", "auto"]} />
                    <Tooltip contentStyle={{ background: "#0b1430", border: "1px solid #2f324b" }} labelFormatter={(l) => `Day ${l}`} />
                    <Line type="monotone" dataKey="value" stroke="#317dff" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          );
        }}
      </Async>
    </section>
  );
}
