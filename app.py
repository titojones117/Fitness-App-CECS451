import json
import hmac
from pathlib import Path

import jsonschema
import streamlit as st
from google import genai

CONFIG_PATH = Path(__file__).with_name("onboarding_config.json")
EXERCISE_CATALOG_PATH = Path(__file__).with_name("exercise_catalog.json")
GEMINI_INSTRUCTIONS_PATH = Path(__file__).with_name("gemini_instructions.txt")
RESPONSE_SCHEMA_PATH = Path(__file__).with_name("workout_response_schema.json")


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


def prepare_gemini_request(onboarding_data, eligible_exercises):
    with GEMINI_INSTRUCTIONS_PATH.open(encoding="utf-8") as instructions_file:
        instructions = instructions_file.read()
    if not instructions.strip():
        raise ValueError("The generation instructions are empty.")

    with RESPONSE_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        response_schema = json.load(schema_file)
    if not isinstance(response_schema, dict) or not response_schema:
        raise ValueError("The response schema must be a nonempty JSON object.")

    return {
        "instructions": instructions,
        "input": {
            "user_selections": onboarding_data,
            "eligible_exercises": eligible_exercises,
        },
        "response_schema": response_schema,
    }


def generate_workout_plan(prepared_request):
    with genai.Client(api_key=st.secrets["GEMINI_API_KEY"]) as client:
        response = client.interactions.create(
            model=st.secrets["GEMINI_MODEL"],
            system_instruction=prepared_request["instructions"],
            input=json.dumps(prepared_request["input"], ensure_ascii=False),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": prepared_request["response_schema"],
            },
        )

    raw_response = response.output_text
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ValueError("Gemini returned no text.")
    plan = json.loads(raw_response)
    jsonschema.validate(instance=plan, schema=prepared_request["response_schema"])

    eligible_ids = {
        exercise["id"] for exercise in prepared_request["input"]["eligible_exercises"]
    }
    for workout in plan["workouts"]:
        workout["exercises"] = [
            exercise for exercise in workout["exercises"]
            if exercise["exercise_id"] in eligible_ids
        ]
    plan["workouts"] = [workout for workout in plan["workouts"] if workout["exercises"]]
    if not plan["workouts"]:
        raise ValueError("Gemini returned no usable workouts.")

    return {
        "plan": plan,
        "raw_response": raw_response,
        "user_selections": prepared_request["input"]["user_selections"],
    }


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
            try:
                prepared_request = prepare_gemini_request(
                    onboarding_data, eligible_exercises
                )
            except (OSError, ValueError):
                st.error(
                    "Unable to prepare the Gemini request. "
                    "Please try again or contact the team."
                )
            else:
                st.session_state.onboarding_data = onboarding_data
                st.session_state.eligible_exercises = eligible_exercises
                st.session_state.prepared_request = prepared_request
                try:
                    with st.spinner("Generating your workout plan..."):
                        generation_result = generate_workout_plan(prepared_request)
                except (ValueError, jsonschema.ValidationError, jsonschema.SchemaError):
                    st.error(
                        "Gemini did not return a usable workout plan. Please try again."
                    )
                except Exception:
                    st.error(
                        "Unable to generate a workout plan. "
                        "Please try again or contact the team."
                    )
                else:
                    st.session_state.generation_result = generation_result
                    st.success("Workout plan generated.")

if "onboarding_data" in st.session_state:
    with st.expander("Submitted onboarding JSON"):
        st.json(st.session_state.onboarding_data)

if "generation_result" in st.session_state:
    generation_result = st.session_state.generation_result
    st.subheader("Workout plan - last successful generation")
    st.caption("Selections used for this result:")
    st.json(generation_result["user_selections"])
    st.json(generation_result["plan"])
    st.caption(
        "The download preserves Gemini's original JSON. The displayed plan excludes "
        "exercises unavailable for these selections."
    )
    st.download_button(
        "Download Gemini response (.json)",
        data=generation_result["raw_response"].encode("utf-8"),
        file_name="gemini_response.json",
        mime="application/json",
        on_click="ignore",
    )

if "prepared_request" in st.session_state:
    with st.expander("Prepared Gemini request (last prepared submission)"):
        st.info(
            "These are the inputs for the last prepared request. "
            "This preview does not indicate that generation succeeded."
        )
        prepared_request = st.session_state.prepared_request
        st.caption("Generation instructions")
        st.code(prepared_request["instructions"], language="text")
        st.caption("Input JSON")
        st.code(
            json.dumps(prepared_request["input"], indent=2, ensure_ascii=False),
            language="json",
        )
        st.caption("Response schema")
        st.code(
            json.dumps(prepared_request["response_schema"], indent=2, ensure_ascii=False),
            language="json",
        )

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