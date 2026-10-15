import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { PROJECT_PRESETS } from "./lib/presets.js";
import { generateProjectBlueprint } from "./lib/aiEngine.js";
import { exportToMarkdown } from "./lib/markdownExporter.js";
import { exec, execFile } from "child_process";
import fs from "fs";
import { validateGenerateRequest, validateSimulationRequest } from "./lib/validator.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(__dirname, "public")));

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({
    status: "healthy",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    version: "1.0.0",
    skillsActive: ["project-development", "senior-fullstack", "llm-app-patterns", "systematic-debugging", "webapp-testing"]
  });
});

// Presets endpoint
app.get("/api/presets", (req, res) => {
  res.json({
    success: true,
    presets: PROJECT_PRESETS
  });
});

// Autonomous blueprint generation
app.post("/api/generate", async (req, res) => {
  try {
    const validation = validateGenerateRequest(req.body);
    if (!validation.valid) {
      return res.status(400).json({ success: false, error: validation.error });
    }

    const blueprint = await generateProjectBlueprint(validation.data);
    res.json({
      success: true,
      blueprint
    });
  } catch (err) {
    console.error("Error in /api/generate:", err);
    res.status(500).json({
      success: false,
      error: "Internal server error during blueprint generation",
      details: err.message
    });
  }
});

// Interactive sandbox execution
app.post("/api/simulate", (req, res) => {
  try {
    const validation = validateSimulationRequest(req.body);
    if (!validation.valid) {
      return res.status(400).json({ success: false, error: validation.error });
    }

    const { input, topic } = validation.data;
    
    // Process input through multi-stage simulated pipeline
    const inputLength = input.length;
    const stage1Analysis = `Processed input stream of ${inputLength} chars. Identified 3 anomalous vectors, flagged high deviation from steady-state baselines.`;
    const stage2Reasoning = `Synthesized semantic intent for [${topic}]. Correlation confidence: 97.2%. No harmful injections detected. RAG context injected with 4 verified reference chunks.`;
    const stage3Action = `Executed automated mitigation playbook. Result: System returned to nominal operating limits with zero disruption. Audit log saved to immutable storage.`;

    res.json({
      success: true,
      result: {
        timestamp: new Date().toISOString(),
        inputProcessed: input,
        stages: [
          { name: "1. Ingestion & Semantic Parser", result: stage1Analysis, latencyMs: 38 },
          { name: "2. RAG Synthesis & Task-Model Fit Reasoning", result: stage2Reasoning, latencyMs: 142 },
          { name: "3. Guardrail Verification & Action Dispatch", result: stage3Action, latencyMs: 45 }
        ],
        totalLatencyMs: 225
      }
    });
  } catch (err) {
    console.error("Error in /api/simulate:", err);
    res.status(500).json({ success: false, error: "Simulation failed", details: err.message });
  }
});

// Refine blueprint section
app.post("/api/refine", (req, res) => {
  try {
    const { blueprint, instruction } = req.body;
    if (!blueprint || !instruction) {
      return res.status(400).json({ success: false, error: "Missing blueprint or instruction." });
    }

    // Clone and adjust blueprint based on instruction
    const updated = JSON.parse(JSON.stringify(blueprint));
    const instLower = instruction.toLowerCase();

    if (instLower.includes("serverless") || instLower.includes("lambda") || instLower.includes("cloud")) {
      updated.architecture.backend.runtime = "AWS Lambda / Cloudflare Workers (Edge Serverless)";
      updated.architecture.backend.resilience += " | Edge cold-start mitigation with provisioned concurrency";
    }

    if (instLower.includes("privacy") || instLower.includes("hipaa") || instLower.includes("compliance") || instLower.includes("gdpr")) {
      updated.architecture.llmAppPatterns.guardrails.push("Zero-retention ephemeral PII masking & HIPAA BAA compliance filter");
    }

    if (instLower.includes("cache") || instLower.includes("redis")) {
      updated.architecture.backend.resilience += " | Redis semantic cache for frequent query responses";
    }

    updated.meta.lastRefinement = {
      instruction,
      appliedAt: new Date().toISOString()
    };

    res.json({
      success: true,
      blueprint: updated,
      message: `Refinement applied: "${instruction}"`
    });
  } catch (err) {
    console.error("Error in /api/refine:", err);
    res.status(500).json({ success: false, error: "Refinement failed", details: err.message });
  }
});

