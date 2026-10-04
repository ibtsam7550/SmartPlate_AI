# Test report — SmartPlate AI

Tested on 4 October 2026 in a Linux environment with Python 3.12.14, Streamlit 1.50.0 and Requests 2.32.5.

## Automated tests

Command:

```bash
python -m unittest discover -s tests -v
```

Result: **25 test methods passed**. Several methods contain multiple cases. The suite comprises 11 budgeting/catalogue tests, 7 API-handling tests and 7 Streamlit interface tests. See `test-results.txt` for the execution log.

Checked:

- A manually calculated dal-and-rice bill of Rs. 273.22 with the supplied prices.
- Partial and full pantry stock, no negative purchasing quantities, zero budget with full stock.
- Exact budget boundary (Rs. 273.22 allowed; Rs. 273.21 excludes that meal).
- Portion scaling, whole eggs, consistent sum of rounded line totals, and all six recipes across 1–12 servings.
- Changed prices, invalid budgets, invalid quantities and missing/invalid price values.
- Vegetarian filtering, ingredient exclusions, no matching recipes and no affordable recipes.
- Valid structured API response and request configuration using a simulated HTTP response.
- Unknown/duplicate IDs, wrong counts, bad explanations, incomplete and malformed responses.
- HTTP 400/401/403/404/429/500/503 handling, timeouts and connection errors.
- Missing key and Sample mode make no AI request.
- Actual Streamlit AppTest controls: initial load, result rendering, input edits, stale-result clearing, pantry and price edits, no-results messages, missing-key message, simulated Live AI success and quota failure.

## Server smoke test

Started the app with the real Streamlit server. Its `/_stcore/health` endpoint returned **HTTP 200, `ok`**, and the root page returned **HTTP 200 with HTML**. The server was stopped after this check.

The interface tests use Streamlit's official AppTest runner. They are not browser screenshot or mobile-layout tests. `missing ScriptRunContext` warnings in the unit-test log are produced by the test harness; the suite exits successfully.

## Not verified here

- No real Groq generation was performed because no user API key was provided. Mocked API tests do not prove real model quality, account permissions, free quota or connectivity from a future host.
- No GitHub repository or public deployment was created. Deployment must be tested in the user's account.
- No Windows/macOS execution was performed. The code is portable Python, but the tested OS is Linux.
- No live grocery prices, diet adequacy, taste or recipe cooking trials were verified. Sample prices and approximate recipes are labelled in the app.

## Required user acceptance test

1. Run Sample mode with four people, Rs. 600 and no pantry stock. Confirm three options and expandable ingredients/steps.
2. Add 300 g rice and 250 g lentils. Confirm dal-and-rice extra spending becomes Rs. 83.22.
3. Download a shopping CSV and open it. It should list only missing ingredients for the selected dinner.
4. With your own **Groq Free-plan key**, select Live AI and click Generate. Check that explanations are relevant and no error appears.
5. Try Roman Urdu and one ingredient exclusion. Confirm the exclusion is respected in displayed ingredients.
6. After deployment, repeat Sample and Live AI checks using the public app URL.

The app is ready for those acceptance checks; it is not claimed to be live-API-tested or publicly deployed.
