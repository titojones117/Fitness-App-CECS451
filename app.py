import hmac

import streamlit as st
from google import genai

st.set_page_config(page_title="Streamlit Connection Test")
st.title("Streamlit Connection Test")

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
    st.success("A text response was received from Gemini.")
    st.write(st.session_state.ai_test_result)