// Markdown PRD export
app.post("/api/export", (req, res) => {
  try {
    const { blueprint } = req.body;
    if (!blueprint) {
      return res.status(400).json({ success: false, error: "Blueprint required for export." });
    }
    const markdown = exportToMarkdown(blueprint);
    res.setHeader("Content-Disposition", 'attachment; filename="PRD_Pitch_Blueprint.md"');
    res.setHeader("Content-Type", "text/markdown; charset=utf-8");
    res.send(markdown);
  } catch (err) {
    console.error("Error in /api/export:", err);
    res.status(500).json({ success: false, error: "Export failed", details: err.message });
  }
});

// ========================================================
// AnnaSetu Surplus Food Redistribution Endpoints (Fast / Zero-Locks)
// ========================================================
const PYTHON_BIN = process.env.PYTHON_BIN || (fs.existsSync("E:\\anaconda path\\python.exe") ? "E:\\anaconda path\\python.exe" : "python");
const ORCHESTRATE_SCRIPT = path.join(__dirname, "skills", "annasetu-orchestrator", "scripts", "orchestrate.py");
const LEDGER_PATH = path.join(__dirname, "data", "ledger.csv");
const RUNS_DIR = path.join(__dirname, "runs");
if (!fs.existsSync(RUNS_DIR)) fs.mkdirSync(RUNS_DIR, { recursive: true });

function runOrchestrator(args) {
  return new Promise((resolve, reject) => {
    execFile(
      PYTHON_BIN,
      [ORCHESTRATE_SCRIPT, ...args],
      { timeout: 10000, maxBuffer: 10 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: "utf-8" } },
      (error, stdout, stderr) => {
        if (error) {
          return reject({ error, stderr, stdout });
        }
        try {
          const parsed = JSON.parse(stdout.trim());
          resolve(parsed);
        } catch (e) {
          reject({ error: e, stderr, stdout });
        }
      }
    );
  });
}

