import streamlit as st
from typing import Dict, Optional
from .modal import show_modal, close_modal


def render_likert_question(
    question: Dict, key_prefix: str, default: Optional[int] = None
) -> Optional[int]:
    """Render a Likert scale question with default value support."""
    st.write(question["text"])

    options = {i: question["labels"].get(i, str(i)) for i in question["options"]}

    # Calculate index for default value
    if default is not None:
        default_index = list(options.keys()).index(default)
    else:
        default_index = None

    response = st.radio(
        "Select Your Answer:",
        options=list(options.keys()),
        format_func=lambda x: f"{x} - {options[x]}" if x in [1, 5] else str(x),
        key=f"{key_prefix}_{question['id']}",
        horizontal=True,
        label_visibility="collapsed",
        index=default_index,
    )

    return response


def render_text_question(
    question: Dict, key_prefix: str, default: str = ""
) -> Optional[str]:
    """Render a text input question with default value support."""
    return st.text_area(
        question["text"], value=default, key=f"{key_prefix}_{question['id']}"
    )


def render_per_query_questions(config, interaction_id: str) -> Dict:
    """Render per-query questions in a modal."""
    show_modal()

    with st.container():
        responses = {}

        st.subheader("Please Rate the Last Response")

        # Render questions
        for question in config.per_query_questions:
            st.markdown("---")
            if question["type"] == "likert":
                response = render_likert_question(
                    question, f"per_query_{interaction_id}"
                )
                responses[question["id"]] = response

        # Add submit button with columns for error message
        col1, col2 = st.columns([4, 1])
        with col2:
            submit_button = st.button(
                "Submit Feedback",
                key=f"submit_feedback_{interaction_id}",
                type="primary",
                use_container_width=True,
            )

        if submit_button:
            if all(v is not None for v in responses.values()):
                st.session_state.per_query_responses = responses
                close_modal()
                return responses
            else:
                with col1:
                    st.error("Please Answer All Questions Before Continuing")

        return {}


def render_overall_survey(config) -> Dict:
    """Render overall survey questions with draft saving."""
    st.subheader("We'd Love Your Feedback!")
    st.write("Please share your thoughts about RoostAI:")

    # Initialize responses with existing drafts
    responses = st.session_state.draft_survey_responses.copy()

    # Render questions
    for question in config.overall_questions:
        st.markdown("---")
        if question["type"] == "likert":
            # Pass default value from draft
            response = render_likert_question(
                question, "overall", default=responses.get(question["id"])
            )
            if response is not None:  # Update draft when changed
                responses[question["id"]] = response
        elif question["type"] == "text":
            # Pass default value from draft
            response = render_text_question(
                question, "overall", default=responses.get(question["id"], "")
            )
            if response:  # Update draft when changed
                responses[question["id"]] = response

    # Save drafts to session state
    st.session_state.draft_survey_responses = responses.copy()

    # Add columns for buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Return to Chat", type="secondary", use_container_width=True):
            st.session_state.survey_mode = False
            st.rerun()

    with col2:
        if st.session_state.draft_survey_responses:
            if st.button(
                "Clear Draft Responses", type="secondary", use_container_width=True
            ):
                st.session_state.draft_survey_responses = {}
                st.rerun()

    st.markdown("---")

    if st.button("Submit Feedback", type="primary", use_container_width=True):
        required_answered = all(
            responses.get(q["id"]) is not None
            for q in config.overall_questions
            if q["type"] == "likert"
        )

        if required_answered:
            # Clear draft after successful submission
            st.session_state.draft_survey_responses = {}
            return responses
        else:
            st.error("Please answer all required questions before submitting.")

    return {}
