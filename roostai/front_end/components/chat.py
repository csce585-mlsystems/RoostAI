import streamlit as st
from typing import Dict, Optional
import asyncio
from datetime import datetime

from roostai.back_end.main import UniversityChatbot


async def initialize_chatbot() -> UniversityChatbot:
    """Initialize the chatbot instance."""
    return UniversityChatbot()


def render_chat_interface(chatbot: UniversityChatbot) -> Optional[Dict]:
    """Render chat interface and return interaction details if query is submitted."""
    st.subheader("Chat with RoostAI")

    # Initialize chat history and feedback states in session state if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "needs_feedback" not in st.session_state:
        st.session_state.needs_feedback = False
    if "last_response_shown" not in st.session_state:
        st.session_state.last_response_shown = False

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"])

    # Chat input
    query = st.chat_input(
        "Please provide feedback for the previous response before asking a new question."
        if st.session_state.needs_feedback
        else "Ask a question about USC"
    )

    if query:
        # Check if feedback is needed for previous interaction
        if st.session_state.needs_feedback:
            st.error(
                "Please provide feedback for the previous response before asking a new question."
            )
            # Show feedback button again
            if st.button("Provide Feedback", key="feedback_reminder", type="primary"):
                st.session_state.waiting_for_feedback = True
                st.session_state.show_modal = True
                st.rerun()
            return None

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

                    # Store current interaction for survey
                    st.session_state.current_interaction = {
                        "timestamp": start_time.isoformat(),
                        "query": query,
                        "response": results["response"],
                        "processing_time": (end_time - start_time).total_seconds(),
                        "raw_results": results,
                    }

                    # Mark that feedback is needed and response has been shown
                    st.session_state.needs_feedback = True
                    st.session_state.last_response_shown = True

                else:
                    st.error("Failed to get a response. Please try again.")
                    return None

    # Show feedback button after response is shown
    if st.session_state.needs_feedback and st.session_state.last_response_shown:
        st.markdown("---")
        feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 2, 1])
        with feedback_col2:
            if st.button(
                "Provide Feedback for this Response",
                key="feedback_button",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.waiting_for_feedback = True
                st.session_state.show_modal = True
                st.session_state.interaction_num += 1
                st.rerun()

    return None
