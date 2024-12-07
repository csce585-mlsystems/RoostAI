import asyncio
import time
import uuid

import streamlit as st

from components.chat import initialize_chatbot, render_chat_interface
from components.questions import render_per_query_questions, render_overall_survey
from components.utils import save_interaction, save_overall_survey
from config import SurveyConfig

# Page config
st.set_page_config(page_title="RoostAI Survey", page_icon="🎓", layout="wide")

# Load config
config = SurveyConfig()

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "interaction_num" not in st.session_state:
    st.session_state.interaction_num = 0
if "chatbot" not in st.session_state:
    st.session_state.chatbot = asyncio.run(initialize_chatbot())
if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "waiting_for_feedback" not in st.session_state:
    st.session_state.waiting_for_feedback = False
if "show_modal" not in st.session_state:
    st.session_state.show_modal = False

# Sidebar with system information
with st.sidebar:
    # Show system information after first interaction
    if len(st.session_state.chat_history) > 0:
        st.subheader("About RoostAI")
        st.markdown(
            """
        RoostAI is a Retrieval-Augmented Generation (RAG) system 
        designed to provide accurate information about USC using:

        - Vector similarity search
        - Cross-encoder reranking
        - Large Language Model response generation
        """
        )

    # Show warning if waiting for feedback
    if st.session_state.waiting_for_feedback:
        st.warning("Please complete the feedback survey before continuing.")

    # Session information
    st.markdown("---")  # Separator between sections
    st.subheader("Session Information")
    st.write(f"Session ID: {st.session_state.session_id}")
    # Divide by 2 because each interaction has user + assistant message
    st.write(f"Interactions: {len(st.session_state.chat_history) // 2}")

# Title and initial description (only shown before first interaction)
if len(st.session_state.chat_history) == 0:
    st.title("RoostAI Survey")
    st.markdown(
        """
    This is a survey application to evaluate our Retrieval-Augmented Generation (RAG) system 
    for the University of South Carolina. The system uses advanced natural language processing 
    to provide accurate information about USC by combining:

    - Vector similarity search
    - Cross-encoder reranking
    - Large Language Model response generation

    Please interact with the system by asking questions about USC, and provide feedback 
    about your experience.
    """
    )
else:
    # Just show the title if already interacting
    st.title("RoostAI Survey")

# Main interaction loop
if not st.session_state.survey_completed:
    # Show chat interface
    interaction = render_chat_interface(st.session_state.chatbot)

    # Show per-query questions if waiting for feedback
    if st.session_state.waiting_for_feedback and st.session_state.show_modal:
        responses = render_per_query_questions(
            config, str(st.session_state.interaction_num)
        )

        # If all questions are answered
        if responses:
            # Save interaction data
            save_interaction(
                config.responses_dir,
                st.session_state.session_id,
                st.session_state.interaction_num,
                st.session_state.current_interaction,
                responses,
            )

            # Reset feedback states
            st.session_state.waiting_for_feedback = False
            st.session_state.show_modal = False
            st.session_state.needs_feedback = False
            st.session_state.last_response_shown = False
            st.rerun()

    # Add option to end survey
    if (
        not st.session_state.needs_feedback
    ):  # Only show end survey button if no feedback is pending
        st.markdown("---")
        if st.button("End Survey", key="end_survey_button"):
            st.session_state.survey_completed = True
            st.session_state.show_modal = True
            st.rerun()

# Show overall survey when completed
if st.session_state.survey_completed:
    responses = render_overall_survey(config)

    # If all required questions are answered and submit button clicked
    if responses:
        save_overall_survey(
            config.responses_dir, st.session_state.session_id, responses
        )

        st.success(
            """
        Thank you for completing the survey! Your feedback will help us improve 
        the RoostAI system.
        """
        )
        st.balloons()

        # Reset session state after a brief delay
        with st.spinner("Resetting session..."):
            time.sleep(2)

        # Reset all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Initialize new session
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.interaction_num = 0
        st.session_state.chatbot = asyncio.run(initialize_chatbot())
        st.session_state.survey_completed = False
        st.session_state.chat_history = []
        st.session_state.waiting_for_feedback = False
        st.session_state.show_modal = False

        # Rerun the app to show the start page
        st.rerun()
