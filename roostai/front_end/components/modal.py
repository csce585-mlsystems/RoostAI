import streamlit as st
from streamlit.components.v1 import html


def show_modal():
    """Show modal dialog by injecting custom HTML/CSS/JS."""
    st.markdown(
        """
        <style>
        .modal {
            display: block;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
        }
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            width: 70%;
            max-width: 800px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def close_modal():
    """Close the modal by clearing the session state."""
    if "show_modal" in st.session_state:
        del st.session_state.show_modal
