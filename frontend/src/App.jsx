import React, { useEffect, useState } from "react";

export const percent = (value) =>
  value == null ? "—" : `${(value * 100).toFixed(2)}%`;
const json = (value) => JSON.stringify(value, null, 2);
const number = (value) => (value == null ? "—" : value.toLocaleString("en-US"));
async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok)
    throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}
const post = (value) => ({
  method: "POST",
  headers: { "Content-Type": "application/json", "X-BBT-Local": "1" },
  body: JSON.stringify(value),
});

export function Badge({ status }) {
  return (
    <span
      className={`badge ${String(status).toLowerCase().replaceAll("_", "-")}`}
    >
      {status}
    </span>
  );
}
export function Metric({ label, value, note }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}
export function TraceTable({ comparison }) {
  if (!comparison) return <p>No recorded counterexample available.</p>;
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Action</th>
            <th>Original output</th>
            <th>Twin output</th>
          </tr>
        </thead>
        <tbody>
          {comparison.actions.map((action, i) => (
            <tr
              key={i}
              className={i === comparison.first_divergence ? "divergence" : ""}
            >
              <td>
                {i + 1}
                {i === comparison.first_divergence && (
                  <small>First divergence</small>
                )}
              </td>
              <td>
                <code>{action}</code>
              </td>
              <td>
                <code>
                  {JSON.stringify(comparison.raw_original[i] ?? null)}
                </code>
              </td>
              <td>
                <code>{JSON.stringify(comparison.raw_twin[i] ?? null)}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ModelGraph({ model, selected, onSelect }) {
  const states = Object.keys(model.transitions);
  const point = (index) =>
    states.length === 1
      ? [220, 125]
      : [
          220 +
            145 * Math.cos((index * 2 * Math.PI) / states.length - Math.PI / 2),
          125 +
            82 * Math.sin((index * 2 * Math.PI) / states.length - Math.PI / 2),
        ];
  const edges = Object.entries(model.transitions[selected] || {});
  return (
    <svg
      viewBox="0 0 440 250"
      role="img"
      aria-label={`Learned model with ${states.length} states; outgoing transitions from ${selected}`}
    >
      <defs>
        <marker
          id="arrow"
          viewBox="0 0 10 10"
          refX="20"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#92a56b" />
        </marker>
      </defs>
      {edges.map(([action, edge], i) => {
        const a = point(states.indexOf(selected)),
          b = point(states.indexOf(edge.next_state));
        return (
          <g key={action}>
            {selected === edge.next_state ? (
              <path
                d={`M ${a[0] - 14} ${a[1] - 10} c -50 -65 75 -65 28 0`}
                fill="none"
                stroke="#92a56b"
              />
            ) : (
              <line
                x1={a[0]}
                y1={a[1]}
                x2={b[0]}
                y2={b[1]}
                stroke="#92a56b"
                markerEnd="url(#arrow)"
              />
            )}
            <text
              x={(a[0] + b[0]) / 2 + i * 4}
              y={(a[1] + b[1]) / 2 - 20 - i * 12}
              className="edge-label"
            >
              {action}
            </text>
          </g>
        );
      })}
      {states.map((state, i) => {
        const [x, y] = point(i);
        return (
          <g key={state}>
            <circle
              cx={x}
              cy={y}
              r="23"
              className={selected === state ? "node selected-node" : "node"}
              onClick={() => onSelect(state)}
            />
            <text x={x} y={y + 4} textAnchor="middle" className="node-label">
              {state}
            </text>
            {state === model.initial_state && (
              <text x={x} y={y + 38} textAnchor="middle" className="edge-label">
                RESET
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function Models({ experiment }) {
  const [revision, setRevision] = useState(0),
    [selected, setSelected] = useState("");
  const record = experiment.models[revision] || experiment.models[0],
    model = record.model;
  const state = model.transitions[selected] ? selected : model.initial_state;
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">02 / INSPECT</span>
          <h2>Watch the model change</h2>
        </div>
        <div className="segmented">
          {experiment.models.map((m, i) => (
            <button
              key={i}
              className={revision === i ? "active" : ""}
              onClick={() => {
                setRevision(i);
                setSelected("");
              }}
            >
              Revision {i} · {Object.keys(m.model.transitions).length} states
            </button>
          ))}
        </div>
      </div>
      <div className="model-layout">
        <div className="graph">
          <ModelGraph model={model} selected={state} onSelect={setSelected} />
          <div className="state-buttons">
            {Object.keys(model.transitions).map((s) => (
              <button
                key={s}
                aria-pressed={state === s}
                onClick={() => setSelected(s)}
              >
                {s}
              </button>
            ))}
          </div>
          <p>
            Learned states, not hidden source states. Select a state to inspect
            its outgoing transitions.
          </p>
        </div>
        <div>
          <span className="eyebrow">OUTGOING FROM {state}</span>
          <table>
            <thead>
              <tr>
                <th>Input</th>
                <th>Next</th>
                <th>Prediction</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(model.transitions[state]).map(
                ([action, edge]) => (
                  <tr key={action}>
                    <td>
                      <code>{action}</code>
                    </td>
                    <td>{edge.next_state}</td>
                    <td>
                      <code>{JSON.stringify(edge.output.payload)}</code>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
          <p className="subtle">
            Finite predictions carry the legacy concrete claim. They are not
            version-3 INFERRED_SUPPORTED predictions.
          </p>
          <div className="actions">
            <a
              href={`/api/experiments/${experiment.id}/export/${revision}/model`}
            >
              ↓ Model JSON
            </a>
            <a
              href={`/api/experiments/${experiment.id}/export/${revision}/twin`}
            >
              ↓ Standalone twin
            </a>
          </div>
          <details>
            <summary>
              Model and provenance · {number(record.bytes)} bytes
            </summary>
            <p className="mono wrap">SHA256 {record.sha256}</p>
            <pre>{json(model)}</pre>
          </details>
        </div>
      </div>
    </section>
  );
}

function Events({ id, onError }) {
  const [offset, setOffset] = useState(0),
    [data, setData] = useState(null);
  useEffect(() => {
    let active = true;
    api(`/api/experiments/${id}/events?offset=${offset}&limit=10`)
      .then((x) => active && setData(x))
      .catch(onError);
    return () => {
      active = false;
    };
  }, [id, offset]);
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">05 / AUDIT</span>
          <h2>Physical action ledger</h2>
        </div>
        <span className="subtle">SQLite · read only</span>
      </div>
      {!data ? (
        <p>Loading recorded events…</p>
      ) : (
        <>
          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th>Event / experiment</th>
                  <th>Phase</th>
                  <th>Request</th>
                  <th>Oracle response</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.id}>
                    <td>
                      #{r.id}
                      <small className="mono">{r.experiment_id}</small>
                    </td>
                    <td>{r.phase}</td>
                    <td>
                      <code>{JSON.stringify(r.request)}</code>
                    </td>
                    <td>
                      <code>
                        {JSON.stringify(r.response?.payload ?? r.response)}
                      </code>
                    </td>
                    <td>{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 10))}
            >
              Previous events
            </button>
            <span>
              {offset + 1}–{Math.min(offset + 10, data.total)} of{" "}
              {number(data.total)}
            </span>
            <button
              disabled={offset + 10 >= data.total}
              onClick={() => setOffset(offset + 10)}
            >
              Next events
            </button>
          </div>
        </>
      )}
    </section>
  );
}

function Demo({ experiment, onError }) {
  const [minimized, setMinimized] = useState(true);
  if (!experiment)
    return <div className="empty">Loading persisted experiment…</div>;
  const { summary, evaluation } = experiment;
  const iteration = summary.iterations.find((i) => i.regressions),
    record = experiment.counterexamples[0];
  const comparison = record?.minimization[minimized ? "minimized" : "original"];
  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow light">FLAGSHIP / DELAYED COMMIT</span>
          <h1>
            A disagreement.
            <br />A smaller witness.
            <br />
            <em>A better twin.</em>
          </h1>
          <p>
            Explore an owned program through JSON inputs. Find a real mismatch,
            shrink its history, then relearn and test an independent executable.
          </p>
          <Badge status={experiment.mode} />
        </div>
        <div className="hero-evidence">
          <span className="eyebrow light">PERSISTED EXPERIMENT RESULTS</span>
          <div className="big-transition">
            <span>
              {Object.keys(experiment.models[0].model.transitions).length}
            </span>
            <span>→</span>
            <strong>
              {Object.keys(experiment.models.at(-1).model.transitions).length}
            </strong>
          </div>
          <p>learned states before / after refinement</p>
          <div className="hero-score">
            <span>{percent(evaluation.scores.initial.trace_match_rate)}</span>
            <span>→</span>
            <strong>
              {percent(evaluation.scores.refined.trace_match_rate)}
            </strong>
          </div>
          <p>
            exact traces on {evaluation.scores.refined.traces} frozen sequences
          </p>
          <small>Sample fidelity. Equivalence is not proven.</small>
        </div>
      </section>
      <div className="metrics">
        <Metric
          label="Original training actions"
          value={number(summary.original_costs.actions)}
          note={`${number(summary.original_costs.resets)} resets · all learning/refinement phases`}
        />
        <Metric
          label="Separate reference actions"
          value={number(evaluation.original_costs.actions)}
          note={`${evaluation.original_costs.resets} resets · paired evaluation`}
        />
        <Metric
          label="Resolved counterexamples"
          value={summary.resolved_counterexamples}
          note={`${iteration?.regressions.passed ?? 0}/${iteration?.regressions.checked ?? 0} recorded regressions passed`}
        />
        <Metric
          label="Refined output fidelity"
          value={percent(evaluation.scores.refined.step_match_rate)}
          note={`${evaluation.scores.refined.step_matches}/${evaluation.scores.refined.steps} evaluated outputs`}
        />
      </div>
      <section className="panel contract">
        <span className="eyebrow">01 / THE INTERFACE</span>
        <h2>Three inputs. A hidden history.</h2>
        <p>
          Owned fixture: {experiment.fixture}. Exact reset:{" "}
          <code>{'{"control":"reset"}'}</code>. The learner receives this public
          action interface, never a transition table.
        </p>
        <div className="action-chips">
          {Object.entries(experiment.input_contract).map(([s, a]) => (
            <code key={s}>{JSON.stringify(a)}</code>
          ))}
        </div>
        <p className="subtle">
          Initial AALpy L* exploration uses deliberately weak testing to make a
          genuine missed history visible. This is a demonstration, not evidence
          that its initial model was adequate.
        </p>
      </section>
      <Models key={experiment.id} experiment={experiment} />
      <section className="panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">03 / CHALLENGE</span>
            <h2>A real counterexample, replayed smaller</h2>
          </div>
          <div className="segmented">
            <button
              className={!minimized ? "active" : ""}
              onClick={() => setMinimized(false)}
            >
              Discovered · {record?.minimization.original.actions.length}{" "}
              actions
            </button>
            <button
              className={minimized ? "active" : ""}
              onClick={() => setMinimized(true)}
            >
              Minimized · {record?.minimization.minimized.actions.length}{" "}
              actions
            </button>
          </div>
        </div>
        <p>
          Each row below is a persisted original-versus-initial-twin execution.
          Highlighted step: first divergence, displayed with one-based indexing.
        </p>
        <TraceTable comparison={comparison} />
        <p className="subtle">
          Minimization: {record?.minimization.status} · deletion-local
          minimality: {String(record?.minimization.locally_minimal)}. This does
          not establish a globally shortest counterexample.
        </p>
      </section>
      <section className="panel">
        <span className="eyebrow">04 / REGENERATE + VERIFY</span>
        <h2>The new model must face the old evidence</h2>
        <div className="two-col">
          <div>
            <p>
              Refinement uses the confirmed counterexample through the existing
              AALpy workflow. The regenerated twin replays prior physical
              observations.
            </p>
            <strong className="result">
              {iteration?.regressions.passed}/{iteration?.regressions.checked}{" "}
              regression cases passed
            </strong>
            <p>
              Previously passing preserved:{" "}
              {iteration?.regressions.previously_passing_preserved}/
              {iteration?.regressions.previously_passing}. New regressions:{" "}
              {iteration?.regressions.new_regressions}.
            </p>
          </div>
          <div>
            <p>
              Separate frozen evaluation, generated before learning and checked
              for full-sequence overlap:
            </p>
            <strong className="result">
              {evaluation.scores.refined.trace_matches}/
              {evaluation.scores.refined.traces} exact refined traces
            </strong>
            <p>
              Training overlap: {evaluation.full_sequence_training_overlap}.
              Stop reason: <code>{summary.status}</code>. No equivalence proof.
            </p>
          </div>
        </div>
        <details>
          <summary>All phase costs and recorded budgets</summary>
          <pre>
            {json({
              original: summary.original_costs,
              configuration: experiment.configuration,
              twin: summary.twin_costs,
              phases: summary.phase_costs,
              evaluation,
            })}
          </pre>
        </details>
        <p className="source">
          Source: {experiment.source} · immutable historical evidence is never
          overwritten.
        </p>
      </section>
      <Events
        key={experiment.id + "-events"}
        id={experiment.id}
        onError={onError}
      />
    </>
  );
}

export function SupportRows({ rows }) {
  return (
    <div className="support-rows">
      {rows.map((row, i) => (
        <article key={i} className="support-row">
          <div className="section-heading">
            <strong>
              Step {i + 1} · {row.action.operation || "reset"}
            </strong>
            <Badge status={row.support.status} />
          </div>
          <p className="mono">
            State {JSON.stringify(row.state_before)} →{" "}
            {JSON.stringify(row.state_after)}
          </p>
          <pre>{json(row.output)}</pre>
          <p>{row.support.reason}</p>
          {row.output.bbt_unsupported && (
            <p className="refusal">
              Abstention — no concrete target prediction. State stays unknown
              until reset.
            </p>
          )}
          <details>
            <summary>Support and physical evidence references</summary>
            <pre>
              {json({
                support: row.support,
                rules: row.rules,
                evidence: row.evidence,
                evidence_total: row.evidence_total,
                evidence_truncated: row.evidence_truncated,
              })}
            </pre>
          </details>
        </article>
      ))}
    </div>
  );
}

function Typed({ onError }) {
  const [data, setData] = useState(null),
    [text, setText] = useState(""),
    [result, setResult] = useState(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api("/api/typed")
      .then((x) => {
        setData(x);
        setText(json(x.examples[0].actions));
      })
      .catch(onError);
  }, []);
  async function preview() {
    setBusy(true);
    setResult(null);
    try {
      const requests = JSON.parse(text);
      setResult(await api("/api/typed/preview", post({ requests })));
    } catch (e) {
      onError(e);
    } finally {
      setBusy(false);
    }
  }
  if (!data) return <p>Loading saved support model…</p>;
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">EVIDENCE-AWARE WALLET</span>
        <h1>
          Knowing when
          <br />
          to stop predicting.
        </h1>
        <p>
          Inspect four support categories from a real M6 model. Every preview
          starts at reset state [0,false]. Edit the action sequence, or choose
          an actual model example.
        </p>
      </div>
      <div className="notice">
        Saved policy preview · zero new oracle queries. These are model outputs,
        not fresh target measurements.
      </div>
      <section className="panel">
        <h2>Choose a support case</h2>
        <div className="preset-grid">
          {data.examples.map((example) => (
            <button
              key={example.status}
              onClick={() => {
                setText(json(example.actions));
                setResult(null);
              }}
            >
              <Badge status={example.status} />
              <small>
                {example.actions.length} action
                {example.actions.length === 1 ? "" : "s"} · inspect provenance
              </small>
            </button>
          ))}
        </div>
        <label htmlFor="typed-actions">
          JSON action sequence · up to 30 requests
        </label>
        <textarea
          id="typed-actions"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck="false"
          rows="9"
        />
        <div className="actions">
          <button className="primary" disabled={busy} onClick={preview}>
            {busy ? "Evaluating policy…" : "Inspect predictions"}
          </button>
          <button
            onClick={() => {
              try {
                const actions = JSON.parse(text);
                setText(
                  json([
                    ...actions,
                    { control: "reset" },
                    { operation: "get_balance", arguments: {} },
                  ]),
                );
              } catch (e) {
                onError(e);
              }
            }}
          >
            Append reset + balance check
          </button>
        </div>
        <p className="subtle">
          Unknown-effect actions poison state. Public contract validation errors
          can preserve known state. A reset is a trusted control operation, not
          a learned prediction.
        </p>
      </section>
      {result && (
        <section className="panel" aria-live="polite">
          <h2>Prediction trace</h2>
          <p>
            {result.note} Oracle actions: {result.oracle_actions}.
          </p>
          <SupportRows rows={result.rows} />
        </section>
      )}
      <section className="panel">
        <h2>The bounded support contract</h2>
        <p>
          OBSERVED refers to a real recorded state/action. INFERRED_SUPPORTED
          requires complete bounded version-space consensus. AMBIGUOUS and
          UNSUPPORTED refuse. These labels are evidence categories, not
          probabilities or guarantees about arbitrary software.
        </p>
        <p>
          {data.observations} observations · {data.rules} rules ·{" "}
          {data.states.length} observed state pairs.
        </p>
        <p className="source">{data.source}</p>
        <details>
          <summary>Model identity and provenance hash</summary>
          <pre>{json(data)}</pre>
        </details>
      </section>
    </>
  );
}

export function BenchmarkTable({ cells }) {
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>
            <th>Target / seed</th>
            <th>Method / ceiling</th>
            <th>Run status</th>
            <th>Trace fidelity</th>
            <th>Output fidelity</th>
            <th>Coverage</th>
            <th>Conditional accuracy</th>
            <th>False-supported</th>
            <th>Abstention</th>
            <th>Actions</th>
            <th>Criterion</th>
          </tr>
        </thead>
        <tbody>
          {cells.map((c, i) => (
            <tr key={i}>
              <td>
                {c.target}
                <small>
                  learner index {c.learner_index} · seed {c.learner_seed}
                </small>
                <details>
                  <summary>Cost & provenance</summary>
                  <pre>
                    {json({
                      training_source: c.source,
                      evaluation_source: c.evaluation_source,
                      resets: c.resets,
                      training_wall_seconds: c.wall_seconds,
                      model_bytes: c.model_bytes,
                      note: "Run status and wall time refer to the whole training run; A checkpoints share it.",
                    })}
                  </pre>
                </details>
              </td>
              <td>
                {c.method}
                <small>{number(c.ceiling)} action cap</small>
              </td>
              <td>
                <Badge status={c.status} />
              </td>
              <td>{percent(c.metrics.trace_fidelity)}</td>
              <td>{percent(c.metrics.output_fidelity)}</td>
              <td>{percent(c.metrics.prediction_coverage)}</td>
              <td>{percent(c.metrics.conditional_accuracy)}</td>
              <td>{percent(c.metrics.false_supported_rate)}</td>
              <td>{percent(c.metrics.abstention_rate)}</td>
              <td>{number(c.actual_actions)}</td>
              <td>{c.criterion_reached ? "Reached" : "Not reached"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Benchmarks({ onError }) {
  const [data, setData] = useState(null),
    [track, setTrack] = useState("all"),
    [failed, setFailed] = useState(false),
    [page, setPage] = useState(0);
  useEffect(() => {
    api("/api/benchmarks").then(setData).catch(onError);
  }, []);
  if (!data) return <p>Loading frozen M6 evidence…</p>;
  const cells = data.cells.filter(
    (c) =>
      (track === "all" || c.track === track) &&
      (!failed || !c.criterion_reached),
  );
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">
          FROZEN M6 / ENGINEERING PASS WITH LIMITATIONS
        </span>
        <h1>
          The failures belong
          <br />
          in the evidence.
        </h1>
        <p>
          Inspect every scored checkpoint. Budget exhaustion, incompatibility
          and non-qualifying results remain visible.
        </p>
      </div>
      <div className="metrics">
        <Metric
          label="Target instances"
          value={data.distinct_targets}
          note="Includes historical regression targets"
        />
        <Metric
          label="Benchmark cells"
          value={data.summary.cells}
          note={`${data.summary.points} scored checkpoints`}
        />
        <Metric
          label="Unreached cells"
          value={data.summary.unreached_cells}
          note="95% trace fidelity + 95% coverage criterion"
        />
        <Metric
          label="Original training actions"
          value={number(data.summary.training_actions)}
          note={`${number(data.summary.training_resets)} resets`}
        />
      </div>
      <div className="notice">{data.warning}</div>
      <section className="panel">
        <div className="section-heading">
          <h2>Experiment explorer</h2>
          <div className="filters">
            <label>
              Track{" "}
              <select
                aria-label="Benchmark track"
                value={track}
                onChange={(e) => {
                  setTrack(e.target.value);
                  setPage(0);
                }}
              >
                <option value="all">All tracks</option>
                <option value="A">A · Finite</option>
                <option value="B">B · Wallet</option>
                <option value="C">C · Inventory</option>
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={failed}
                onChange={(e) => {
                  setFailed(e.target.checked);
                  setPage(0);
                }}
              />{" "}
              Criterion not reached
            </label>
          </div>
        </div>
        <BenchmarkTable cells={cells.slice(page * 15, page * 15 + 15)} />
        <div className="pagination">
          <button disabled={page === 0} onClick={() => setPage(page - 1)}>
            Previous cells
          </button>
          <span>
            {cells.length ? page * 15 + 1 : 0}–
            {Math.min(page * 15 + 15, cells.length)} of {cells.length} points
          </span>
          <button
            disabled={(page + 1) * 15 >= cells.length}
            onClick={() => setPage(page + 1)}
          >
            Next cells
          </button>
        </div>
        <details>
          <summary>Frozen source and summary</summary>
          <pre>
            {json({
              source: data.source,
              sha256: data.sha256,
              statuses: data.summary.status_counts,
            })}
          </pre>
        </details>
      </section>
      <section className="panel">
        <h2>What this evidence does not establish</h2>
        <p>
          Inventory reconstruction is unsupported. All concrete inventory runs
          lacked a complete hypothesis at the tested budget. High finite output
          fidelity can conceal rare-path errors. Hardened wallet abstention
          reduced coverage; it did not consistently beat adaptive learning.
          Query-efficiency superiority is not supported. The custom M4 ranker
          remains experimental.
        </p>
        <p>
          Conditional accuracy is undefined when there are zero concrete
          predictions: displayed as —, never 100%. Abstentions never count as
          correct target predictions.
        </p>
      </section>
    </>
  );
}

export function App() {
  const [tab, setTab] = useState("demo"),
    [experiments, setExperiments] = useState([]),
    [id, setId] = useState("m3-replay"),
    [experiment, setExperiment] = useState(null),
    [error, setError] = useState(""),
    [job, setJob] = useState(null);
  const onError = (e) => setError(e.message || String(e));
  const refresh = () =>
    api("/api/experiments").then(setExperiments).catch(onError);
  useEffect(() => {
    refresh();
  }, []);
  useEffect(() => {
    let active = true;
    setExperiment(null);
    api(`/api/experiments/${id}`)
      .then((x) => active && setExperiment(x))
      .catch(onError);
    return () => {
      active = false;
    };
  }, [id]);
  useEffect(() => {
    if (!job || job.status !== "running") return;
    const timer = setInterval(
      () =>
        api(`/api/jobs/${job.id}`)
          .then((x) => {
            setJob(x);
            if (x.status === "completed") {
              refresh();
              setId(x.id);
              setTab("demo");
            }
          })
          .catch(onError),
      1000,
    );
    return () => clearInterval(timer);
  }, [job?.id, job?.status]);
  async function start() {
    setError("");
    try {
      setJob(await api("/api/demo", post({})));
    } catch (e) {
      onError(e);
    }
  }
  return (
    <div className="shell">
      <aside>
        <a className="brand" href="/" aria-label="BlackBox Twin home">
          <span className="brand-mark">
            B<span>↗</span>
          </span>
          <span>
            BLACKBOX
            <br />
            <strong>TWIN</strong>
          </span>
        </a>
        <span className="nav-label">SCIENTIFIC WORKBENCH / M7</span>
        <nav>
          {[
            ["demo", "01", "Discover & refine"],
            ["typed", "02", "Support & uncertainty"],
            ["benchmarks", "03", "Benchmark evidence"],
          ].map(([key, n, label]) => (
            <button
              key={key}
              aria-current={tab === key ? "page" : undefined}
              className={tab === key ? "nav-active" : ""}
              onClick={() => {
                setTab(key);
                setError("");
              }}
            >
              <span>{n}</span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="local-dot" /> Local execution
          <p>
            Owned fixtures only.
            <br />
            No cloud. No paid API.
            <br />
            No equivalence claim.
          </p>
          <span className="version">EXPERIMENTAL / 0.1</span>
        </div>
      </aside>
      <main>
        <header>
          <span>
            RESEARCH /{" "}
            <strong>
              {tab === "demo"
                ? "DIFFERENTIAL RECONSTRUCTION"
                : tab === "typed"
                  ? "SUPPORT POLICY"
                  : "BENCHMARK EXPLORER"}
            </strong>
          </span>
          <span className="header-tag">EVIDENCE BEFORE CLAIMS</span>
        </header>
        {error && (
          <div role="alert" className="error">
            {error}
            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}
        {tab === "demo" && (
          <div className="demo-toolbar">
            <label>
              Experiment{" "}
              <select
                aria-label="Experiment"
                value={id}
                onChange={(e) => setId(e.target.value)}
              >
                {experiments.map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="primary"
              disabled={job?.status === "running"}
              onClick={start}
            >
              {job?.status === "running"
                ? "Demonstration running…"
                : "↗ Run fresh demonstration"}
            </button>
          </div>
        )}
        {job && (
          <div
            className={`job ${job.status === "failed" ? "error" : ""}`}
            role="status"
          >
            <strong>
              {job.status === "running" ? "LIVE" : job.status.toUpperCase()}
            </strong>{" "}
            {job.stage || job.error || "Fresh executable evidence saved."}{" "}
            <small>
              {job.id} · training ≤6,000 actions / 2,000 resets / 90s;
              evaluation separately ≤6,000 / 1,000 / 90s.
            </small>
          </div>
        )}
        {tab === "demo" ? (
          <Demo experiment={experiment} onError={onError} />
        ) : tab === "typed" ? (
          <Typed onError={onError} />
        ) : (
          <Benchmarks onError={onError} />
        )}
        <footer>
          <span>BLACKBOX TWIN / A LOCAL SCIENTIFIC WORKBENCH</span>
          <span>Behavioral evidence, bounded conclusions.</span>
        </footer>
      </main>
    </div>
  );
}
