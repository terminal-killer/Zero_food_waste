/**
 * IdeaSprint AI - Main Frontend Application Orchestrator
 * Integrates Pipeline UI, Blueprint Viewer, Interactive Sandbox & Slide Deck
 */

import { runPipelineAnimation, addTerminalLog } from "./pipelineUI.js";
import { renderBlueprint } from "./blueprintUI.js";
import { initSandboxUI } from "./sandboxUI.js";
import { initSlidesUI } from "./slidesUI.js";

// Global Application State
const state = {
  presets: [],
  selectedPresetId: null,
  currentBlueprint: null,
  provider: "built-in",
  apiKey: ""
};

// UI Initialization
document.addEventListener("DOMContentLoaded", () => {
  initCountdownTimer(60); // 60-minute hackathon timer
  fetchPresets();
  initTabs();
  initGenerator();
  initSandboxUI(showToast);
  initRefinement();
  initExport();
  initSettingsModal();
});

/**
 * 60-minute countdown timer for hackathons
 */
function initCountdownTimer(minutes) {
  let secondsLeft = minutes * 60;
  const timerEl = document.getElementById("hackathon-timer");

  const interval = setInterval(() => {
    secondsLeft--;
    if (secondsLeft <= 0) {
      clearInterval(interval);
      timerEl.innerText = "00:00 - Time's Up!";
      showToast("Hackathon sprint time expired! Ready for final demo.", "warning");
      return;
    }
    const mins = Math.floor(secondsLeft / 60);
    const secs = secondsLeft % 60;
    timerEl.innerText = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')} remaining`;
  }, 1000);
}

/**
 * Toast Notification Helper
 */
export function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";

  const icons = {
    success: "✓",
    error: "✕",
    warning: "⚠️",
    info: "ℹ️"
  };

  const colors = {
    success: "var(--emerald)",
    error: "var(--rose)",
    warning: "var(--amber)",
    info: "var(--cyan)"
  };

  toast.style.borderColor = colors[type] || colors.info;
  toast.innerHTML = `
    <span style="font-weight: 700; color: ${colors[type]};">${icons[type] || icons.info}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(15px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/**
 * Fetch and render presets
 */
async function fetchPresets() {
  try {
    const res = await fetch("/api/presets");
    const data = await res.json();
    if (data.success && data.presets) {
      state.presets = data.presets;
      renderPresetsList(data.presets);
    }
  } catch (err) {
    console.error("Failed to load presets:", err);
    showToast("Could not load presets list. Using offline cache.", "warning");
  }
}

function renderPresetsList(presets) {
  const container = document.getElementById("presets-container");
  container.innerHTML = "";

  presets.forEach((p, index) => {
    const card = document.createElement("div");
    card.className = `glass-card preset-card ${index === 0 ? "active" : ""}`;
    card.dataset.id = p.id;

    if (index === 0) state.selectedPresetId = p.id;

    card.innerHTML = `
      <div>
        <div class="preset-icon">⚡</div>
        <div class="preset-track">${p.track}</div>
        <h4 class="preset-name">${p.title}</h4>
        <p class="preset-tagline">${p.tagline}</p>
      </div>
      <div style="font-size: 0.72rem; color: var(--emerald); font-weight: 600;">
        ${p.keyMetrics[0] || "High Impact MVP"}
      </div>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      state.selectedPresetId = p.id;
      document.getElementById("custom-topic-input").value = p.title;
      document.getElementById("track-select").value = p.track;
    });

    container.appendChild(card);
  });

  // Pre-fill input with first preset
  if (presets.length > 0) {
    document.getElementById("custom-topic-input").value = presets[0].title;
    document.getElementById("track-select").value = presets[0].track;
  }
}

/**
 * Generator Execution
 */
function initGenerator() {
  const btnGen = document.getElementById("btn-generate");
  const btnSurprise = document.getElementById("btn-surprise");
  const topicInput = document.getElementById("custom-topic-input");
  const trackSelect = document.getElementById("track-select");

  btnSurprise.addEventListener("click", () => {
    if (state.presets.length === 0) return;
    const randomPreset = state.presets[Math.floor(Math.random() * state.presets.length)];
    state.selectedPresetId = randomPreset.id;
    topicInput.value = randomPreset.title;
    trackSelect.value = randomPreset.track;

    document.querySelectorAll(".preset-card").forEach(c => {
      c.classList.toggle("active", c.dataset.id === randomPreset.id);
    });

    showToast(`Loaded "${randomPreset.title}"`, "info");
  });

  btnGen.addEventListener("click", async () => {
    const topic = topicInput.value.trim() || state.selectedPresetId;
    const track = trackSelect.value;

    if (!topic) {
      showToast("Please enter a concept or choose a preset.", "warning");
      return;
    }

    btnGen.disabled = true;
    btnGen.innerHTML = "<span>⏳ Synthesizing Full MVP...</span>";

    try {
      // Step 1: Start UI pipeline animation
      runPipelineAnimation({
        onComplete: async () => {
          // Step 2: Fetch generation result
          const res = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              topic: state.selectedPresetId || topic,
              track,
              customDescription: topicInput.value.trim(),
              provider: state.provider,
              apiKey: state.apiKey
            })
          });

          const data = await res.json();
          if (!data.success) {
            throw new Error(data.error || "Generation failed");
          }

          state.currentBlueprint = data.blueprint;

          // Step 3: Render blueprint into tabs
          renderBlueprint(data.blueprint);

          // Step 4: Initialize slide deck
          initSlidesUI(data.blueprint.pitchSlides);

          // Step 5: Update markdown preview
          updateMarkdownPreview(data.blueprint);

          showToast("🎉 Hackathon MVP Blueprint & Interactive Sandbox Ready!", "success");
          btnGen.disabled = false;
          btnGen.innerHTML = "<span>🚀 Generate Full MVP</span>";
        }
      });

    } catch (err) {
      console.error(err);
      showToast("Generation error: " + err.message, "error");
      btnGen.disabled = false;
      btnGen.innerHTML = "<span>🚀 Generate Full MVP</span>";
    }
  });
}

