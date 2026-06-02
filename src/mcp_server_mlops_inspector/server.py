import os
import json
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from mcp_server_mlops_inspector.metrics_generator import get_simulated_metrics, generate_drift_data

# Initialize FastMCP Server
mcp = FastMCP("MLOps Inspector")

# Path to persist the routing configuration state
ROUTING_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routing_config.json")

DEFAULT_ROUTING_CONFIG = {
    "churn-predictor-xgb": {
        "description": "XGBoost classifier predicting customer churn risk.",
        "versions": {
            "v1": {"stage": "Staging", "routing_weight": 0.10, "status": "Healthy"},
            "v2": {"stage": "Production", "routing_weight": 0.90, "status": "Healthy"}
        }
    },
    "customer-lifetime-value-regressor": {
        "description": "Gradient boosted regressor forecasting user CLV.",
        "versions": {
            "v1": {"stage": "Staging", "routing_weight": 0.00, "status": "Healthy"},
            "v2": {"stage": "Production", "routing_weight": 1.00, "status": "Degraded"}
        }
    },
    "sentiment-analyzer-bert": {
        "description": "Transformer model scoring sentiment score on feedback reviews.",
        "versions": {
            "v1": {"stage": "Production", "routing_weight": 1.00, "status": "Healthy"}
        }
    }
}

