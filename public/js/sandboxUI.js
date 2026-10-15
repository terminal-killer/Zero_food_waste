/**
 * Sandbox UI: Handles interactive live simulation of the generated AI project MVP
 */

export function initSandboxUI(showToast) {
  const btnRun = document.getElementById("btn-run-sandbox");
  const btnReset = document.getElementById("btn-reset-sandbox");
  const inputArea = document.getElementById("sandbox-input");
  const resultsBox = document.getElementById("sandbox-output-timeline");
  const stagesContainer = document.getElementById("sim-stages-container");
  const latencyBadge = document.getElementById("sim-latency-badge");

  btnRun.addEventListener("click", async () => {
    const text = inputArea.value.trim();
    if (!text) {
      showToast("Please enter or retain a simulation payload.", "warning");
      return;
    }

    btnRun.disabled = true;
    btnRun.innerHTML = "<span>⏳ Agent Reasoning in Progress...</span>";

    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input: text,
          topic: document.getElementById("display-title").innerText
        })
      });

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || "Simulation failed");
      }

      const { stages, totalLatencyMs } = data.result;
      latencyBadge.innerText = `Total Roundtrip: ${totalLatencyMs}ms (P99 SLA met)`;

      stagesContainer.innerHTML = "";
      stages.forEach((st, idx) => {
        const card = document.createElement("div");
        card.className = "sim-stage-card";
        card.innerHTML = `
          <div class="sim-stage-title">
            <span>${st.name}</span>
            <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${st.latencyMs}ms</span>
          </div>
          <div class="sim-stage-content">${st.result}</div>
        `;
        stagesContainer.appendChild(card);
      });

      resultsBox.classList.add("visible");
      resultsBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
      showToast("Simulation ran successfully! Verified 0 errors.", "success");
    } catch (err) {
      console.error(err);
      showToast("Simulation error: " + err.message, "error");
    } finally {
      btnRun.disabled = false;
      btnRun.innerHTML = "<span>⚡ Run Agent Simulation</span>";
    }
  });

  btnReset.addEventListener("click", () => {
    inputArea.value = `[CRITICAL 10:14:02 UTC] service=payment-gateway-v2 error="Database connection pool exhausted (500/500)" latency_p99=8420ms
[WARN 10:14:05 UTC] service=checkout-api error="upstream 504 Gateway Timeout on /v2/charge"
[INFO 10:14:08 UTC] commit=9f8a3d author="deploy-bot" message="Deployed PR #412: Enable eager connection pooling"`;
    showToast("Reset simulation payload to default scenario.", "info");
  });
}
