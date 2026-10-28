-- Talent One headless runner: state store (SQLite), one per machine.
-- A "run" is one role on one date. Every headless session the runner spawns is a row in
-- `sessions`; every requested artifact is a row in `artifacts`. Idempotent: safe to re-run.
-- The runner opens a connection per operation and serialises writes behind one lock, so
-- the parallel content and critic phases never share a connection across threads.

CREATE TABLE IF NOT EXISTS runs (
  run_id       TEXT PRIMARY KEY,         -- <role-slug>-<YYYY-MM-DD> unless --run-id is given
  role_title   TEXT NOT NULL,
  role_slug    TEXT NOT NULL,
  role_home    TEXT NOT NULL,            -- talent-one-roles/<role_slug>/
  run_dir      TEXT NOT NULL,            -- <role_home>/runs/<YYYY-MM-DD>/
  profile_path TEXT,
  created_at   TEXT NOT NULL,
  gate         TEXT,                     -- PASSED | FAILED | NOT_EVALUATED
  gate_reasons TEXT                      -- JSON list of the reasons the gate failed
);

-- One row per headless session: scout, critic (pack or artifact), artifact agents, qa-gate.
CREATE TABLE IF NOT EXISTS sessions (
  run_id      TEXT NOT NULL,
  agent       TEXT NOT NULL,             -- e.g. jdbot, critic, qa-gate
  phase       TEXT NOT NULL,             -- pack | content | critic | qa
  artifact_nn TEXT NOT NULL DEFAULT '',  -- '' for scout, the pack critic and qa-gate
  model       TEXT,
  session_id  TEXT,                      -- the claude -p session that produced it
  cost_usd    REAL,
  status      TEXT NOT NULL,             -- ok | dry-run | need-input | error
  verdict     TEXT,                      -- critic: PASS | RETURNED; qa-gate: CERTIFIED | RETURNED
  created_at  TEXT NOT NULL,
  PRIMARY KEY (run_id, agent, phase, artifact_nn)
);

-- One row per requested artifact.
CREATE TABLE IF NOT EXISTS artifacts (
  run_id         TEXT NOT NULL,
  artifact_nn    TEXT NOT NULL,
  agent          TEXT NOT NULL,
  content_path   TEXT,                   -- <run_dir>/content/<NN>.content.json
  html_path      TEXT,                   -- <run_dir>/<NN>_<agent>.html
  verify_path    TEXT,                   -- <run_dir>/verify/<NN>.verify.json
  verify_high    INTEGER,                -- HIGH findings in the verify report
  critic_verdict TEXT,
  status         TEXT NOT NULL,          -- planned | content | rendered | render-failed | need-input
  created_at     TEXT NOT NULL,
  PRIMARY KEY (run_id, artifact_nn)
);
