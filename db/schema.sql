-- Astronaut Health Monitoring – SQLite schema (suggested)
-- One file on board, works offline.
-- Rule: values come from the knowledge base (Excel) via export_kb.py; never edit kb_* tables by hand.

PRAGMA foreign_keys = ON;

------------------------------------------------------------------
-- 1. KNOWLEDGE BASE (exported from Astronaut_Health_Knowledge_Base.xlsx)
------------------------------------------------------------------
CREATE TABLE kb_indicators (
  indicator_id   TEXT PRIMARY KEY,          -- 'R01', 'R21b', 'R18'
  risk           TEXT NOT NULL,             -- 'Sleep Loss'
  name           TEXT NOT NULL,             -- 'Total sleep duration'
  unit           TEXT,
  app_priority   TEXT,                      -- Core / Add-on / Context / Low
  in_mvp         INTEGER DEFAULT 0
);

CREATE TABLE kb_values (
  value_id       TEXT PRIMARY KEY,          -- 'V039'
  indicator_id   TEXT,                      -- may be 'ALL'
  field          TEXT,                      -- 'Career limit'
  value          TEXT,                      -- '600'
  unit           TEXT,                      -- 'mSv'
  value_type     TEXT,                      -- NASA standard / Report finding / Study / Team design / Derived / To find
  source_doc     TEXT,                      -- 'Radiation Carcinogenesis ER (HRP, 2026)'
  file_name      TEXT,
  pdf_page       TEXT,                      -- '49' or 'web'
  quote          TEXT,                      -- exact quote
  status         TEXT                       -- Verified / Design – needs approval / Open
);

CREATE TABLE rules (
  rule_id        INTEGER PRIMARY KEY,
  indicator_id   TEXT NOT NULL REFERENCES kb_indicators,
  level          TEXT NOT NULL CHECK (level IN ('yellow','orange','red')),
  metric         TEXT NOT NULL,             -- 'sleep_h_7d_mean'
  op             TEXT NOT NULL,             -- '<', '>', '>=', 'baseline+2sd', 'and'
  threshold      REAL,                      -- 6
  window_days    INTEGER,                   -- 7
  value_id       TEXT REFERENCES kb_values, -- evidence for this rule
  enabled        INTEGER DEFAULT 1          -- 0 for rules waiting for a source (e.g. R10b red)
);

------------------------------------------------------------------
-- 2. MISSION AND CREW (shared by every indicator)
------------------------------------------------------------------
CREATE TABLE crew (
  astronaut_id                TEXT PRIMARY KEY,   -- 'A1'..'A4'
  role                        TEXT,               -- 'CMO' for the crew medical officer
  sex                         TEXT,
  preflight_abmd_total_hip    REAL,               -- g/cm2, DXA <= 45 days before launch (Fracture ER)
  preflight_abmd_lumbar_spine REAL,               -- g/cm2
  preflight_abmd_femoral_neck REAL                -- g/cm2
);

CREATE TABLE mission_timeline (
  mission_day    INTEGER PRIMARY KEY,       -- 1..180
  date           TEXT NOT NULL,             -- simulated calendar date
  replay_date    TEXT,                      -- real date being replayed (e.g. 2024-02-12) for DONKI/RadLab/EDA
  gravity_level  REAL DEFAULT 0,            -- 0, 0.17, 0.38, 1 
  phase          TEXT                       -- transit / surface / return

  -- gravity_level is a mission-scenario setting that we choose in the simulator:
  -- Our current mission is the ISS, so it’s 0 for all 180 days.
  -- It’s there for a Moon (0.17) or Mars (0.38) scenario
  -- the Fracture report says fracture risk rises on planetary surfaces (p5, p23).
);

CREATE TABLE mission_events (
  event_id       INTEGER PRIMARY KEY,
  mission_day    INTEGER REFERENCES mission_timeline,
  astronaut_id   TEXT REFERENCES crew,      -- NULL = whole crew
  type           TEXT,                      -- 'EVA', 'docking', 'landing', 'surface_activity', 'fall'
  start_time     TEXT,
  end_time       TEXT,
  critical       INTEGER DEFAULT 0          -- used by R01/R01c red rule
);

------------------------------------------------------------------
-- 3. CREW MEASUREMENTS (simulated or collected by the app) are behavioral and cardiovas all here?!
------------------------------------------------------------------
CREATE TABLE readings (
  reading_id     INTEGER PRIMARY KEY,
  astronaut_id   TEXT NOT NULL REFERENCES crew,
  time           TEXT NOT NULL,             -- ISO timestamp
  mission_day    INTEGER REFERENCES mission_timeline,
  indicator_id   TEXT NOT NULL REFERENCES kb_indicators,
  metric         TEXT NOT NULL,             -- 'sleep_h', 'pvt_lapses', 'mood', 'exercise_minutes'
  value          REAL,
  unit           TEXT,
  source         TEXT,                      -- 'simulator', 'app', 'watch-01'
  is_real        INTEGER DEFAULT 0,         -- 1 = real measurement, 0 = simulated
  availability   TEXT DEFAULT 'live'        -- 'live' or 'after_return' (e.g. bone markers)
);
CREATE INDEX ix_readings ON readings (astronaut_id, indicator_id, metric, time);
CREATE UNIQUE INDEX ux_readings_dedup ON readings (astronaut_id, time, metric, source);

