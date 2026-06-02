import unittest
import json
import os
import shutil
from mcp_server_mlops_inspector.server import (
    load_routing_config,
    list_deployed_models,
    get_realtime_metrics,
    fetch_drift_analysis,
    modify_routing_weight,
    get_active_models_resource,
    get_active_alerts_resource,
    ROUTING_CONFIG_PATH
)

class TestMLOpsInspector(unittest.TestCase):
    
    def setUp(self):
        # Ensure we start with clean routing config state
        if os.path.exists(ROUTING_CONFIG_PATH):
            os.remove(ROUTING_CONFIG_PATH)
            
    def tearDown(self):
        # Clean up config state
        if os.path.exists(ROUTING_CONFIG_PATH):
            os.remove(ROUTING_CONFIG_PATH)

    def test_list_deployed_models(self):
        result_str = list_deployed_models()
        result = json.loads(result_str)
        self.assertIn("churn-predictor-xgb", result)
        self.assertIn("customer-lifetime-value-regressor", result)
        self.assertEqual(
            result["churn-predictor-xgb"]["versions"]["v2"]["routing_weight"],
            0.90
        )

    def test_get_realtime_metrics(self):
        result_str = get_realtime_metrics("churn-predictor-xgb")
        result = json.loads(result_str)
        self.assertEqual(result["model_id"], "churn-predictor-xgb")
        self.assertIn("requests_per_second", result)
        self.assertIn("p95_latency_ms", result)

    def test_fetch_drift_analysis(self):
        result_str = fetch_drift_analysis("churn-predictor-xgb")
        result = json.loads(result_str)
        self.assertEqual(result["model_id"], "churn-predictor-xgb")
        self.assertTrue(result["drift_detected"])
        
        # Verify transaction_amount drift is flagged
        features = {f["feature_name"]: f for f in result["features"]}
        self.assertEqual(features["transaction_amount"]["status"], "CRITICAL_DRIFT")
        self.assertEqual(features["user_age"]["status"], "STABLE")

    def test_modify_routing_weight(self):
        # Set CLV model to v1=1.0 and v2=0.0 (rollback from degraded)
        result_str = modify_routing_weight(
            model_id="customer-lifetime-value-regressor",
            version="v1",
            weight=1.0
        )
        result = json.loads(result_str)
        self.assertTrue(result["success"])
        
        # Check config reflects the changes
        config = load_routing_config()
        clv_versions = config["customer-lifetime-value-regressor"]["versions"]
        self.assertEqual(clv_versions["v1"]["routing_weight"], 1.0)
        self.assertEqual(clv_versions["v2"]["routing_weight"], 0.0)
        self.assertEqual(clv_versions["v1"]["status"], "Healthy")
        self.assertEqual(clv_versions["v2"]["status"], "Inactive")

    def test_resources(self):
        models_res = json.loads(get_active_models_resource())
        self.assertEqual(len(models_res), 3)
        
        alerts_res = json.loads(get_active_alerts_resource())
        self.assertEqual(len(alerts_res), 2)
        self.assertEqual(alerts_res[0]["model_id"], "customer-lifetime-value-regressor")

if __name__ == "__main__":
    unittest.main()
