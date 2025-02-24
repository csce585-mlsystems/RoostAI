import asyncio
import time
import uuid
from pathlib import Path

import streamlit as st

from components.chat import initialize_chatbot, render_chat_interface
from components.questions import render_overall_survey
from components.utils import save_overall_survey
from config import SurveyConfig

# Page config
st.set_page_config(page_title="RoostAI", page_icon="🎓", layout="wide")

# Load config
config = SurveyConfig()

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "interaction_num" not in st.session_state:
    st.session_state.interaction_num = 0
if "chatbot" not in st.session_state:
    st.session_state.chatbot = asyncio.run(initialize_chatbot())
if "survey_mode" not in st.session_state:
    st.session_state.survey_mode = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "config" not in st.session_state:
    st.session_state.config = config
if "draft_survey_responses" not in st.session_state:
    st.session_state.draft_survey_responses = {}

# Sidebar
with st.sidebar:
    # Logo
    st.image(
        str(Path(__file__).parent / "assets" / "roostai_logo.png"),
        use_container_width=True,
        output_format="PNG",
    )

    # Show system information
    st.subheader("About RoostAI")
    st.markdown(
        """
        RoostAI provides accurate information about USC using:
        - Vector similarity search
        - Cross-encoder reranking
        - Large Language Model response generation
        """
    )

    # Session information
    feedback_label = (
        "Complete Feedback"
        if st.session_state.draft_survey_responses
        else "Provide Feedback"
    )

    # Show draft status if exists
    if st.button(feedback_label, type="primary", use_container_width=True):
        st.session_state.survey_mode = True
        st.rerun()

    # Session information
    st.markdown("---")
    st.subheader("Session Information")
    st.write(f"Session ID: {st.session_state.session_id}")

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

if st.session_state.survey_mode:
    # Show survey with option to return to chat
    responses = render_overall_survey(config)

    if responses:
        save_overall_survey(
            config.responses_dir, st.session_state.session_id, responses
        )
        st.rerun()  # Just rerun to show the thank you message and reset button

else:
    # Show chat interface
    render_chat_interface(st.session_state.chatbot)
