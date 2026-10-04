# SmartPlate AI — Budget Dinner Planner

A small Streamlit app for choosing one Pakistani-style dinner using pantry quantities and a rupee budget. Python checks ingredient exclusions and costs; Groq's hosted `openai/gpt-oss-20b` selects up to three eligible options and generates brief personalised explanations.

**Start here:** run Sample mode first, then test Live AI with your own free-plan Groq key.

## What is included

- Six starter recipes with ingredients, quantities for four, and simple cooking instructions.
- Scaling for 1–12 approximate servings; eggs round up to whole pieces.
- Editable sample prices and pantry quantities.
- Vegetarian and ingredient-exclusion filters.
- Up to three dinner alternatives within tonight's extra-spending limit.
- English or Roman Urdu AI explanations.
- Cooking instructions, ingredient breakdown, and a CSV shopping list per dinner.
- Clear errors for missing keys, exhausted quota, bad responses and connection problems.
- Automated tests of calculations, API handling and Streamlit interactions.

This is a small catalogue-based planner. It does not invent unlimited recipes. Ingredients, portions, cooking methods and costs come from the catalogue and Python, while the LLM generates the selection and explanations. Explanations can still be mistaken; review them. No model can be promised to never hallucinate.

## Free resources and model choice

Use **Groq Free plan + Streamlit Community Cloud + a GitHub repository**. Local Sample mode needs no account or API key.

The model is `openai/gpt-oss-20b`, served by **Groq**, not the OpenAI API. You need a **Groq key**. You do not need a ChatGPT subscription, OpenAI key, GPU, local model download, database, or paid hosting.

Groq's current free-limit table includes this model, and its structured-output documentation lists support for strict JSON schemas. One Generate click makes at most one AI request. The app does not retry automatically or switch providers. Your account's actual free limits may differ or change. Keep your account on the Free plan. This code cannot determine your billing plan; a key from a paid account can incur charges under that account's terms.

Streamlit Community Cloud documents free app hosting. GitHub is the source-code submission link; Community Cloud supplies the working application link. Do not select a paid upgrade for this project. The current Hugging Face documentation places plan restrictions on creating Docker Spaces, so it is not the default deployment route here.

## 1. Run locally

Extract `SmartPlate_AI.zip`. Open a terminal inside the extracted `SmartPlate_AI` folder — the folder containing `app.py` and `requirements.txt`.

Recommended Python version: **3.12** (the version used for tests). The two direct Python dependencies are pinned in `requirements.txt`; pip installs their supporting dependencies automatically.

### macOS / Linux

Check your Python first:

```bash
python3 --version
```

If it is Python 3.12, run these commands one at a time:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If Python 3.12 is installed as `python3.12`, use `python3.12 -m venv .venv` for the first command. If you use uv, an alternative is `uv venv --python 3.12` followed by `source .venv/bin/activate`, `uv pip install -r requirements.txt`, and `uv run streamlit run app.py`.

### Windows PowerShell

With Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

This uses the environment's Python directly, so it does not need a PowerShell activation-policy change.

Open **http://localhost:8501**. Stop the app with **Ctrl+C** in the terminal. To start again, return to this folder and run the same Streamlit command; do not recreate the environment each time.

## 2. Test without a key

Keep the sidebar in **Sample (no AI)** mode. Use 4 people, a Rs. 600 budget and an empty pantry. Click **Find dinner options**. With the supplied prices, the three cheapest results should be:

| Meal | Extra spending |
|---|---:|
| Vegetable masoor khichdi | Rs. 265.72 |
| Masoor dal with rice | Rs. 273.22 |
| Palak dal with rice | Rs. 318.22 |

These are calculated from the sample table, not actual shop quotations. The word "sample" remains visible; this mode is not a live GenAI demonstration.

Next, select Rice and Masoor lentils in the pantry, enter **300 g rice** and **250 g lentils**, and click again. Masoor dal with rice should require **Rs. 83.22** extra. Change the budget to Rs. 0 with an empty pantry: the app should report that nothing fits.