/**
 * Tab Switching
 */
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const targetPaneId = tab.dataset.tab;
      document.querySelectorAll(".tab-pane").forEach(pane => {
        pane.classList.remove("active");
        if (pane.id === targetPaneId) {
          pane.classList.add("active");
        }
      });
    });
  });
}

/**
 * Real-Time Blueprint Refinement
 */
function initRefinement() {
  const btnRefine = document.getElementById("btn-refine");
  const refineInput = document.getElementById("refine-input");
  const chips = document.querySelectorAll(".refine-chip");

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      refineInput.value = chip.dataset.inst;
      btnRefine.click();
    });
  });

  btnRefine.addEventListener("click", async () => {
    const inst = refineInput.value.trim();
    if (!inst) {
      showToast("Please enter a refinement instruction.", "warning");
      return;
    }

    if (!state.currentBlueprint) {
      showToast("Generate a blueprint first before refining.", "warning");
      return;
    }

    btnRefine.disabled = true;
    btnRefine.innerText = "Applying...";

    try {
      const res = await fetch("/api/refine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blueprint: state.currentBlueprint,
          instruction: inst
        })
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      state.currentBlueprint = data.blueprint;
      renderBlueprint(data.blueprint);
      updateMarkdownPreview(data.blueprint);
      showToast(data.message || "Blueprint refined successfully!", "success");
      refineInput.value = "";
    } catch (err) {
      console.error(err);
      showToast("Refinement failed: " + err.message, "error");
    } finally {
      btnRefine.disabled = false;
      btnRefine.innerText = "Update Blueprint";
    }
  });
}

/**
 * Export and PRD Handling
 */
function initExport() {
  const btnDownload = document.getElementById("btn-download-md");
  const btnCopy = document.getElementById("btn-copy-md");

  btnDownload.addEventListener("click", async () => {
    if (!state.currentBlueprint) {
      showToast("No active blueprint to export.", "warning");
      return;
    }

    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blueprint: state.currentBlueprint })
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${state.currentBlueprint.pitch.title.replace(/\s+/g, '_')}_PRD_Blueprint.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("Downloaded PRD & Pitch kit markdown!", "success");
    } catch (err) {
      console.error(err);
      showToast("Download failed.", "error");
    }
  });

  btnCopy.addEventListener("click", () => {
    const preview = document.getElementById("export-markdown-preview").innerText;
    if (!preview) {
      showToast("No markdown content to copy.", "warning");
      return;
    }
    navigator.clipboard.writeText(preview).then(() => {
      showToast("Copied full PRD Markdown to clipboard!", "success");
    }).catch(() => {
      showToast("Failed to copy to clipboard.", "error");
    });
  });
}

async function updateMarkdownPreview(blueprint) {
  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blueprint })
    });
    const markdownText = await res.text();
    document.getElementById("export-markdown-preview").innerText = markdownText;
  } catch (err) {
    console.error("Failed to generate preview:", err);
  }
}

/**
 * Settings Modal
 */
function initSettingsModal() {
  const modal = document.getElementById("settings-modal");
  const btnSettings = document.getElementById("btn-settings");
  const btnClose = document.getElementById("btn-close-modal");
  const btnCancel = document.getElementById("btn-cancel-settings");
  const btnSave = document.getElementById("btn-save-settings");
  const providerSelect = document.getElementById("setting-provider");
  const apiKeyInput = document.getElementById("setting-api-key");

  btnSettings.onclick = () => modal.classList.add("visible");
  btnClose.onclick = () => modal.classList.remove("visible");
  btnCancel.onclick = () => modal.classList.remove("visible");

  modal.onclick = (e) => {
    if (e.target === modal) modal.classList.remove("visible");
  };

  btnSave.onclick = () => {
    state.provider = providerSelect.value;
    state.apiKey = apiKeyInput.value.trim();
    modal.classList.remove("visible");
    showToast(`Saved settings: Provider is ${state.provider === 'built-in' ? 'Built-in Engine' : 'Google Gemini'}`, "success");
  };
}
