# Copilot instructions

## Build, run, test, and lint

- Install dependencies with `pip install -r requirements.txt`.
- Run the app locally with `streamlit run app.py`.
- The dev container starts the app with:
  `streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false`
  and forwards port `8501`.
- Configure local secrets in `.streamlit/secrets.toml` (which is ignored by Git):
  `PROJECT_ACCESS_CODE`, `GEMINI_API_KEY`, and `GEMINI_MODEL`.
- There is currently no automated test suite, test runner, build command, or lint configuration. There is therefore no single-test command; use `python -m py_compile app.py` for a focused syntax check and manually smoke-test the Streamlit flow.

## Architecture

This is currently a single-file Streamlit prototype in `app.py`. Streamlit reruns the script on interaction, so authentication and the latest Gemini response are persisted in `st.session_state`.

The UI first presents an access-code form. The submitted code is compared with the `PROJECT_ACCESS_CODE` secret using `hmac.compare_digest`; unauthorized users are stopped with `st.stop()`. After authorization, the page exposes an interaction smoke test and a Gemini connection test. The Gemini request uses `google-genai` and the `GEMINI_API_KEY` and `GEMINI_MODEL` secrets, then stores the returned text in session state for display.

The intended product direction is documented in `docs/phase1-proposal.md`: onboarding data should produce a beginner workout plan, with feedback-driven adjustment and a reviewed exercise library. Safety-related behavior must remain conservative: the app should not diagnose pain or promise treatment, and concerning symptoms should lead to professional-care guidance rather than exercise recommendations.

## Repository conventions

- Keep Streamlit page setup and top-level UI flow in `app.py` unless the application grows enough to justify modules.
- Treat Streamlit reruns as normal. Put values that must survive a button click or rerun in `st.session_state`, and clear or update them explicitly when starting a new operation.
- Read credentials and deployment-specific settings from `st.secrets`; never hard-code them or commit `.streamlit/secrets.toml`, `.env`, or virtual-environment files.
- Use constant-time comparison for access-code checks and preserve the current fail-closed authorization flow.
- Keep user-facing AI failures generic; do not expose API keys, raw provider errors, or quota details in the UI. Use the existing success/warning/error Streamlit feedback pattern.
- Keep Gemini model selection configurable through `GEMINI_MODEL`, and use the `google-genai` client through the dependency declared in `requirements.txt`.
- Align new workout-generation behavior with the proposal's inputs (goal, experience, schedule, equipment, preferences, and limitations) and its beginner-focused, reviewed-content approach.