CREATE TABLE pvt_sessions (                 -- detail for R01c (one row per test)
  session_id     INTEGER PRIMARY KEY,
  astronaut_id   TEXT REFERENCES crew,
  time           TEXT,
  version        TEXT,                      -- 'PVT-B 3min' / 'PVT 10min'
  mean_rt_ms     REAL,
  mean_inv_rt    REAL,
  slowest10_ms   REAL,
  lapses         INTEGER,
  false_starts   INTEGER,
  kss            INTEGER,                   -- R01d rating taken just before
  device_id      TEXT
);

------------------------------------------------------------------
-- 4. REAL NASA ENVIRONMENT DATA (are they all being measured in our app?) add Ahmed's data finding
------------------------------------------------------------------
CREATE TABLE spe_events (                   -- DONKI (R21b)
  event_key      TEXT PRIMARY KEY,          -- linked CME/flare activityID, so re-fetching never duplicates
  onset_time     TEXT NOT NULL,
  max_channel    TEXT,                      -- '>100 MeV'
  source_link    TEXT,
  value_id       TEXT DEFAULT 'V063'
);

CREATE TABLE spe_channels (
  event_key      TEXT REFERENCES spe_events,
  channel        TEXT,                      -- '>10 MeV'
  min_energy_mev REAL,                      -- 10
  instrument     TEXT,                      -- 'GOES-P: SEISS >10 MeV'
  time           TEXT,
  sep_id         TEXT,                      -- DONKI record id
  PRIMARY KEY (event_key, channel, instrument)
);

CREATE TABLE env_readings (                 -- raw environment telemetry, as received by POST /environment
  time           TEXT NOT NULL,             -- UTC, normalised by the server to YYYY-MM-DDTHH:MM:SSZ
  metric         TEXT NOT NULL,             -- 'co2_ppm', 'temp_c', 'rh_pct', 'absorbed_dose_rate_uGy_h', ...
  value          REAL,
  unit           TEXT,
  sensor         TEXT NOT NULL,             -- 'CO2_ppm_ISS', 'DosTel1', 'CDRA-1'
  source         TEXT NOT NULL,             -- feed: 'OSDR EDA RR-1', 'RadLab', 'vehicle'
  is_real        INTEGER DEFAULT 1,
  mission_day    INTEGER,                   -- sent by replay feeds; live data gets it from mission_timeline.date
  latitude       REAL,                      -- radiation only (orbit position)
  longitude      REAL,
  l_value        REAL,
  PRIMARY KEY (time, metric, sensor, source)   -- a feed can resend after an outage without double rows
);

CREATE TABLE env_daily (                    -- computed by the server (api/env_summary.py) from env_readings
  date           TEXT NOT NULL,             -- UTC date of the measurement (real date for replays)
  mission_day    INTEGER,                   -- ← new
  metric         TEXT NOT NULL,             -- 'co2_1h_max_ppm', 'temp_sleep_mean_c', 'absorbed_dose_uGy_day', ...
  value          REAL,
  unit           TEXT,
  source         TEXT,
  value_id       TEXT,                      -- V066 / V065 / V053 / V064
  is_real        INTEGER DEFAULT 1,         -- ← new
  coverage_pct   REAL,                      -- ← new: readings received / readings expected that day
  complete       INTEGER,                   -- ← new: 1 if coverage >= 80 % (team design)
  PRIMARY KEY (date, metric, source)
);


------------------------------------------------------------------
-- 5. ENGINE OUTPUT
------------------------------------------------------------------
CREATE TABLE baselines (
  astronaut_id   TEXT REFERENCES crew,
  indicator_id   TEXT REFERENCES kb_indicators,
  metric         TEXT,
  median         REAL,
  robust_sd      REAL,                      -- 1.4826 × MAD
  n_points       INTEGER,
  computed_from  TEXT,                      -- 'mission_day 1-7'
  PRIMARY KEY (astronaut_id, indicator_id, metric)
);

CREATE TABLE alerts (
  alert_id       INTEGER PRIMARY KEY,
  astronaut_id   TEXT REFERENCES crew,
  time           TEXT NOT NULL,
  indicator_id   TEXT REFERENCES kb_indicators,
  level          TEXT CHECK (level IN ('yellow','orange','red')),
  source_engine  TEXT,                      -- 'rule' / 'anomaly_model' / 'mismatch'
  rule_id        INTEGER REFERENCES rules,
  reason         TEXT,                      -- plain-language explanation - maybe Ai here
  action         TEXT,                      -- recommended countermeasure - still to do
  value_ids      TEXT,                      -- 'V008,V005,V007'
  escalated_to   TEXT,                      -- 'astronaut' / 'CMO' / 'flight_surgeon'
  acknowledged   INTEGER DEFAULT 0,
  synced_to_ground INTEGER DEFAULT 0        -- 0 = queued for the delayed link
);

------------------------------------------------------------------
-- 6. TESTING (never read by the engine)
------------------------------------------------------------------
CREATE TABLE anomaly_labels (
  label_id       INTEGER PRIMARY KEY,
  astronaut_id   TEXT REFERENCES crew,
  indicator_id   TEXT REFERENCES kb_indicators,
  scenario       TEXT,                      -- '1_exercise_drop'
  start_day      INTEGER,
  end_day        INTEGER,
  expected_level TEXT,
  is_decoy       INTEGER DEFAULT 0
);

------------------------------------------------------------------
-- 7. PROVENANCE OF RAW FILES
------------------------------------------------------------------
CREATE TABLE raw_files (
  path           TEXT PRIMARY KEY,          -- 'data/raw/radlab/dostel1_2024-02-11_13.csv'
  source         TEXT,                      -- 'NASA OSDR RadLab API'
  request_url    TEXT,
  downloaded_on  TEXT,
  units          TEXT,
  used_for       TEXT                       -- 'R21 base rate; R21b comparison'
);
