import json
import hmac
from pathlib import Path

import streamlit as st
from google import genai

CONFIG_PATH = Path(__file__).with_name("onboarding_config.json")


def load_onboarding_config():
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def parse_and_validate_plan(response_text):
    cleaned_response = response_text.strip()
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.split("\n", 1)[1]
        cleaned_response = cleaned_response.rsplit("```", 1)[0].strip()

    plan = json.loads(cleaned_response)
    if not isinstance(plan, dict):
        raise ValueError("The response was not a JSON object.")
    if not isinstance(plan.get("plan_title"), str) or not plan["plan_title"].strip():
        raise ValueError("The response did not include a plan title.")

    weekly_schedule = plan.get("weekly_schedule")
    if not isinstance(weekly_schedule, list) or not weekly_schedule:
        raise ValueError("The response did not include a weekly schedule.")

    for session in weekly_schedule:
        if not isinstance(session, dict):
            raise ValueError("A workout session was not an object.")
        if not isinstance(session.get("day"), str):
            raise ValueError("A workout session is missing its day.")
        exercises = session.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            raise ValueError("A workout session is missing exercises.")
        for exercise in exercises:
            if not isinstance(exercise, dict):
                raise ValueError("An exercise was not an object.")
            required_fields = ("name", "sets", "reps", "instructions")
            if any(not exercise.get(field) for field in required_fields):
                raise ValueError("An exercise is missing required details.")

    return plan


onboarding_config = load_onboarding_config()
st.set_page_config(page_title="Fitness App")
st.title("Fitness App")

if not st.session_state.get("authorized", False):
    with st.form("access_form"):
        code = st.text_input("Access code", type="password")
        submitted = st.form_submit_button("Unlock")

    if submitted:
        expected = st.secrets["PROJECT_ACCESS_CODE"]

        if expected and hmac.compare_digest(
            code.encode("utf-8"), expected.encode("utf-8")
        ):
            st.session_state.authorized = True
            st.rerun()
        else:
            st.error("Incorrect access code.")

    st.stop()

st.success("Access granted.")

if "ai_test_result" not in st.session_state:
    if st.button("Test interaction"):
        st.info("Button interaction works. No AI request was made.")

    if st.button("Test AI connection"):
        st.session_state.pop("ai_test_result", None)

        try:
            with st.spinner("Waiting for Gemini..."):
                with genai.Client(
                    api_key=st.secrets["GEMINI_API_KEY"]
                ) as client:
                    response = client.interactions.create(
                        model=st.secrets["GEMINI_MODEL"],
                        input=(
                            "This is a software connection test. "
                            "Reply with exactly: Gemini connection successful."
                        ),
                        generation_config={"max_output_tokens": 256},
                    )

            if response.output_text:
                st.session_state.ai_test_result = response.output_text
            else:
                st.warning("The request completed without a text response.")

        except Exception:
            st.error(
                "The AI connection test failed. Check the configured API key, "
                "model name, and available quota."
            )

if "ai_test_result" in st.session_state and not st.session_state.get(
    "onboarding_started", False
):
    st.success("Gemini connection successful.")
    st.write(st.session_state.ai_test_result)
    if st.button("Continue to onboarding"):
        st.session_state.onboarding_started = True
        st.rerun()

if st.session_state.get("onboarding_started", False):
    st.header(onboarding_config["title"])
    fields = onboarding_config["fields"]

    with st.form("onboarding_form"):
        goal = st.selectbox(fields["goal"]["label"], fields["goal"]["options"])
        equipment = st.multiselect(
            fields["equipment"]["label"], fields["equipment"]["options"]
        )
        available_days = st.multiselect(
            fields["available_days"]["label"],
            [option["value"] for option in fields["available_days"]["options"]],
            format_func=lambda value: next(
                option["label"]
                for option in fields["available_days"]["options"]
                if option["value"] == value
            ),
            help=fields["available_days"]["help"],
        )
        session_minutes = st.selectbox(
            fields["session_minutes"]["label"],
            fields["session_minutes"]["options"],
            format_func=lambda minutes: f"{minutes} minutes",
            help=fields["session_minutes"]["help"],
        )
        submitted = st.form_submit_button("Generate workout plan")

    if submitted:
        if not equipment:
            st.error("Select at least one equipment option.")
        elif not available_days:
            st.error("Select at least one available day.")
        else:
            onboarding_data = {
                "goal": goal,
                "equipment": equipment,
                "available_days": available_days,
                "session_minutes": session_minutes,
            }
            st.session_state.onboarding_data = onboarding_data
            st.success("Onboarding submitted. Displaying your onboarding JSON.")

    if "onboarding_data" in st.session_state:
        with st.expander("Submitted onboarding JSON"):
            st.json(st.session_state.onboarding_data)
