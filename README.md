# MCP Server: MLOps Inspector

An enterprise-grade Model Context Protocol (MCP) server that empowers LLM agents (e.g., Claude, Cursor, Gemini) to monitor model deployments, fetch real-time inference metrics, compute input feature drift, and dynamically adjust model routing policies.

This repository is designed to showcase production-ready MLOps observability integration in agentic workflows. It is part of the [rizkashif](https://github.com/rizkashif) profile example portfolio.

---

## Architecture Overview

```text
┌─────────────────┐        Model Context Protocol        ┌────────────────────────────┐
│   LLM Agent /   │ <──────────────────────────────────> │ mcp-server-mlops-inspector │
│ Claude Desktop  │             JSON-RPC                 └─────────────┬──────────────┘
└─────────────────┘                                                    │
                                         ┌─────────────────────────────┼─────────────────────────────┐
                                         ▼                             ▼                             ▼
                            ┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐
                            │    Model Registry      │    │  Metrics & Analytics   │    │      Drift Engine      │
                            │  Active model versions │    │ Latency, RPS, error %  │    │ PSI / KS-test analysis │
                            └────────────────────────┘    └────────────────────────┘    └────────────────────────┘
```

---

## Exposed Capabilities

### 1. Tools (Actions the Agent Can Take)
* **`list_deployed_models`**: Returns the active model versions, their environments (`Production`, `Staging`), current status, and active routing weights.
* **`get_realtime_metrics`**: Returns throughput (RPS), latencies (P50, P95, P99), error rates, and inference costs.
* **`fetch_drift_analysis`**: Calculates feature distribution drift using Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests between reference baselines and production inputs.
* **`modify_routing_weight`**: Updates routing configurations (e.g., shifts traffic away from a degraded/drifted model to a fallback/older model).

### 2. Resources (Live Data Feeds)
* **`model-registry://active-models`**: Lists registered models and current health summaries.
* **`observability://alerts/active`**: Live stream of active MLOps warnings (e.g., error rate spikes or high drift indices).

### 3. Prompts (Pre-configured Agent Workflows)
* **`diagnose_model_health`**: A workflow guiding the agent to read active alerts, query metrics, run statistical drift diagnostics, and recommend/perform routing fixes.

---

## Use Cases & Target Workflows

By acting as the interactive agentic layer over your MLOps telemetry, this server transforms passive metrics into an active, self-healing control plane. It supports both deep technical diagnostics and intuitive business-facing workflows.

### 1. Technical Workflows (SRE, MLOps, & Data Scientists)

#### 🛠️ On-Call Copilot & Troubleshooting
Instead of logging in, hunting through metrics, and manually running rollback scripts, the agent serves as an active co-pilot.
* **How it works:** When a latency or error rate alert is fired, the agent triggers the `diagnose_model_health` prompt workflow. It queries `observability://alerts/active`, fetches real-time operational data, computes feature drift, pinpoints the root cause, and automatically generates mitigation plans.

#### 📊 Conversational Registry & Cost Queries
Technical users can interact with model registries using natural language, removing the need to navigate complex dashboards or write custom SQL/GraphQL queries.
* **Example Agent Queries:**
  * *"Who is our highest-costing model this week and what is its average latency?"*
  * *"List all models in Staging that have been completely inactive for over 48 hours."*
* **Under the Hood:** The agent calls `list_deployed_models` and `get_realtime_metrics`, automatically aggregating the logs into clean Markdown reports.

#### 🔀 Automated Chaos Engineering & Shadow Testing
Safely test staging models under production-like scenarios with automated safety nets.
* **How it works:** You can ask the agent: *"Direct 10% of traffic to version `v2-beta`, run a load test, and if the error rate spikes above 1%, immediately revert back to `v1`."* The agent uses `modify_routing_weight` to manipulate traffic, monitors the outcomes, and acts as the automated safety switch.

---

### 2. Business & Operational Workflows (Product Managers & Operations)

#### 💬 ChatOps: Slack / MS Teams Integrations
Brings MLOps out of siloed dashboards and directly into your company's communication hub.
* **The User Query:** 
  > *"@MLOpsBot, is the fraud detection model running fine? Customers are complaining about transaction delays."*
* **The Behind-the-Scenes Action:** The bot parses this query, calls `get_realtime_metrics` and `fetch_drift_analysis` through the MCP server, and discovers a feature drift anomaly.
* **The Bot Reply:** 
  > *"The fraud model is online (average latency is normal at 15ms). However, the `transaction_amount` distribution has drifted today (PSI: 0.32). I recommend routing traffic to the stable fallback version. Click below to execute."*
  > `[ Approve Rollback to v1 ]`  `[ View Detailed Metrics ]`

#### 🧭 Embedded Dashboard Copilot Sidebar
Add a natural language sidebar widget directly within your internal web application or React dashboard.
* **The User Query:** *"The customer lifetime value model seems degraded today. What's wrong with it?"*
* **The Behind-the-Scenes Action:** The UI routes this question to the MCP-backed agent, which inspects the active alerts and feature statistics.
* **The Copilot Reply:** A conversational, jargon-free summary is rendered directly in the sidebar: *"The CLV model is experiencing a high error rate (8.2%) because the inputs for `user_age` have drifted significantly from the baseline. Staging version `v1` remains unaffected."*

#### 🤖 Hands-Free Autopilot & Self-Healing
Enable autonomous remediation loops where issues are identified and mitigated before customers experience degradation.
* **How it works:** The agent runs as a cron or event-triggered worker. When the error rate crosses the threshold:
  1. It fetches metrics and confirms degradation.
  2. It identifies if a stable staging/fallback version exists.
  3. It calls `modify_routing_weight` to dynamically shift traffic to the healthy version.
  4. It sends an automated email or Slack ping:
     > 🚨 **Self-Healing Resolution: High Error Rate on CLV Regressor**
     > * "An error rate spike of 8.2% was detected on version `v2`. The agent checked for data drift, confirmed degradation, and automatically routed 100% of traffic to the stable `v1` version. Service has normalized."

---

## Installation & Setup

### Prerequisites
* Python `3.10` or higher
* [uv](https://github.com/astral-sh/uv) or `pip`

### 1. Clone & Setup Environment
```bash
git clone https://github.com/rizkashifs/mcp-server-mlops-inspector.git
cd mcp-server-mlops-inspector

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode
pip install -e .
```

### 2. Run the Server
The server starts up over standard input/output (stdio), which allows MCP clients to spawn and communicate with it:
```bash
mcp-server-mlops-inspector
```

---

## Integration with Claude Desktop

Add this configuration to your Claude Desktop configuration file (located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "mlops-inspector": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server_mlops_inspector.server"
      ],
      "env": {},
      "cwd": "C:/Users/admin/Documents/GitHub/repoCreatorCodex/mcp-server-mlops-inspector"
    }
  }
}
```
*(Remember to replace the `cwd` path with your exact local repository location, and make sure `python` is available in your shell environment path).*

---

## Verification & Testing

To run the local unit test suite to verify the mock metrics, PSI calculations, and tool functionality:
```bash
python -m unittest tests/test_server.py
```
