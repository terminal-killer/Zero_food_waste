/**
 * Pipeline UI Visualizer: manages the multi-stage agent pipeline animation & log streaming
 */

export function runPipelineAnimation({ onComplete }) {
  const section = document.getElementById("pipeline-section");
  const fill = document.getElementById("pipeline-progress-fill");
  const percentText = document.getElementById("pipeline-percent");
  const heading = document.getElementById("pipeline-status-heading");
  const terminal = document.getElementById("terminal-output");

  section.classList.add("visible");
  section.scrollIntoView({ behavior: "smooth", block: "center" });

  const steps = [
    { card: "step-card-1", pct: 25, log: "[Agent: TaskFit] Auditing problem structure against LLM vs Deterministic boundary...", title: "Auditing Task-Model Fit..." },
    { card: "step-card-2", pct: 50, log: "[Agent: ProductStrategist] Synthesizing unfair advantage and user personas...", title: "Formulating Value Moat & Personas..." },
    { card: "step-card-3", pct: 75, log: "[Agent: SeniorArchitect] Generating fullstack REST API, SQL DDL & RAG parameters...", title: "Assembling Fullstack Architecture..." },
    { card: "step-card-4", pct: 100, log: "[Agent: DemoCompiler] Compiling interactive live sandbox & pitch deck slides...", title: "Finalizing Live Hackathon MVP!" }
  ];

  // Reset steps
  [1, 2, 3, 4].forEach(i => {
    const card = document.getElementById(`step-card-${i}`);
    card.classList.remove("active", "completed");
  });
  fill.style.width = "0%";
  percentText.innerText = "0%";

  let currentIdx = 0;

  function nextStep() {
    if (currentIdx >= steps.length) {
      setTimeout(() => {
        heading.innerHTML = "✓ Autonomous MVP Synthesis Complete!";
        addTerminalLog("[System] All pipeline stages verified and compiled successfully.", "badge-ok");
        if (onComplete) onComplete();
      }, 350);
      return;
    }

    const s = steps[currentIdx];
    heading.innerText = s.title;
    fill.style.width = `${s.pct}%`;
    percentText.innerText = `${s.pct}%`;

    const card = document.getElementById(s.card);
    card.classList.add("active");
    addTerminalLog(s.log, "badge-agent");

    setTimeout(() => {
      card.classList.remove("active");
      card.classList.add("completed");
      currentIdx++;
      nextStep();
    }, 450);
  }

  nextStep();
}

export function addTerminalLog(message, badgeClass = "badge-agent") {
  const terminal = document.getElementById("terminal-output");
  const line = document.createElement("div");
  line.className = "terminal-line";

  const time = new Date().toTimeString().split(" ")[0];
  line.innerHTML = `
    <span class="timestamp">[${time}]</span>
    <span class="${badgeClass}">[Pipeline]</span>
    <span>${message}</span>
  `;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}
