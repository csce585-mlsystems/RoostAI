import streamlit as st
from typing import Dict, Optional
import asyncio
from datetime import datetime

from roostai.back_end.main import UniversityChatbot
from components.utils import save_interaction


async def initialize_chatbot() -> UniversityChatbot:
    """Initialize the chatbot instance."""
    return UniversityChatbot()


def render_chat_interface(chatbot: UniversityChatbot) -> Optional[Dict]:
    """Render chat interface and return interaction details if query is submitted."""

    # Create a horizontal layout for the header
    header_col1, header_col2 = st.columns([2, 3])

    with header_col1:
        st.subheader("Chat with RoostAI...")

    with header_col2:
        # Create an expander for feedback
        with st.expander("Help Improve RoostAI", expanded=False, icon="📝"):
            st.markdown(
                """
                We'd love to hear your thoughts about RoostAI! Your feedback helps us improve.
                """
            )

            # Show progress if there are draft responses
            if st.session_state.draft_survey_responses:
                st.info("You have a partially completed survey")
                feedback_label = "Continue Survey"
            else:
                feedback_label = "Start Survey"

            if st.button(
                feedback_label,
                type="primary",
                use_container_width=True,
                key="feedback_button_header",
            ):
                st.session_state.survey_mode = True
                st.rerun()

    # Initialize chat history in session state if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"])

    # Chat input
    query = st.chat_input("Ask a Question About USC")

    if query:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Record start time
                start_time = datetime.now()

                # Process query
                results = asyncio.run(chatbot.process_query(query))

                # Record end time
                end_time = datetime.now()

                # Display response
                if results["response"]:
                    st.markdown(results["response"])
                    # Add assistant message to chat history
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": results["response"]}
                    )

                    # Store interaction for logging
                    interaction = {
                        "timestamp": start_time.isoformat(),
                        "query": query,
                        "response": results["response"],
                        "processing_time": (end_time - start_time).total_seconds(),
                        "raw_results": results,
                    }

                    # Save interaction without feedback
                    save_interaction(
                        st.session_state.config.responses_dir,
                        st.session_state.session_id,
                        st.session_state.interaction_num,
                        interaction,
                        {},
                    )
                    st.session_state.interaction_num += 1

                    # After a few interactions, show a gentle reminder if no feedback started
                    if (
                        len(st.session_state.chat_history) >= 6
                        and not st.session_state.draft_survey_responses
                    ):
                        st.info(
                            """
                            👋 Enjoying RoostAI? We'd love to hear your thoughts! 
                            Click the feedback expander above to share your experience.
                            """
                        )

                else:
                    st.error("Failed To Get a Response. Please Try Again.")
                    return None

    return None
