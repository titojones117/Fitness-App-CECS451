import json
import hmac
from pathlib import Path

import streamlit as st
from google import genai

CONFIG_PATH = Path(__file__).with_name("onboarding_config.json")
EXERCISE_CATALOG_PATH = Path(__file__).with_name("exercise_catalog.json")
ELIGIBLE_EXERCISES_PATH = Path(__file__).with_name("eligible_exercises.json")


def load_onboarding_config():
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def create_eligible_exercises(equipment_selection):
    with EXERCISE_CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        exercise_catalog = json.load(catalog_file)

    if not isinstance(exercise_catalog, list):
        raise ValueError("The exercise catalog must be a JSON array.")

    allowed_equipment = {
        "Bodyweight only": set(),
        "Bodyweight and dumbbells": {"dumbbells"},
    }.get(equipment_selection)
    if allowed_equipment is None:
        raise ValueError("The selected equipment is not supported.")

    eligible_exercises = []
    for exercise in exercise_catalog:
        if not isinstance(exercise, dict):
            raise ValueError("An exercise catalog entry must be a JSON object.")

        exercise_equipment = exercise.get("equipment")
        if not isinstance(exercise_equipment, list):
            raise ValueError("An exercise catalog entry has invalid equipment.")

        if set(exercise_equipment).issubset(allowed_equipment):
            eligible_exercises.append(exercise)

    with ELIGIBLE_EXERCISES_PATH.open("w", encoding="utf-8") as eligible_file:
        json.dump(eligible_exercises, eligible_file, indent=2)
        eligible_file.write("\n")

    return eligible_exercises


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
        equipment = st.selectbox(
            fields["equipment"]["label"], fields["equipment"]["options"]
        )
        workouts_per_week = st.selectbox(
            fields["workouts_per_week"]["label"],
            fields["workouts_per_week"]["options"],
            help=fields["workouts_per_week"]["help"],
        )
        session_minutes = st.selectbox(
            fields["session_length_minutes"]["label"],
            fields["session_length_minutes"]["options"],
            format_func=lambda minutes: f"{minutes} minutes",
            help=fields["session_length_minutes"]["help"],
        )
        submitted = st.form_submit_button("Generate workout plan")

    if submitted:
        onboarding_data = {
            "user_selections": {
                "goal": goal,
                "equipment": equipment,
                "workouts_per_week": workouts_per_week,
                "session_length_minutes": session_minutes,
            }
        }
        try:
            eligible_exercises = create_eligible_exercises(equipment)
        except (OSError, json.JSONDecodeError, ValueError):
            st.error("Unable to create the eligible exercise library.")
        else:
            st.session_state.onboarding_data = onboarding_data
            st.session_state.eligible_exercises = eligible_exercises
            st.success("Onboarding submitted. Created your eligible exercise library.")

    if "onboarding_data" in st.session_state:
        with st.expander("Submitted onboarding JSON"):
            st.json(st.session_state.onboarding_data)

    if "eligible_exercises" in st.session_state:
        with st.expander("Eligible exercises JSON"):
            st.json(st.session_state.eligible_exercises)
