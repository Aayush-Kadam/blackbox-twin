import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync, readdirSync } from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";
import {
  percent,
  Badge,
  TraceTable,
  ModelGraph,
  SupportRows,
  BenchmarkTable,
} from "../src/App.jsx";

const read = (path) => JSON.parse(readFileSync(path, "utf8"));
const loop = "../evidence/m3-demo/loop";
const caseFolder = readdirSync(`${loop}/counterexamples`)[0];
const record = read(`${loop}/counterexamples/${caseFolder}/discovery.json`);

test("undefined conditional accuracy is not rendered as perfect accuracy", () => {
  assert.equal(percent(null), "—");
  assert.equal(percent(undefined), "—");
  assert.equal(percent(0), "0.00%");
  assert.equal(percent(1), "100.00%");
});
for (const status of [
  "OBSERVED",
  "INFERRED_SUPPORTED",
  "AMBIGUOUS",
  "UNSUPPORTED",
]) {
  test(`support category ${status} has a visible text label`, () => {
    assert.match(
      renderToStaticMarkup(<Badge status={status} />),
      new RegExp(`>${status}<`),
    );
  });
}
for (const kind of ["original", "minimized"]) {
  test(`persisted ${kind} counterexample exposes real outputs and one first divergence`, () => {
    const comparison = record.minimization[kind];
    const html = renderToStaticMarkup(<TraceTable comparison={comparison} />);
    assert.equal((html.match(/First divergence/g) || []).length, 1);
    assert.match(
      html,
      new RegExp(
        `<td>${comparison.first_divergence + 1}<small>First divergence`,
      ),
    );
    assert.match(html, /accepted/);
    assert.equal(
      (html.match(/<tr/g) || []).length,
      comparison.actions.length + 1,
    );
  });
}
for (const revision of ["000", "001"]) {
  test(`revision ${revision} graph uses the persisted learned transitions`, () => {
    const model = read(`${loop}/revisions/${revision}/model.json`);
    const html = renderToStaticMarkup(
      <ModelGraph
        model={model}
        selected={model.initial_state}
        onSelect={() => {}}
      />,
    );
    assert.match(
      html,
      new RegExp(
        `Learned model with ${Object.keys(model.transitions).length} states`,
      ),
    );
    for (const name of Object.keys(model.transitions[model.initial_state]))
      assert.match(html, new RegExp(name));
  });
}
test("abstention is explicitly labelled, with unknown state and evidence disclosure", () => {
  const html = renderToStaticMarkup(
    <SupportRows
      rows={[
        {
          action: { operation: "withdraw" },
          state_before: [0, false],
          state_after: null,
          output: { bbt_unsupported: true },
          support: { status: "AMBIGUOUS", reason: "unit-test ambiguity" },
          evidence: [],
        },
      ]}
    />,
  );
  assert.match(html, /Abstention/);
  assert.match(html, /State stays unknown until reset/);
  assert.match(html, /physical evidence references/);
  assert.match(html, /→ null/);
});
test("inventory incompatibility, zero coverage and null accuracy remain visible", () => {
  const result = read("../evidence/m6-confirmatory-v1/results.json").find(
    (r) => r.track === "C" && r.method === "hardened",
  );
  const point = result.points[0];
  const html = renderToStaticMarkup(
    <BenchmarkTable
      cells={[
        {
          ...result,
          ...point,
          metrics: point.metrics.overall,
          status: result.training.status,
        },
      ]}
    />,
  );
  assert.match(html, /model_class_unsupported/);
  assert.match(html, /0.00%/);
  assert.match(html, /—/);
  assert.match(html, /Not reached/);
});
