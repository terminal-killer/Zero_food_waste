/**
 * Blueprint UI: renders full project blueprint into DOM tabs
 */

export function renderBlueprint(blueprint) {
  const { pitch, taskModelFit, architecture, interactiveSandbox, pitchSlides } = blueprint;

  // 1. Pitch & Moat Tab
  document.getElementById("display-title").innerText = pitch.title;
  document.getElementById("display-tagline").innerText = pitch.tagline;
  document.getElementById("display-track").innerText = pitch.track;
  document.getElementById("display-summary").innerText = pitch.summary;
  document.getElementById("display-problem").innerText = pitch.problemStatement;
  document.getElementById("display-solution").innerText = pitch.solutionStatement;
  document.getElementById("display-moat").innerText = pitch.unfairAdvantage;

  const personasList = document.getElementById("display-personas");
  personasList.innerHTML = "";
  pitch.targetPersonas.forEach(p => {
    const li = document.createElement("li");
    li.innerText = p;
    personasList.appendChild(li);
  });

  const metricsList = document.getElementById("display-metrics");
  metricsList.innerHTML = "";
  pitch.keyMetrics.forEach(m => {
    const li = document.createElement("li");
    li.innerText = m;
    metricsList.appendChild(li);
  });

  // 2. Task-Model Fit Tab
  document.getElementById("fit-score-num").innerText = taskModelFit.fitScore;
  document.getElementById("fit-verdict-text").innerText = taskModelFit.verdict;
  document.getElementById("fit-synthesis-text").innerHTML = `<strong>Synthesis:</strong> ${taskModelFit.analysis.synthesisSuitability}`;
  document.getElementById("fit-reasoning-text").innerHTML = `<strong>Reasoning:</strong> ${taskModelFit.analysis.subjectiveJudgmentSuitability}`;
  document.getElementById("fit-boundary-text").innerHTML = `<strong>Deterministic Boundary:</strong> ${taskModelFit.analysis.deterministicBoundary}`;
  document.getElementById("fit-latency-text").innerHTML = `<strong>Latency Budget:</strong> ${taskModelFit.analysis.latencyBudget}`;

  const tableBody = document.getElementById("division-table-body");
  tableBody.innerHTML = "";
  taskModelFit.llmVsCodeDivision.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${row.component}</strong></td>
      <td><span style="color: var(--cyan); font-weight: 600;">${row.handling}</span></td>
      <td style="color: var(--text-muted);">${row.reason}</td>
    `;
    tableBody.appendChild(tr);
  });

  // 3. Architecture Tab
  document.getElementById("arch-frontend-stack").innerText = architecture.frontend.framework;
  document.getElementById("arch-frontend-state").innerText = architecture.frontend.stateManagement;
  document.getElementById("arch-frontend-tokens").innerText = architecture.frontend.visualTokens;

  document.getElementById("arch-backend-runtime").innerText = architecture.backend.runtime;
  document.getElementById("arch-backend-framework").innerText = architecture.backend.framework;
  document.getElementById("arch-backend-resilience").innerText = architecture.backend.resilience;

  document.getElementById("arch-llm-pattern").innerText = architecture.llmAppPatterns.pattern;
  document.getElementById("arch-llm-retrieval").innerText = architecture.llmAppPatterns.retrievalMethod;
  document.getElementById("arch-llm-chunking").innerText = architecture.llmAppPatterns.chunkingStrategy;

  const guardrailsList = document.getElementById("arch-llm-guardrails");
  guardrailsList.innerHTML = "";
  architecture.llmAppPatterns.guardrails.forEach(g => {
    const li = document.createElement("li");
    li.innerText = g;
    guardrailsList.appendChild(li);
  });

  // DB SQL
  let sql = "";
  architecture.databaseSchema.tables.forEach(t => {
    sql += `-- Table: ${t.name}\nCREATE TABLE ${t.name} (\n  ${t.columns.join(",\n  ")}\n);\n\n`;
  });
  document.getElementById("arch-db-sql").innerText = sql || "-- Schema ready";

  // 4. Interactive Sandbox setup
  document.getElementById("sandbox-headline").innerText = interactiveSandbox.simulationTitle;
  document.getElementById("sandbox-input-label").innerText = interactiveSandbox.inputLabel;
  document.getElementById("sandbox-input").value = interactiveSandbox.defaultInput;

  // Make Blueprint section visible
  const blueprintSection = document.getElementById("blueprint-section");
  blueprintSection.classList.add("visible");
  blueprintSection.scrollIntoView({ behavior: "smooth", block: "start" });
}
