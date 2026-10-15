/**
 * Automated smoke and API integration test suite for IdeaSprint AI
 * Run with: node tests/api.test.js
 */
import { generateProjectBlueprint } from "../lib/aiEngine.js";
import { PROJECT_PRESETS, getPresetById } from "../lib/presets.js";
import { exportToMarkdown } from "../lib/markdownExporter.js";
import { validateGenerateRequest, validateSimulationRequest } from "../lib/validator.js";

async function runTests() {
  console.log("🚀 Starting IdeaSprint AI Systematic Test Suite...");
  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`  ✅ PASS: ${message}`);
      passed++;
    } else {
      console.error(`  ❌ FAIL: ${message}`);
      failed++;
    }
  }

  // Test 1: Presets availability
  console.log("\n[Test 1] Presets verification");
  assert(Array.isArray(PROJECT_PRESETS) && PROJECT_PRESETS.length >= 5, "Presets list contains at least 5 curated hackathon projects");
  const devopsPreset = getPresetById("devops-incident-autopilot");
  assert(devopsPreset && devopsPreset.title === "IncidentPulse AI", "Can retrieve 'devops-incident-autopilot' preset");

  // Test 2: Request validation
  console.log("\n[Test 2] Request validation & sanitization");
  const validReq = validateGenerateRequest({ topic: "devops-incident-autopilot", track: "DevOps" });
  assert(validReq.valid === true, "Valid payload passes validation");
  const invalidReq = validateGenerateRequest({});
  assert(invalidReq.valid === false, "Empty payload correctly fails validation");
  const validSim = validateSimulationRequest({ input: "Sample error log", topic: "DevOps" });
  assert(validSim.valid === true, "Valid simulation payload passes validation");

  // Test 3: Blueprint Generation Pipeline
  console.log("\n[Test 3] Multi-Stage Blueprint Generation");
  const blueprint = await generateProjectBlueprint({ topic: "devops-incident-autopilot" });
  assert(blueprint && blueprint.pitch && blueprint.pitch.title === "IncidentPulse AI", "Blueprint generated with correct title");
  assert(blueprint.taskModelFit && blueprint.taskModelFit.fitScore > 80, "Task-model fit evaluated with high score");
  assert(blueprint.architecture && blueprint.architecture.frontend && blueprint.architecture.backend, "Fullstack architecture generated");
  assert(Array.isArray(blueprint.pitchSlides) && blueprint.pitchSlides.length === 5, "Pitch slides generated (5 slides)");
  assert(blueprint.interactiveSandbox && blueprint.interactiveSandbox.sampleOutputs.length > 0, "Interactive sandbox workflow populated");

  // Test 4: Markdown Exporter
  console.log("\n[Test 4] Markdown PRD Exporter");
  const md = exportToMarkdown(blueprint);
  assert(typeof md === "string" && md.includes("# IncidentPulse AI"), "Markdown PRD generated with header");
  assert(md.includes("Task-Model Fit Audit"), "Markdown PRD includes task-model fit audit");

  console.log(`\n===================================`);
  console.log(`Results: ${passed} passed, ${failed} failed`);
  console.log(`===================================`);

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error("Test suite threw uncaught error:", err);
  process.exit(1);
});