def load_routing_config() -> Dict[str, Any]:
    """Loads the active model registry routing state."""
    if not os.path.exists(ROUTING_CONFIG_PATH):
        with open(ROUTING_CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_ROUTING_CONFIG, f, indent=4)
        return DEFAULT_ROUTING_CONFIG
    try:
        with open(ROUTING_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_ROUTING_CONFIG

def save_routing_config(config: Dict[str, Any]) -> None:
    """Saves the active model registry routing state."""
    with open(ROUTING_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

# --- TOOLS ---

@mcp.tool()
def list_deployed_models() -> str:
    """
    Retrieves a list of all models registered in the system, including metadata, deployment environment, and routing weights.
    """
    config = load_routing_config()
    return json.dumps(config, indent=2)

@mcp.tool()
def get_realtime_metrics(model_id: str) -> str:
    """
    Fetches the real-time operational performance metrics (latency, RPS, error rate, cost) for a given model.
    """
    config = load_routing_config()
    if model_id not in config:
        return json.dumps({"error": f"Model '{model_id}' not found in registry."}, indent=2)
        
    metrics = get_simulated_metrics(model_id)
    return json.dumps(metrics, indent=2)

@mcp.tool()
def fetch_drift_analysis(model_id: str) -> str:
    """
    Performs data distribution drift analysis (PSI, KS-test) for a model's input features against baseline data.
    """
    config = load_routing_config()
    if model_id not in config:
        return json.dumps({"error": f"Model '{model_id}' not found in registry."}, indent=2)

    # Let's mock feature drift depending on the model
    features_report = []
    if model_id == "churn-predictor-xgb":
        # Simulate drift in transaction_amount
        features_report.append(generate_drift_data("transaction_amount", has_drift=True))
        features_report.append(generate_drift_data("user_age", has_drift=False))
        features_report.append(generate_drift_data("days_since_active", has_drift=False))
    elif model_id == "customer-lifetime-value-regressor":
        # Customer lifetime value features
        features_report.append(generate_drift_data("monthly_spend", has_drift=False))
        features_report.append(generate_drift_data("user_age", has_drift=True))  # age drifted
    else:
        # stable model
        features_report.append(generate_drift_data("text_length", has_drift=False))
        features_report.append(generate_drift_data("vocabulary_density", has_drift=False))

    summary = {
        "model_id": model_id,
        "drift_detected": any(f["status"] in ["CRITICAL_DRIFT", "MODERATE_DRIFT"] for f in features_report),
        "features": features_report
    }
    return json.dumps(summary, indent=2)

@mcp.tool()
def modify_routing_weight(model_id: str, version: str, weight: float) -> str:
    """
    Updates the routing weight configuration for a specific version of a model.
    Weights must be between 0.0 and 1.0.
    """
    if not (0.0 <= weight <= 1.0):
        return json.dumps({"error": "Routing weight must be between 0.0 and 1.0 inclusive."}, indent=2)

    config = load_routing_config()
    if model_id not in config:
        return json.dumps({"error": f"Model '{model_id}' not found in registry."}, indent=2)

    versions = config[model_id]["versions"]
    if version not in versions:
        return json.dumps({"error": f"Version '{version}' not found for model '{model_id}'."}, indent=2)

    # Update routing weight for targeted version
    versions[version]["routing_weight"] = weight
    
    # Auto-adjust other version weights so they sum to 1.0 if there are multiple versions
    other_versions = [v for v in versions if v != version]
    if other_versions:
        # Distribute remaining weight evenly or set to zero if weight is 1.0
        remaining = max(0.0, 1.0 - weight)
        share = remaining / len(other_versions)
        for ov in other_versions:
            versions[ov]["routing_weight"] = round(share, 2)
            
    # Update health statuses based on new weight distribution
    for v_name, v_info in versions.items():
        if v_info["routing_weight"] < 0.05:
            if v_info["status"] == "Degraded":
                v_info["status"] = "Inactive"
        else:
            if v_info["status"] == "Inactive":
                v_info["status"] = "Healthy"

    save_routing_config(config)
    return json.dumps({
        "success": True,
        "message": f"Successfully updated routing weight of {model_id}:{version} to {weight}.",
        "updated_configuration": config[model_id]
    }, indent=2)


# --- RESOURCES ---

@mcp.resource("model-registry://active-models")
def get_active_models_resource() -> str:
    """
    Exposes a static registry configuration file of all active models and health status.
    """
    config = load_routing_config()
    summary = []
    for model_id, details in config.items():
        summary.append({
            "model_id": model_id,
            "description": details["description"],
            "versions": list(details["versions"].keys()),
            "status": "Degraded" if any(v["status"] == "Degraded" for v in details["versions"].values()) else "Healthy"
        })
    return json.dumps(summary, indent=2)

@mcp.resource("observability://alerts/active")
def get_active_alerts_resource() -> str:
    """
    Lists active system-level MLOps alerts and performance anomalies.
    """
    alerts = [
        {
            "alert_id": "ALERT_0921",
            "model_id": "customer-lifetime-value-regressor",
            "severity": "CRITICAL",
            "metric": "error_rate",
            "message": "Model error rate spiked to 8.2% (Threshold: 1.0%). P95 latency exceeded 350ms.",
            "timestamp": "2026-06-02T13:10:00Z"
        },
        {
            "alert_id": "ALERT_0922",
            "model_id": "churn-predictor-xgb",
            "severity": "WARNING",
            "metric": "data_drift",
            "message": "Significant feature drift detected on 'transaction_amount'. PSI value is 0.32 (Threshold: 0.25).",
            "timestamp": "2026-06-02T13:15:00Z"
        }
    ]
    return json.dumps(alerts, indent=2)


# --- PROMPTS ---

@mcp.prompt()
def diagnose_model_health() -> str:
    """
    An on-call MLOps workflow to check active alerts, fetch model metrics,
    diagnose issues, and suggest corrective routing adjustments.
    """
    return (
        "You are an on-call MLOps Platform reliability agent.\n\n"
        "Please follow these operational diagnostic steps:\n"
        "1. Retrieve the list of active alerts by reading the resource `observability://alerts/active`.\n"
        "2. For each model flag with an alert or warning, fetch its real-time metrics using the `get_realtime_metrics` tool.\n"
        "3. Investigate potential data input problems by executing `fetch_drift_analysis` for that model.\n"
        "4. Summarize your diagnostic findings. If appropriate, recommend or perform weight modifications via the `modify_routing_weight` tool to mitigate user impact (e.g., rolling back to a stable version)."
    )

def main():
    mcp.run()

if __name__ == "__main__":
    main()
