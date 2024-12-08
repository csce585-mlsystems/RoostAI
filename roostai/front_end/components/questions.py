import streamlit as st
from typing import Dict, Optional
from .modal import show_modal, close_modal


def render_likert_question(question: Dict, key_prefix: str) -> Optional[int]:
    """Render a Likert scale question."""
    st.write(question["text"])

    options = {i: question["labels"].get(i, str(i)) for i in question["options"]}
    response = st.radio(
        "Select your answer:",
        options=list(options.keys()),
        format_func=lambda x: f"{x} - {options[x]}" if x in [1, 5] else str(x),
        key=f"{key_prefix}_{question['id']}",
        horizontal=True,
        label_visibility="collapsed",
        index=None,  # No default selection
    )

    return response


def render_text_question(question: Dict, key_prefix: str) -> Optional[str]:
    """Render a text input question."""
    return st.text_area(question["text"], key=f"{key_prefix}_{question['id']}")


def render_per_query_questions(config, interaction_id: str) -> Dict:
    """Render per-query questions in a modal."""
    show_modal()

    with st.container():
        # Display the last interaction
        with st.expander("View Last Response", expanded=True):
            st.markdown("**Your Question:**")
            st.write(st.session_state.current_interaction["query"])
            st.markdown("**System Response:**")
            st.markdown(st.session_state.current_interaction["response"])

        responses = {}

        st.subheader("Please rate the last response")

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
                    st.error("Please answer all questions before continuing.")

        return {}


def render_overall_survey(config) -> Dict:
    """Render overall survey questions in a modal."""
    show_modal()

    with st.container():
        st.subheader("Overall System Survey")
        st.write("Please provide your feedback about the overall system:")

        responses = {}

        # Render questions
        for question in config.overall_questions:
            st.markdown("---")
            if question["type"] == "likert":
                response = render_likert_question(question, "overall")
                responses[question["id"]] = response
            elif question["type"] == "text":
                response = render_text_question(question, "overall")
                if response:  # Only include non-empty text responses
                    responses[question["id"]] = response

        # Add submit button with columns for error message
        col1, col2 = st.columns([4, 1])
        with col2:
            submit_button = st.button(
                "Submit Survey",
                key="submit_overall_survey",
                type="primary",
                use_container_width=True,
            )

        if submit_button:
            required_answered = all(
                responses.get(q["id"]) is not None
                for q in config.overall_questions
                if q["type"] == "likert"  # All Likert questions are required
            )

            if required_answered:
                st.session_state.overall_survey_responses = responses
                close_modal()
                return responses
            else:
                with col1:
                    st.error("Please answer all required questions before submitting.")

        return {}
