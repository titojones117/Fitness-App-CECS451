import json
import hmac
from pathlib import Path

import streamlit as st
from google import genai

CONFIG_PATH = Path(__file__).with_name("onboarding_config.json")
EXERCISE_CATALOG_PATH = Path(__file__).with_name("exercise_catalog.json")


def load_onboarding_config():
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def load_exercise_catalog():
    with EXERCISE_CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        exercise_catalog = json.load(catalog_file)

    if not isinstance(exercise_catalog, list):
        raise ValueError("The exercise catalog must be a JSON array.")

    for exercise in exercise_catalog:
        if not isinstance(exercise, dict):
            raise ValueError("An exercise catalog entry must be a JSON object.")
        exercise_equipment = exercise.get("equipment")
        if not isinstance(exercise_equipment, list) or not all(
            isinstance(item, str) for item in exercise_equipment
        ):
            raise ValueError("An exercise catalog entry has invalid equipment.")

    return exercise_catalog


def filter_eligible_exercises(exercise_catalog, equipment_selection):
    allowed_equipment = {
        "Bodyweight only": set(),
        "Bodyweight and dumbbells": {"dumbbells"},
    }.get(equipment_selection)
    if allowed_equipment is None:
        raise ValueError("The selected equipment is not supported.")
    return [
        exercise
        for exercise in exercise_catalog
        if set(exercise["equipment"]).issubset(allowed_equipment)
    ]


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

st.header(onboarding_config["title"])
fields = onboarding_config["fields"]

with st.form("onboarding_form"):
    onboarding_data = {
        key: st.selectbox(
            field["label"],
            field["options"],
            index=None,
            help=field.get("help"),
        )
        for key, field in fields.items()
    }
    submitted = st.form_submit_button("Generate workout plan")

if submitted:
    missing_fields = [
        field["label"]
        for key, field in fields.items()
        if field["required"] and onboarding_data[key] is None
    ]
    if missing_fields:
        st.error("Select an option for: " + ", ".join(missing_fields) + ".")
    else:
        try:
            exercise_catalog = load_exercise_catalog()
            eligible_exercises = filter_eligible_exercises(
                exercise_catalog, onboarding_data["equipment"]
            )
        except (OSError, ValueError):
            st.error(
                "Unable to load the exercise catalog. Please try again or contact the team."
            )
        else:
            st.session_state.onboarding_data = onboarding_data
            st.session_state.eligible_exercises = eligible_exercises
            st.success(
                f"Onboarding submitted. {len(eligible_exercises)} exercises are eligible. "
                "Workout generation is not available yet."
            )

if "onboarding_data" in st.session_state:
    with st.expander("Submitted onboarding JSON"):
        st.json(st.session_state.onboarding_data)

with st.expander("Connection diagnostics (optional)"):
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

    if "ai_test_result" in st.session_state:
        st.write(st.session_state.ai_test_result)