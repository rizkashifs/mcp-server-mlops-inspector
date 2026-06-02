import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List

# Stable seed for reproducible mock calculations
np.random.seed(42)

def calculate_psi(reference: np.ndarray, production: np.ndarray, num_buckets: int = 10) -> float:
    """
    Computes the Population Stability Index (PSI) between reference and production distributions.
    """
    # Remove NaNs
    ref = reference[~np.isnan(reference)]
    prod = production[~np.isnan(production)]
    
    if len(ref) == 0 or len(prod) == 0:
        return 0.0

    # Determine bin edges based on reference distribution percentiles
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(ref, percentiles)
    # Ensure unique bins
    bins = np.unique(bins)
    if len(bins) < 2:
        return 0.0
        
    # Adjust outer bounds to capture all values
    bins[0] = -np.inf
    bins[-1] = np.inf

    # Calculate bucket counts
    ref_counts, _ = np.histogram(ref, bins=bins)
    prod_counts, _ = np.histogram(prod, bins=bins)

    # Convert to proportions with laplace smoothing to avoid division by zero
    ref_props = (ref_counts + 1e-4) / (len(ref) + 1e-4 * len(ref_counts))
    prod_props = (prod_counts + 1e-4) / (len(prod) + 1e-4 * len(prod_counts))

    # Calculate PSI
    psi_value = np.sum((prod_props - ref_props) * np.log(prod_props / ref_props))
    return float(psi_value)

def generate_drift_data(feature_name: str, has_drift: bool = False) -> Dict[str, Any]:
    """
    Generates reference and production data, calculates PSI and KS-test,
    and returns a structured drift assessment.
    """
    size = 1000
    
    if feature_name == "transaction_amount":
        ref = np.random.normal(loc=150.0, scale=50.0, size=size)
        if has_drift:
            # Drifted distribution: higher mean, larger variance (users spending more/anomalously)
            prod = np.random.normal(loc=230.0, scale=90.0, size=size)
        else:
            prod = np.random.normal(loc=152.0, scale=49.0, size=size)
            
    elif feature_name == "user_age":
        ref = np.random.triangular(left=18, mode=28, right=75, size=size)
        if has_drift:
            # Drifted distribution: sudden influx of younger users
            prod = np.random.exponential(scale=10.0, size=size) + 18
        else:
            prod = np.random.triangular(left=18, mode=29, right=74, size=size)
            
    else: # general continuous feature
        ref = np.random.beta(a=2, b=5, size=size) * 100
        if has_drift:
            prod = np.random.beta(a=5, b=2, size=size) * 100
        else:
            prod = np.random.beta(a=2.1, b=4.9, size=size) * 100

    # Calculate PSI
    psi = calculate_psi(ref, prod)
    
    # Calculate KS-Test
    ks_stat, p_val = stats.ks_2samp(ref, prod)
    
    # Determine status
    if psi >= 0.25:
        status = "CRITICAL_DRIFT"
    elif psi >= 0.10:
        status = "MODERATE_DRIFT"
    else:
        status = "STABLE"
        
    return {
        "feature_name": feature_name,
        "psi_statistic": round(psi, 4),
        "ks_statistic": round(float(ks_stat), 4),
        "ks_p_value": float(p_val),
        "status": status,
        "reference_mean": round(float(np.mean(ref)), 2),
        "production_mean": round(float(np.mean(prod)), 2),
    }

def get_simulated_metrics(model_id: str) -> Dict[str, Any]:
    """
    Returns simulated real-time metrics for a given model.
    """
    if model_id == "churn-predictor-xgb":
        return {
            "model_id": model_id,
            "requests_per_second": round(np.random.normal(120.0, 10.0), 2),
            "p50_latency_ms": round(np.random.normal(12.0, 1.0), 2),
            "p95_latency_ms": round(np.random.normal(25.0, 3.0), 2),
            "p99_latency_ms": round(np.random.normal(45.0, 5.0), 2),
            "error_rate": round(max(0.0, np.random.normal(0.002, 0.0005)), 4),
            "average_cost_per_query_usd": 0.0001,
        }
    elif model_id == "customer-lifetime-value-regressor":
        # Simulate a degradation event (high error rate/latency spikes)
        return {
            "model_id": model_id,
            "requests_per_second": round(np.random.normal(45.0, 5.0), 2),
            "p50_latency_ms": round(np.random.normal(110.0, 15.0), 2),
            "p95_latency_ms": round(np.random.normal(350.0, 50.0), 2),
            "p99_latency_ms": round(np.random.normal(780.0, 90.0), 2),
            "error_rate": round(max(0.0, np.random.normal(0.082, 0.015)), 4), # ~8% error rate
            "average_cost_per_query_usd": 0.0005,
        }
    elif model_id == "sentiment-analyzer-bert":
        return {
            "model_id": model_id,
            "requests_per_second": round(np.random.normal(85.0, 8.0), 2),
            "p50_latency_ms": round(np.random.normal(40.0, 2.0), 2),
            "p95_latency_ms": round(np.random.normal(85.0, 8.0), 2),
            "p99_latency_ms": round(np.random.normal(120.0, 15.0), 2),
            "error_rate": round(max(0.0, np.random.normal(0.001, 0.0002)), 4),
            "average_cost_per_query_usd": 0.0008,
        }
    else:
        return {
            "model_id": model_id,
            "requests_per_second": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "error_rate": 0.0,
            "average_cost_per_query_usd": 0.0,
        }
