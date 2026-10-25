"""
Tool 3: Web page for the Document Q&A bot.
Lets non-technical staff ask questions in a browser instead of the terminal.
Run with:  streamlit run src/app.py
"""
import streamlit as st
from ask_docs import load_index, answer

st.set_page_config(page_title="Construction Docs Assistant", page_icon="🏗️")
st.title("🏗️ Construction Docs Assistant")
st.caption("Ask questions about company contracts, safety rules, closeout, and RFIs. "
           "Answers come only from company documents, with sources.")


@st.cache_resource
def get_index():
    """Load the search index once, not on every question."""
    return load_index()


index = get_index()

examples = [
    "How many days do subcontractors have to submit a weather delay notice?",
    "What documents are needed for final payment?",
    "What do we do when a hurricane watch is issued?",
    "How long does the architect have to answer an RFI?",
]
with st.expander("Example questions"):
    for q in examples:
        st.markdown(f"- {q}")

question = st.text_input("Your question")

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Searching company documents..."):
        try:
            reply, matches = answer(question, index)
        except Exception:
            st.error("The AI service is busy right now. Please try again in a few minutes.")
            st.stop()

    st.subheader("Answer")
    st.markdown(reply)

    st.subheader("Sources used")
    for score, chunk in matches:
        with st.expander(f"{chunk['source']} > {chunk['section']}  (match: {score:.2f})"):
            st.text(chunk["text"])