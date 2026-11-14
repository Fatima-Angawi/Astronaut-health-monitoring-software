import { useEffect, useState } from "react";

const A = "src/assets";

const icons = {
  logo: `${A}/aa2ec.svg`,
  status: `${A}/2356b.svg`,
  bell: `${A}/db6a0.svg`,
  user: `${A}/a2a78.svg`,
  dashboard: `${A}/e1e31.svg`,
  moonNav: `${A}/8a9d4.svg`,
  activity: `${A}/a1e57.svg`,
  heart: `${A}/e10b7.svg`,
  settings: `${A}/d6efe.svg`,
  warning: `${A}/b7e21.svg`,
  timer: `${A}/c1438.svg`,
  moon: `${A}/81af4.svg`,
  rocket: `${A}/c0623.svg`,
  brain: `${A}/14773.svg`,
  testTimer: `${A}/5c239.svg`,
  actionWarning: `${A}/bf1b3.svg`,
  coffee: `${A}/d81af.svg`,
  sun: `${A}/cb309.svg`,
  calendar: `${A}/15766.svg`,
  dose: `${A}/a244e.svg`,
  radio: `${A}/1ccc7.svg`,
};

function Metric({ icon, status, tone = "red", title, value, detail }) {
  return (
    <article className="metric">
      <div className="metric-top">
        <img src={icon} alt="" />
        <span className={`pill ${tone}`}>{status}</span>
      </div>
      <p className="label">{title}</p>
      <p className="metric-value">{value}</p>
      <p className="micro">{detail}</p>
    </article>
  );
}

