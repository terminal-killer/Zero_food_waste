# Autonomous Hackathon Engineering Playbook (60-Minute Sprint)

> **Role:** Autonomous Senior Hackathon Engineering Team  
> **Workspace:** `e:\softwares\ML projects\ideasprint`  
> **Frameworks & Principles:** `@project-development`, `@planning-and-task-breakdown`, `@senior-fullstack`, `@high-end-visual-design`, `@llm-app-patterns`, `@systematic-debugging`, `@webapp-testing`, `@verification-before-completion`

---

## 1. Rapid Project-Selection Process (5 Minutes)

When the hackathon theme/problem statement is announced:

1. **Task-Model Fit Filter (`@project-development`)**:
   - *Pass Criteria:* High synthesis across unstructured data, semantic categorization, natural language explanation, error tolerance.
   - *Fail Criteria:* Pure deterministic arithmetic, sub-millisecond execution, zero-hallucination tolerance without guardrails.
2. **Moat & Unfair Advantage (`@senior-fullstack`)**:
   - Hybrid architecture: deterministic fast ingestion + LLM reasoning + schema guardrail.
3. **Judge Appeal Formula**:
   - **Immediate Visual WOW:** Agency-grade dark glassmorphism, glowing micro-interactions, responsive layouts (`@high-end-visual-design`).
   - **Interactive Live Sandbox:** Judges can input data and test live inference directly in the browser.
   - **Pitch Deck Mode:** Fullscreen slide carousel tailored to judging criteria.

---

## 2. 60-Minute Implementation Schedule (`@planning-and-task-breakdown`)

| Time Window | Milestone | Key Deliverables & Validation Gate |
|-------------|-----------|-------------------------------------|
| **00:00 - 05:00** | Problem Selection & Decomposition | Select high-fit idea, define REST contract, establish deterministic vs LLM boundaries. |
| **05:00 - 15:00** | Backend API & Ingestion Engine | REST endpoints (`/api/generate`, `/api/simulate`, `/api/refine`), schema validation, health check. |
| **15:00 - 30:00** | AI Pipeline & Reasoning Core | Hybrid synthesis engine (`@llm-app-patterns`), prompt templates, resilience fallback. |
| **30:00 - 45:00** | Frontend UI & Interactive Sandbox | Glassmorphism dashboard, multi-agent progress runner, sandbox playground, slide deck (`@high-end-visual-design`). |
| **45:00 - 55:00** | End-to-End Testing & Debugging | Headless browser journey validation (`@webapp-testing`), unit tests (`tests/api.test.js`), root cause fixes (`@systematic-debugging`). |
| **55:00 - 60:00** | Demo Polish & Pitch Verification | Final smoke test, verify Markdown PRD export, slide deck presentation walkthrough (`@verification-before-completion`). |

---

## 3. Coding & Systematic Testing Workflow

### Core Development Rules
- **No Mockup Only:** The system must run end-to-end with real REST endpoints and functional interactive controls.
- **Fail Gracefully:** Built-in intelligent synthesis engine ensures 100% uptime with zero external API key dependency, while seamlessly supporting live Gemini/OpenAI keys when provided.
- **Systematic Debugging Iron Law (`@systematic-debugging`)**:
  ```
  NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
  ```
  Inspect server logs and network responses before patching.

### Automated Test Verification Gate (`@verification-before-completion`)
Run automated smoke tests before claiming readiness:
```bash
node tests/api.test.js
```

---

## 4. Run & Build Commands

All commands run directly in `e:\softwares\ML projects\ideasprint`:

```bash
# 1. Install dependencies
npm install

# 2. Run automated test suite
npm test
# or
node tests/api.test.js

# 3. Start the production/dev server
npm start
# Server listens at http://localhost:3000
# Health check: http://localhost:3000/api/health
```

---

## 5. Procedure for API Keys & Unavailable Services

- **Zero-Dependency Default Mode:** IdeaSprint AI ships with a high-fidelity built-in neural generation engine that runs locally with sub-second latency. No API keys are required for judging or local evaluation.
- **Live Provider Integration:**
  - If a live Gemini API key or OpenAI key is available, open the **⚙️ Settings** modal in the UI or set `GEMINI_API_KEY` / `OPENAI_API_KEY` in `.env`.
  - The backend automatically validates keys and falls back safely to the local synthesizer if rate-limited or offline.

---

## 6. Final Demo Checklist (Pre-Pitch Verification)

- [ ] **Server Online:** Server running and healthy on `http://localhost:3000/api/health`.
- [ ] **Preset Demonstration:** Select a preset (e.g., *IncidentPulse AI* or *AetherMed Copilot*) and trigger **🚀 Generate Full MVP**.
- [ ] **Pipeline Execution:** Confirm all 4 agent stages animate and agent terminal logs populate.
- [ ] **Tab Exploration:** Verify **Pitch & Moat**, **Task-Model Fit**, **System Architecture**, **Interactive Sandbox**, **Pitch Deck**, and **Export PRD** tabs.
- [ ] **Live Interactive Sandbox:** Click **⚡ Run Agent Simulation** and show judges the live multi-stage reasoning outputs and latency metrics.
- [ ] **Live Refinement:** Click a quick modifier (e.g. *Make Architecture Serverless*) to demonstrate real-time adaptability.
- [ ] **Pitch Presentation:** Open **📽️ Pitch Deck Mode** and advance slides using arrow keys.
- [ ] **Export:** Verify **📥 Download PRD.md** produces a comprehensive submission document.