## 3. Add the free AI key

1. Open https://console.groq.com/ and sign in or create an account.
2. Confirm that your organisation uses the **Free plan**. Do not upgrade or add paid billing for this prototype.
3. Open **API Keys** at https://console.groq.com/keys and create a key.
4. In SmartPlate's sidebar choose **Live AI** and paste your key into the password field for this session.
5. Enter a preference such as `Prefer lentils and use my spinach`, then click **Find dinner options**.

For a persistent local configuration, create `.streamlit/secrets.toml` using `secrets.example.toml` as the template:

```toml
GROQ_API_KEY = "your-real-groq-key"
```

Restart Streamlit after creating/changing the secrets file. You can alternatively set the `GROQ_API_KEY` environment variable. The app checks the environment first, then Streamlit secrets, then offers the session input if neither is set. Never publish the real key or real secrets file. The included `.gitignore` excludes both the virtual environment and local secrets.

Live mode sends eligible meal names, ingredient names, computed extra costs and your preference to Groq. It does not send names or contact information. Avoid adding personal information in the preference field. An entered key is used for the API request; the application does not save it to a file or include it in CSV downloads.

**A valid AI run is still required on your account.** The package's tests simulate API responses; they do not prove your key, quota, model permissions, network or generated text quality.

## 4. Deploy free with GitHub + Streamlit Community Cloud

1. Create a GitHub repository named `smartplate-ai`. Public is simplest for hackathon review.
2. Upload the extracted project files to the **repository root**. The root must contain `app.py`, `planner.py`, `catalog.json`, and `requirements.txt` directly. Include `README.md` and `tests/` for reviewers. Include `.streamlit/config.toml` if desired for the green theme.
3. Do not upload `.venv/`, `.env`, `__pycache__/` or your real `.streamlit/secrets.toml`. Uploading files through GitHub's browser UI does not apply `.gitignore` automatically; select the source files carefully.
4. Open https://share.streamlit.io/ and connect your GitHub account.
5. Choose **Create app** and select the repository and branch. Set the main file path to **app.py**.
6. In advanced settings, select **Python 3.12**. Add the following in the **Secrets** field:

```toml
GROQ_API_KEY = "your-real-groq-key"
```

7. Deploy and wait for dependency installation. Test the generated app URL first in Sample mode, then in Live AI mode.
8. Submit your actual GitHub repository URL for **Code Deployment Link**, and the actual generated `streamlit.app` URL for **Application working Link**. No deployment URLs have been created for you in this package.

If the project is inside a repository subfolder, specify the correct path, such as `SmartPlate_AI/app.py`, instead. The price catalogue is loaded relative to `planner.py`, so it is independent of the terminal's current directory.

The hosted app starts in Sample mode deliberately. Switch to Live AI for your GenAI demonstration. A configured server key is shared by visitors to the app, so their requests consume that account's quota. Free services can have rate limits, downtime or sleeping apps.

## How costs work

All starter quantities are for four servings. They scale by `people / 4` and round up to whole grams, millilitres or eggs. Appetite differs; these are recipe serving estimates, not personalised nutrition targets.

For each ingredient:

```text
From home = min(needed quantity, available quantity)
Buy quantity = max(0, needed quantity - available quantity)
Extra cost = buy quantity × entered unit price ÷ unit divisor
```

Divisor is 1000 for prices per kilogram/litre and 1 for eggs per piece. Line costs round to two decimal places; the displayed total is the sum of those displayed line costs. Budget comparisons use this total. Zero budget is valid if all ingredients are already available.

Example: Rice costs Rs. 300/kg in the sample table. A recipe needs 300 g, and you have 100 g. You need 200 g more, costing `200 × 300 / 1000 = Rs. 60` under the loose-quantity assumption.

The app distinguishes **extra spending** from the **estimated value of all recipe ingredients**. Pantry stock reduces cash needed tonight but still has value. Leftover budget is a projection, not a bank balance or actual expense ledger. Three displayed dinners are alternatives; pantry is not consumed across all three.

