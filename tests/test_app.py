import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"GROQ_API_KEY": ""})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = AppTest.from_file(APP, default_timeout=15).run()

    def test_start_and_sample_results(self):
        self.assertFalse(self.app.exception)
        self.app.button(key="generate").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.session_state["results"]), 3)
        self.assertEqual(len(self.app.metric), 9)

    def test_changed_budget_clears_old_results(self):
        self.app.button(key="generate").click().run()
        self.app.number_input(key="budget").set_value(0).run()
        self.assertEqual(len(self.app.metric), 0)
        self.app.button(key="generate").click().run()
        self.assertTrue(self.app.warning)
        self.assertFalse(self.app.exception)

    def test_filter_no_recipes(self):
        self.app.multiselect(key="avoid").set_value(["rice"]).run()
        self.app.button(key="generate").click().run()
        self.assertIn("No catalogue recipes", self.app.warning[0].value)

    def test_pantry_and_price_edit(self):
        self.app.multiselect(key="stock_items").set_value(["rice", "lentils"]).run()
        self.app.number_input(key="stock_rice").set_value(300).run()
        self.app.number_input(key="stock_lentils").set_value(250).run()
        self.app.button(key="generate").click().run()
        self.assertFalse(self.app.exception)
        dal = next(r for r in self.app.session_state["results"] if r["id"] == "dal_rice")
        self.assertEqual(dal["extra"], 83.22)
        self.app.number_input(key="price_onion").set_value(300.0).run()
        self.assertEqual(len(self.app.metric), 0)

    def test_live_without_key(self):
        self.app.radio(key="mode").set_value("Live AI").run()
        self.app.button(key="generate").click().run()
        self.assertTrue(self.app.error)
        self.assertIn("API key", self.app.error[0].value)
        self.assertFalse(self.app.exception)

    @patch("planner.requests.post")
    def test_live_success_with_mocked_http(self, post):
        data = {"choices": [{"id": key, "reason": "Test explanation."}
                             for key in ["dal_rice", "khichdi", "palak_dal"]]}
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{
            "finish_reason": "stop", "message": {"content": json.dumps(data)}}]})
        self.app.radio(key="mode").set_value("Live AI").run()
        self.app.text_input(key="api_key").set_value("fake-test-key").run()
        self.app.button(key="generate").click().run()
        self.assertFalse(self.app.exception)
        self.assertFalse(self.app.error)
        self.assertEqual(len(self.app.session_state["results"]), 3)
        self.assertEqual(post.call_count, 1)
        self.app.selectbox(key="language").set_value("Roman Urdu").run()
        self.assertEqual(len(self.app.metric), 0)

    @patch("planner.requests.post")
    def test_live_quota_error_has_no_fake_success(self, post):
        post.return_value = Mock(status_code=429)
        self.app.radio(key="mode").set_value("Live AI").run()
        self.app.text_input(key="api_key").set_value("fake-test-key").run()
        self.app.button(key="generate").click().run()
        self.assertIn("quota", self.app.error[0].value)
        self.assertEqual(len(self.app.metric), 0)


if __name__ == "__main__":
    unittest.main()
