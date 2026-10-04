import copy
import json
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

import requests

from planner import INGREDIENTS, RECIPES, ai_choices, candidates, cost_recipe, sample_choices


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.prices = {k: v["price"] for k, v in INGREDIENTS.items()}

    def test_hand_calculated_dal_total(self):
        # 90 rice + 100 lentils + 22.50 onion + 32 tomato + 18 oil
        # + .32 salt + 8 cumin + 2.40 turmeric = 273.22
        result = cost_recipe(RECIPES[0], 4, {}, self.prices)
        self.assertEqual(result["extra"], 273.22)
        self.assertEqual(result["value"], 273.22)

    def test_partial_pantry(self):
        result = cost_recipe(RECIPES[0], 4, {"rice": 100, "lentils": 999}, self.prices)
        self.assertEqual(result["extra"], 143.22)
        self.assertEqual(result["rows"][0]["Buy"], 200)
        self.assertEqual(result["value"], 273.22)

    def test_full_pantry_zero_budget(self):
        stock = {k: 100000 for k in INGREDIENTS}
        options, _ = candidates(4, 0, stock, self.prices, [], False)
        self.assertEqual(len(options), 6)
        self.assertTrue(all(r["extra"] == 0 for r in options))

    def test_exact_budget_boundary(self):
        for budget, should_include in [(273.22, True), (273.21, False)]:
            options, _ = candidates(4, budget, {}, self.prices, [], False)
            self.assertEqual("dal_rice" in [r["id"] for r in options], should_include)

    def test_scaled_eggs_round_up(self):
        result = cost_recipe(RECIPES[3], 1, {}, self.prices)
        egg = next(r for r in result["rows"] if r["Ingredient"] == "Egg")
        self.assertEqual(egg["Needed"], 2)

    def test_larger_family_costs_more(self):
        small = cost_recipe(RECIPES[0], 4, {}, self.prices)
        big = cost_recipe(RECIPES[0], 8, {}, self.prices)
        self.assertEqual(big["extra"], 2 * small["extra"])

    def test_invalid_inputs(self):
        for value in [-1, float("nan"), float("inf"), "not a number"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidates(4, value, {}, self.prices, [], False)
        for value in [0, -1, None, float("nan")]:
            prices = {**self.prices, "rice": value}
            with self.subTest(price=value), self.assertRaises(ValueError):
                candidates(4, 600, {}, prices, [], False)
        for pantry in [{"rice": -1}, {"egg": 1.5}, {"rice": float("inf")}]:
            with self.subTest(pantry=pantry), self.assertRaises(ValueError):
                candidates(4, 600, pantry, self.prices, [], False)
        for people in [0, 13, 1.5, True]:
            with self.subTest(people=people), self.assertRaises(ValueError):
                candidates(people, 600, {}, self.prices, [], False)

    def test_exclusions_and_vegetarian(self):
        options, _ = candidates(4, 10000, {}, self.prices, ["lentils"], True)
        self.assertEqual([r["id"] for r in options], ["chana_rice"])
        options, allowed = candidates(4, 10000, {}, self.prices, ["rice"], False)
        self.assertEqual((options, allowed), ([], []))

    def test_insufficient_budget(self):
        options, allowed = candidates(4, 1, {}, self.prices, [], False)
        self.assertEqual(options, [])
        self.assertEqual(len(allowed), 6)

    def test_price_edit_changes_result(self):
        before = cost_recipe(RECIPES[0], 4, {}, self.prices)
        after = cost_recipe(RECIPES[0], 4, {}, {**self.prices, "rice": 600})
        self.assertEqual(after["extra"] - before["extra"], 90)

    def test_catalog_and_rounding_invariants(self):
        self.assertEqual(len({r["id"] for r in RECIPES}), len(RECIPES))
        for recipe in RECIPES:
            self.assertTrue(set(recipe["ingredients"]).issubset(INGREDIENTS))
            self.assertTrue(all(q > 0 for q in recipe["ingredients"].values()))
            self.assertTrue(recipe["steps"])
            for people in range(1, 13):
                result = cost_recipe(recipe, people, {"rice": 111}, self.prices)
                self.assertEqual(Decimal(str(result["extra"])),
                                 sum(Decimal(str(row["Extra cost (Rs.)"])) for row in result["rows"]))
                self.assertTrue(all(row["Buy"] >= 0 for row in result["rows"]))


class ApiTests(unittest.TestCase):
    def setUp(self):
        prices = {k: v["price"] for k, v in INGREDIENTS.items()}
        self.options, _ = candidates(4, 600, {}, prices, [], False)
        self.good = {"choices": [{"id": r["id"], "reason": "Uses rice from the catalogue."}
                                 for r in self.options[:3]]}

    def response(self, data=None, status=200, finish="stop"):
        return Mock(status_code=status, json=lambda: {"choices": [{
            "finish_reason": finish, "message": {"content": json.dumps(data or self.good)}}]})

    @patch("planner.requests.post")
    def test_valid_ai_and_request_contract(self, post):
        post.return_value = self.response()
        result = ai_choices(self.options, "fake-test-key", "Prefer rice", "English")
        self.assertEqual(len(result), 3)
        kwargs = post.call_args.kwargs
        self.assertTrue(kwargs["json"]["response_format"]["json_schema"]["strict"])
        self.assertEqual(kwargs["json"]["model"], "openai/gpt-oss-20b")
        self.assertEqual(kwargs["timeout"], (10, 45))
        self.assertNotIn("fake-test-key", json.dumps(kwargs["json"]))
        post.assert_called_once()

    @patch("planner.requests.post")
    def test_unknown_duplicate_empty_and_wrong_type(self, post):
        for change in ["unknown", "duplicate", "empty", "wrong_type", "wrong_count"]:
            data = copy.deepcopy(self.good)
            if change == "unknown": data["choices"][0]["id"] = "invented_recipe"
            if change == "duplicate": data["choices"][1]["id"] = data["choices"][0]["id"]
            if change == "empty": data["choices"][0]["reason"] = ""
            if change == "wrong_type": data["choices"][0]["reason"] = 15
            if change == "wrong_count": data["choices"] = data["choices"][:1]
            post.return_value = self.response(data)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "validation"):
                ai_choices(self.options, "fake", "", "English")

    @patch("planner.requests.post")
    def test_http_errors_do_not_expose_key_or_body(self, post):
        for status in [400, 401, 403, 404, 429, 500, 503]:
            post.return_value = self.response(status=status)
            with self.subTest(status=status), self.assertRaises(ValueError) as error:
                ai_choices(self.options, "private-key", "", "English")
            self.assertNotIn("private-key", str(error.exception))

    @patch("planner.requests.post")
    def test_network_failure(self, post):
        for exception in [requests.Timeout(), requests.ConnectionError()]:
            post.side_effect = exception
            with self.assertRaisesRegex(ValueError, "Cannot reach"):
                ai_choices(self.options, "fake", "", "English")

    @patch("planner.requests.post")
    def test_truncated_and_malformed_response(self, post):
        post.return_value = self.response(finish="length")
        with self.assertRaisesRegex(ValueError, "validation"):
            ai_choices(self.options, "fake", "", "English")
        post.return_value = Mock(status_code=200, json=lambda: {"choices": []})
        with self.assertRaisesRegex(ValueError, "validation"):
            ai_choices(self.options, "fake", "", "English")
        post.return_value = Mock(status_code=200)
        post.return_value.json.side_effect = ValueError("not json")
        with self.assertRaisesRegex(ValueError, "validation"):
            ai_choices(self.options, "fake", "", "English")

    @patch("planner.requests.post")
    def test_missing_key_and_sample_mode_never_call_api(self, post):
        with self.assertRaisesRegex(ValueError, "key"):
            ai_choices(self.options, "", "", "English")
        self.assertEqual(len(sample_choices(self.options)), 3)
        post.assert_not_called()

    @patch("planner.requests.post")
    def test_only_one_available_option(self, post):
        post.return_value = self.response({"choices": self.good["choices"][:1]})
        self.assertEqual(len(ai_choices(self.options[:1], "fake", "", "Roman Urdu")), 1)


if __name__ == "__main__":
    unittest.main()