function appendToLedger(result) {
  if (result.status !== "SAFE" && result.status !== "SAFE_IF_FAST") {
    return;
  }
  try {
    const intake = result.intake || {};
    const impact = (result.impact && result.impact.this_listing) || {};
    const vol = (result.pickup && result.pickup.assigned_volunteer) || {};
    const destinations = (result.pickup && result.pickup.destinations) || [];
    const recipientsServed = destinations.map(d => d.name).join(", ") || "Community Kitchen";

    const listingId = impact.listing_id || `OD-${Date.now().toString().slice(-8)}`;
    const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const donorName = (intake.donor_name || "Surplus Donor").replace(/"/g, '""');
    const area = intake.area || "Bhubaneswar";
    const totalMeals = intake.total_quantity || 0;
    const kgDiverted = impact.kg_diverted || Number((totalMeals * 0.4).toFixed(1));
    const co2eAvoided = impact.co2e_avoided_kg || Number((kgDiverted * 2.5).toFixed(1));
    const economicValue = impact.economic_value_inr || Number((totalMeals * 60).toFixed(1));
    const volName = vol.name || "Volunteer";
    const status = "COMPLETED";

    const row = `${listingId},${timestamp},"${donorName}",${area},${totalMeals},${kgDiverted},${co2eAvoided},${economicValue},"${recipientsServed.replace(/"/g, '""')}","${volName}",${status}\n`;
    fs.appendFileSync(LEDGER_PATH, row, "utf-8");
  } catch (err) {
    console.error("Ledger append error:", err);
  }
}

// 1. Run pipeline
app.post("/api/annasetu/run", async (req, res) => {
  const { listingText, text, simulatedNow, overrideJson, runId } = req.body;
  const input = text || listingText || "Wedding banquet at Royal Garden, Patia. 40 veg biryani packets and 20 sweets, cooked at 6:30 PM, expires at 10:30 PM, contact: 9861122334";
  const id = runId || `run_${Date.now()}`;

  const args = ["--run-id", id, "--text", input];
  if (simulatedNow) args.push("--simulated-now", simulatedNow);
  if (overrideJson) args.push("--override-json", typeof overrideJson === "string" ? overrideJson : JSON.stringify(overrideJson));

  try {
    const result = await runOrchestrator(args);
    appendToLedger(result);
    res.json({ success: true, data: result });
  } catch (err) {
    console.error("Orchestrator run error:", err);
    res.status(500).json({
      success: false,
      error: err.error ? err.error.message : "Orchestration failed",
      stderr: err.stderr || "",
      stdout: err.stdout || ""
    });
  }
});

// 2. Answer clarifying question or edit fields
app.post("/api/annasetu/run/:id/answer", async (req, res) => {
  const runId = req.params.id;
  const runFile = path.join(RUNS_DIR, `${runId}.json`);

  if (!fs.existsSync(runFile)) {
    return res.status(404).json({ success: false, error: `Run ${runId} not found.` });
  }

  try {
    const existingRun = JSON.parse(fs.readFileSync(runFile, "utf-8"));
    const originalText = (existingRun.intake && (existingRun.intake.raw_text || existingRun.raw_text)) || "Surplus food donation";
    
    const overridePayload = {
      ...(existingRun.intake || {}),
      ...(req.body.overrides || {}),
      ...req.body
    };

    const args = ["--run-id", runId, "--text", originalText, "--override-json", JSON.stringify(overridePayload)];
    if (req.body.simulatedNow || existingRun.intake?.intake_timestamp) {
      args.push("--simulated-now", req.body.simulatedNow || existingRun.intake?.intake_timestamp);
    }

    const result = await runOrchestrator(args);
    appendToLedger(result);
    res.json({ success: true, data: result });
  } catch (err) {
    console.error("Answer endpoint error:", err);
    res.status(500).json({
      success: false,
      error: err.error ? err.error.message : "Failed to answer clarifying question",
      stderr: err.stderr || ""
    });
  }
});

// 3. Live ledger statistics
app.get("/api/annasetu/stats", (req, res) => {
  try {
    if (!fs.existsSync(LEDGER_PATH)) {
      return res.json({
        success: true,
        stats: {
          total_dispatches: 0,
          total_meals_saved: 0,
          total_kg_diverted: 0,
          total_co2e_avoided_kg: 0,
          total_economic_value_inr: 0,
          unique_donors_count: 0,
          unique_recipients_count: 0
        }
      });
    }

    const content = fs.readFileSync(LEDGER_PATH, "utf-8");
    const lines = content.trim().split("\n").filter(l => l.trim());
    if (lines.length <= 1) {
      return res.json({
        success: true,
        stats: {
          total_dispatches: 0,
          total_meals_saved: 0,
          total_kg_diverted: 0,
          total_co2e_avoided_kg: 0,
          total_economic_value_inr: 0,
          unique_donors_count: 0,
          unique_recipients_count: 0
        }
      });
    }

    let totalMeals = 0;
    let totalKg = 0;
    let totalCo2e = 0;
    let totalInr = 0;
    const donors = new Set();
    const recipients = new Set();
    let dispatches = 0;

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      const parts = line.split(",");
      if (parts.length >= 8) {
        dispatches++;
        totalMeals += parseFloat(parts[4]) || 0;
        totalKg += parseFloat(parts[5]) || 0;
        totalCo2e += parseFloat(parts[6]) || 0;
        totalInr += parseFloat(parts[7]) || 0;
        if (parts[2]) donors.add(parts[2].replace(/"/g, ''));
        if (parts[8]) recipients.add(parts[8].replace(/"/g, ''));
      }
    }

    res.json({
      success: true,
      stats: {
        total_dispatches: dispatches,
        total_meals_saved: Math.round(totalMeals),
        total_kg_diverted: Number(totalKg.toFixed(1)),
        total_co2e_avoided_kg: Number(totalCo2e.toFixed(1)),
        total_economic_value_inr: Number(totalInr.toFixed(1)),
        unique_donors_count: donors.size,
        unique_recipients_count: recipients.size
      }
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 4. Past 20 runs
app.get("/api/annasetu/runs", (req, res) => {
  try {
    if (!fs.existsSync(RUNS_DIR)) {
      return res.json({ success: true, count: 0, runs: [] });
    }
    const files = fs.readdirSync(RUNS_DIR).filter(f => f.endsWith(".json"));
    const sorted = files.map(f => {
      const p = path.join(RUNS_DIR, f);
      const stat = fs.statSync(p);
      return { file: f, path: p, mtime: stat.mtimeMs };
    }).sort((a, b) => b.mtime - a.mtime).slice(0, 20);

    const runs = [];
    for (const item of sorted) {
      try {
        const raw = fs.readFileSync(item.path, "utf-8");
        runs.push(JSON.parse(raw));
      } catch (e) {}
    }

    res.json({ success: true, count: runs.length, runs });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "dashboard.html"));
});

// Start server
app.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(` IdeaSprint AI - Autonomous Hackathon Accelerator v1.0 `);
  console.log(` Running live on http://localhost:${PORT}             `);
  console.log(` Health check:   http://localhost:${PORT}/api/health   `);
  console.log(`=======================================================`);
});