function Trend({ title, subtitle, note, labels, chartA, chartB, legend }) {
  return (
    <section className="trend">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <p className="trend-note">{note}</p>
      <div className="chart">
        <div className="y-axis">
          {labels.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <div className="chart-plot">
          <div className="chart-lines">
            <img className="chart-a" src={chartA} alt="" />
            <img className="chart-b" src={chartB} alt="" />
          </div>
          <div className="x-axis">
            <span>53</span>
            <span>56</span>
            <span>59</span>
            <span>62</span>
            <span>66</span>
          </div>
        </div>
      </div>
      {legend && (
        <div className="legend">
          <span>
            <img src={`${A}/0f068.svg`} alt="" />
            Sleep
          </span>
          <span>
            <img src={`${A}/5802a.svg`} alt="" />
            Target
          </span>
          <span>
            <img src={`${A}/69bc2.svg`} alt="" />
            Alert threshold
          </span>
        </div>
      )}
    </section>
  );
}

function ActionItem({ title, copy, icon, tag, tone }) {
  return (
    <div className="action-item">
      <div className="action-title">
        <strong>{title}</strong>
        <img src={icon} alt="" />
      </div>
      <p>{copy}</p>
      <span className={`pill ${tone}`}>{tag}</span>
    </div>
  );
}

function ContextItem({ icon, title, value, detail, alert }) {
  return (
    <div className="context-item">
      <img src={icon} alt="" />
      <strong>{title}</strong>
      <b>{value}</b>
      {alert ? <span className="pill red">{detail}</span> : <small>{detail}</small>}
    </div>
  );
}

export default function App() {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [testState, setTestState] = useState("ready");
  const [reaction, setReaction] = useState(null);
  const [goAt, setGoAt] = useState(0);

  useEffect(() => {
    if (testState !== "waiting") return;
    const timeout = window.setTimeout(() => {
      setGoAt(performance.now());
      setTestState("go");
    }, 1400);
    return () => window.clearTimeout(timeout);
  }, [testState]);

  const runTest = () => {
    if (testState === "go") {
      setReaction(Math.round(performance.now() - goAt));
      setTestState("done");
      return;
    }
    setReaction(null);
    setTestState("waiting");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="logo-wrap">
            <img src={icons.logo} alt="" />
          </div>
          <div>
            <strong>Astronaut Health</strong>
            <span>Personal Health Overview</span>
          </div>
        </div>
        <div className="mission-meta">
          <div>
            <span>Mission Status</span>
            <strong className="on-track">
              On Track <img src={icons.status} alt="" />
            </strong>
          </div>
          <div>
            <span>Mission Day</span>
            <strong>180 / 043</strong>
          </div>
          <button aria-label="Notifications">
            <img src={icons.bell} alt="" />
          </button>
          <button className="user-button" aria-label="User profile">
            <img src={icons.user} alt="" />
          </button>
        </div>
      </header>

      <aside className="sidebar" aria-label="Main navigation">
        {[
          ["dashboard", icons.dashboard, "Dashboard"],
          ["sleep", icons.moonNav, "Sleep"],
          ["activity", icons.activity, "Activity"],
          ["heart", icons.heart, "Heart"],
          ["settings", icons.settings, "Settings"],
        ].map(([id, icon, label]) => (
          <button
            key={id}
            className={activeNav === id ? "active" : ""}
            onClick={() => setActiveNav(id)}
            aria-label={label}
          >
            <img src={icon} alt="" />
          </button>
        ))}
      </aside>

      <main>
        <h1>Health Overview</h1>

        <section className="alert-card">
          <div className="alert-heading">
            <h2>You're short on sleep before tomorrow's EVA.</h2>
            <span className="pill red">RED ALERT</span>
          </div>
          <p>
            Your average sleep has been 4.8 hours over the last 7 nights, and your reaction test is
            slower than usual.
          </p>
          <div className="recommendation">
            <span>
              <strong>Recommended:</strong> Ask the flight surgeon to review EVA timing
            </span>
            <img src={icons.warning} alt="" />
          </div>
        </section>

        <section className="metrics">
          <Metric
            icon={icons.timer}
            status="Slower"
            title="Reaction Test"
            value="8 lapses"
            detail="Latest PVT"
          />
          <Metric
            icon={icons.moon}
            status="Low"
            title="Sleep"
            value="h 4.8"
            detail="7-day average"
          />
          <Metric
            icon={icons.rocket}
            status="Critical"
            title="Next EVA"
            value="08:00"
            detail="Mission Day 67"
          />
          <Metric
            icon={icons.brain}
            status="Declining"
            tone="orange"
            title="Mood"
            value="3 / 5"
            detail="Self-reported"
          />
        </section>

        <div className="dashboard-grid">
          <section className="panel trends-panel">
            <h2>Health Trends - Last 14 Days</h2>
            <Trend
              title="Sleep Duration"
              subtitle="Hours per night · 8.5 h target · 6h alert"
              note="Illustrative visualization of the scenario, not raw daily source data."
              labels={["10 h", "8 h", "6 h", "4 h"]}
              chartA={`${A}/4fac5.svg`}
              chartB={`${A}/18fe0.svg`}
              legend
            />
            <Trend
              title="Reaction Test (PVT)"
              subtitle="Reaction lapses · personal baseline comparison"
              note="Illustrative trend, not exact daily values."
              labels={["9", "6", "3", "0"]}
              chartA={`${A}/26281.svg`}
              chartB={`${A}/daec8.svg`}
            />
            <Trend
              title="Mood Tracking"
              subtitle="Self-reported mood · scale 1–5"
              note="Illustrative trend, exact intermediate values are not provided."
              labels={["5 / 5", "4 / 5", "3 / 5", "2 / 5", "1 / 5"]}
              chartA={`${A}/82bd2.svg`}
              chartB={`${A}/9802b.svg`}
            />
          </section>

          <div className="right-column">
            <section className="panel reaction-card">
              <div className="section-heading">
                <h2>Reaction Test</h2>
                <span className="pill blue">PVT-B · 3 MIN</span>
              </div>
              <h3>Test your reaction time</h3>
              <p>Tap as quickly as possible when the visual stimulus appears.</p>
              <button
                className={`test-display ${testState}`}
                onClick={testState === "go" ? runTest : undefined}
              >
                <img src={icons.testTimer} alt="" />
                <strong>
                  {testState === "go" ? "TAP NOW" : reaction ? `${reaction} ms` : "03:00"}
                </strong>
                <span>
                  {testState === "waiting"
                    ? "Wait for the signal…"
                    : testState === "go"
                      ? "Tap the panel"
                      : reaction
                        ? "Reaction recorded"
                        : "Estimated test duration"}
                </span>
                <em>
                  {testState === "ready"
                    ? "Ready to start"
                    : testState === "done"
                      ? "Test complete"
                      : testState === "go"
                        ? "Go!"
                        : "Get ready"}
                </em>
              </button>
              <button
                className="start-button"
                onClick={runTest}
                disabled={testState === "waiting" || testState === "go"}
              >
                {testState === "done" ? "Run Test Again" : "Start Reaction Test"}
              </button>
            </section>

            <section className="panel actions-card">
              <div className="section-heading">
                <h2>Recommended Actions</h2>
                <span className="pill red">High Priority</span>
              </div>
              <ActionItem
                title="Review EVA Timing"
                copy="Ask the flight surgeon to review tomorrow's EVA schedule."
                icon={icons.actionWarning}
                tag="Requires Review"
                tone="red"
              />
              <ActionItem
                title="Protect Sleep Period"
                copy="Aim for a full 8.5-hour sleep period tonight."
                icon={icons.moon}
                tag="Important"
                tone="orange"
              />
              <ActionItem
                title="Recovery Plan"
                copy="Take a short nap this afternoon and use caffeine early."
                icon={icons.coffee}
                tag="Suggested"
                tone="blue"
              />
            </section>

            <section className="panel context-card">
              <h2>Mission Context</h2>
              <div className="context-grid">
                <ContextItem
                  icon={icons.sun}
                  title="Space Weather"
                  value="No SPE"
                  detail="No active event"
                />
                <ContextItem
                  icon={icons.calendar}
                  title="Tomorrow's EVA"
                  value="08:00"
                  detail="Requires Review"
                  alert
                />
                <ContextItem
                  icon={icons.dose}
                  title="ISS Dose Today"
                  value="mGy 0.55"
                  detail="NASA RadLab"
                />
                <ContextItem
                  icon={icons.radio}
                  title="Cabin CO₂"
                  value="2,480 ppm"
                  detail="Simulated data"
                />
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}