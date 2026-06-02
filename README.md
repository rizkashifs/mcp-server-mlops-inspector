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

By acting as the interactive agentic layer over your MLOps telemetry, this server supports both technical engineering tasks and non-technical business workflows.

### 1. For Technical Teams (SRE, MLOps, & Data Scientists)
* **On-Call Copilot & Troubleshooting:** When system alerts fire, the agent automatically retrieves performance metrics, checks distribution drift, isolates the failing component, and recommends routing overrides.
* **Conversational Registry Queries:** Instantly inspect model versions, routing metrics, and costs via natural language (e.g., *"Which models in Staging have been inactive for 48 hours?"*).
* **Automated Shadow Testing:** The agent can be instructed to dynamically adjust routing weights to direct test traffic to staging versions, monitor error rates in real-time, and auto-rollback if anomalies occur.

### 2. For Non-Technical Users (Product Managers & Operations)
* **Slack / MS Teams ChatOps Integration:** Business stakeholders can ask standard chat channels simple questions (e.g., *"Is the churn predictor running fine?"*) and receive natural language status summaries with one-click **[Approve Rollback]** action buttons.
* **Embedded Dashboard Sidebars:** Power custom "AI Support" chat sidebars inside your internal MLOps web dashboard UI, allowing users to ask questions directly next to the charts.
* **Hands-free Autopilot Resolutions:** The server powers background automation that detects errors, performs the diagnostic checks, updates routing weights to a healthy version, and pings the team with a simple summary: *"CLV model v2 degraded. Automatically routed traffic to v1 baseline."*

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
