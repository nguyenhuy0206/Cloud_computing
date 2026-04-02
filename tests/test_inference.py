import unittest

from src.edge.inference import InferenceEngine


class TestInferenceEngine(unittest.TestCase):
    def test_predict_anomaly_when_value_high(self):
        engine = InferenceEngine()
        result = engine.predict(sensor_value=0.92)

        self.assertEqual(result["prediction"], "anomaly")
        self.assertGreaterEqual(result["confidence"], 0.8)
        self.assertIn("inference_ms", result)

    def test_predict_normal_when_value_low(self):
        engine = InferenceEngine()
        result = engine.predict(sensor_value=0.21)

        self.assertEqual(result["prediction"], "normal")
        self.assertGreaterEqual(result["confidence"], 0.5)


if __name__ == "__main__":
    unittest.main()
