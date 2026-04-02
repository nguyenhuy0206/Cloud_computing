import unittest

from src.pipeline import run_pipeline
from src.shared.config import AppConfig


class TestPipeline(unittest.TestCase):
    def test_pipeline_runs_and_sends_expected_count_in_mock_mode(self):
        config = AppConfig(
            cloud_mode="mock",
            telemetry_interval_sec=0.0,
            iterations=3,
            device_id="edge-demo-01",
            iot_hub_device_connection_string="",
        )

        sent_messages = run_pipeline(config)

        self.assertEqual(len(sent_messages), 3)
        payload = sent_messages[0]
        self.assertIn("timestamp", payload)
        self.assertIn("prediction", payload)
        self.assertIn("device_id", payload)


if __name__ == "__main__":
    unittest.main()
