"""Run: python -m streamlit run app.py"""
import csv
import io
import json
import os

import streamlit as st

from planner import CATALOG, INGREDIENTS, MODEL, ai_choices, candidates, sample_choices

st.set_page_config(page_title="SmartPlate AI", page_icon="🍲", layout="wide")
st.title("🍲 SmartPlate AI")
st.write("A Pakistani dinner that fits your pantry and tonight's budget.")
st.caption("One dinner • 1–12 servings • Estimated extra spending in Pakistani rupees")


def configured_key():
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            pass
    return key


with st.sidebar:
    st.header("How to use")
    st.write("1. Set your dinner budget.\n2. Enter what you have.\n3. Check prices and find meals.")
    mode = st.radio("Mode", ["Sample (no AI)", "Live AI"], key="mode")
    key = configured_key()
    if mode == "Live AI":
        if key:
            st.success("Server API key configured")
        else:
            key = st.text_input("Your Groq API key", type="password", key="api_key")
            st.caption("Used only for your request. Never included in downloaded files.")
        st.caption(f"Groq model: {MODEL}. Use a Free-plan account; usage limits apply.")
    st.divider()
    st.caption("Sample mode uses fixed recipes and no AI call. Live mode adds AI selection and explanations.")

left, right = st.columns(2)
people = left.number_input("People / servings", 1, 12, 4, key="people")
budget = right.number_input("Tonight's extra-spending limit (Rs.)", 0, 100000, 600, step=50, key="budget")
vegetarian = st.checkbox("Vegetarian (exclude chicken and eggs)", key="vegetarian")
avoid = st.multiselect("Ingredients to exclude", list(INGREDIENTS),
                      format_func=lambda k: INGREDIENTS[k]["name"], key="avoid")
st.caption("Exclusions filter listed ingredients only. Check actual products if managing allergies.")
preference = st.text_input("Preference (optional; used in Live AI mode)",
                           placeholder="For example: prefer lentils and use my spinach", max_chars=300, key="preference")
language = st.selectbox("AI explanation language", ["English", "Roman Urdu"], key="language")

st.subheader("What is already at home?")
st.caption("Enter usable raw/dry quantities. Chickpeas must be cooked and drained. Water is assumed available.")
stock_items = st.multiselect("Select ingredients you have", list(INGREDIENTS),
                             format_func=lambda k: INGREDIENTS[k]["name"], key="stock_items")
pantry = {}
columns = st.columns(3)
for i, ingredient in enumerate(stock_items):
    info = INGREDIENTS[ingredient]
    pantry[ingredient] = columns[i % 3].number_input(
        f"{info['name']} ({info['unit']})", 0, 100000, 0,
        step=1 if info["unit"] == "piece" else 10, key=f"stock_{ingredient}")

with st.expander("Edit ingredient prices — sample values, not live market prices"):
    st.caption(CATALOG["price_note"])
    prices = {}
    columns = st.columns(3)
    for i, (ingredient, info) in enumerate(INGREDIENTS.items()):
        prices[ingredient] = columns[i % 3].number_input(
            f"{info['name']}: Rs. per {info['price_unit']}",
            min_value=0.01, max_value=100000.0, value=float(info["price"]), step=1.0,
            key=f"price_{ingredient}")

st.info("Cost estimates use the prices above and assume you can buy the exact missing quantities. "
        "Whole packets may cost more. Fuel and delivery are excluded.")

# Invalidate results when inputs change, so old costs never appear as current.
signature = json.dumps([people, budget, vegetarian, avoid, pantry, prices, preference, language, mode], sort_keys=True)
if st.session_state.get("signature") != signature:
    st.session_state.pop("results", None)
    st.session_state["signature"] = signature

if st.button("Find dinner options", type="primary", key="generate"):
    st.session_state.pop("results", None)
    try:
        options, allowed = candidates(people, budget, pantry, prices, avoid, vegetarian)
        if not allowed:
            st.warning("No catalogue recipes match these exclusions. Adjust your filters.")
        elif not options:
            st.warning(f"No matching meal fits this budget. The cheapest matching option needs "
                       f"Rs. {allowed[0]['extra']:.2f} extra at your entered prices. "
                       "Check your pantry quantities or increase the limit.")
        else:
            with st.spinner("Checking dinner options…"):
                choices = (ai_choices(options, key, preference, language)
                           if mode == "Live AI" else sample_choices(options))
            lookup = {r["id"]: r for r in options}
            st.session_state["results"] = [{**lookup[c["id"]], "reason": c["reason"]} for c in choices]
    except ValueError as error:
        st.error(str(error))

results = st.session_state.get("results", [])
if results:
    st.subheader(f"{len(results)} dinner option{'s' if len(results) != 1 else ''}")
    st.caption("Each is a separate alternative for the whole family. Choose one; do not add their shopping lists together.")
    for recipe in results:
        with st.container(border=True):
            st.subheader(recipe["name"])
            st.caption(f"{people} approximate servings • About {recipe['minutes']} minutes")
            st.text(recipe["reason"])
            a, b, c = st.columns(3)
            a.metric("Estimated extra spending", f"Rs. {recipe['extra']:.2f}")
            b.metric("Left from tonight's limit", f"Rs. {budget - recipe['extra']:.2f}")
            c.metric("All ingredients' estimated value", f"Rs. {recipe['value']:.2f}")
            with st.expander("Ingredients, cooking steps and shopping list"):
                st.dataframe(recipe["rows"], hide_index=True, width="stretch")
                st.write("**Cooking steps**")
                for i, step in enumerate(recipe["steps"], 1):
                    st.write(f"{i}. {step}")
                shopping = [{"Ingredient": r["Ingredient"], "Quantity": r["Buy"],
                             "Unit": r["Unit"], "Estimated cost (Rs.)": r["Extra cost (Rs.)"]}
                            for r in recipe["rows"] if r["Buy"] > 0]
                if shopping:
                    st.write("**Buy for this dinner**")
                    st.dataframe(shopping, hide_index=True, width="stretch")
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=list(shopping[0]))
                    writer.writeheader()
                    writer.writerows(shopping)
                    st.download_button("Download shopping list", output.getvalue(),
                                       f"{recipe['id']}_shopping.csv", "text/csv", key=f"download_{recipe['id']}")
                else:
                    st.success("You have all listed ingredients for this option.")
    st.caption("Six starter recipes with approximate portions. Review AI explanations; they can make mistakes. "
               "This version does not calculate nutrition or track actual purchases. Refreshing may reset session inputs.")