Oil, salt, cumin and turmeric are costed explicitly. Water is assumed available. Full packet purchases, fuel, delivery and side dishes are outside this estimate. Cooked chickpeas use a cooked/drained quantity and matching price basis; do not enter a dry-chickpea price in that row.

## What the AI does

Workflow: validate inputs → scale recipes → filter ingredients → calculate costs → keep affordable meals → AI selects up to three and explains → validate returned IDs → display costed recipes and CSV shopping lists.

The model is constrained to eligible IDs using a strict JSON schema. Python also rejects duplicate/unknown IDs, wrong counts, empty explanations and incomplete output. Budget figures and recipe steps displayed by the UI are never taken from model output. Ingredient exclusions are enforced before the API call. Preference text is a soft preference; use the exclusion controls for ingredients that must be removed.

This implements **Generative AI** and an **AI workflow**. It is not an autonomous agent or multi-agent system. Hackathon acceptance is up to the organisers.

## File guide

| File | Purpose |
|---|---|
| `app.py` | Streamlit screen, inputs, result display and CSV downloads |
| `planner.py` | Portion scaling, budget calculations, filters and one Groq API request |
| `catalog.json` | Six recipes and 14 ingredient sample prices |
| `requirements.txt` | Two direct dependencies |
| `.streamlit/config.toml` | Theme and disabled Streamlit usage telemetry |
| `secrets.example.toml` | Placeholder key configuration; contains no real key |
| `tests/test_planner.py` | Calculation and simulated API tests |
| `tests/test_app.py` | Streamlit AppTest interaction tests |
| `TEST_REPORT.md` | What was actually tested and remaining checks |

## Run the tests

From the project folder with the environment active:

```bash
python -m unittest discover -s tests -v
```

No API key is required and no real API calls are made by these tests. On Windows, replace `python` with `.\.venv\Scripts\python.exe` if the environment is not activated.

## Troubleshooting

| Symptom | Action |
|---|---|
| `No module named streamlit` | Install `requirements.txt` with the same Python used to run the app. |
| `app.py` not found | Open the extracted project folder or correct the deployment main-file path. |
| Missing API key | Select Sample mode or add a Groq key as described above. |
| Key rejected / 401 | Copy a valid Groq key; a Gemini/OpenAI key will not work. |
| Permission / 403 | Check the Groq account's model permissions. |
| Free quota / 429 | Wait for the account's quota to reset; Sample mode still works. |
| Rejected request / 400 or model unavailable / 404 | Check the current model documentation. Share the app error and we can update the integration. Do not publish your key. |
| AI validation failed | Try again once; if it persists, use Sample mode and inspect model/API compatibility. |
| No dinner fits | Check pantry quantities and prices or increase tonight's budget. |
| No catalogue recipes match | The exclusions removed all six recipes; change filters or add a recipe. |
| Results disappear after an edit | Intentional: regenerate to avoid showing stale costs. |

## Current limits

Prices are illustrative and must be replaced for a real household estimate. No live market feed, nutrition analysis, medical diet advice, seasonal-price optimisation, monthly planning, automatic inventory update or actual-spending tracker is included. Ingredient exclusions do not check product labels or cross-contamination. Recipes and cooking times are approximate starter content, not professionally validated meal plans. AI text can be wrong even when its JSON and IDs are valid.

## Documentation checked for this package

- Groq models: https://console.groq.com/docs/models
- Groq free limits: https://console.groq.com/docs/rate-limits
- Groq strict structured output: https://console.groq.com/docs/structured-outputs
- Groq reasoning options: https://console.groq.com/docs/reasoning
- Streamlit free hosting: https://docs.streamlit.io/deploy/streamlit-community-cloud
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Hugging Face plan restrictions: https://huggingface.co/docs/hub/spaces-overview

Checked 4 October 2026. Provider limits and availability may change; your account console is authoritative.
