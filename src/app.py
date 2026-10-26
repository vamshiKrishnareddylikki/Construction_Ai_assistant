"""
Web app for the Construction AI Assistant.
Tab 1: chat with the AI agent (uses all tools).
Tab 2: simple document Q&A (RAG only).
Run with:  streamlit run src/app.py
"""
import json
import streamlit as st
from ask_docs import load_index, answer
from agent import run_agent

st.set_page_config(page_title="Construction AI Assistant", page_icon="🏗️", layout="wide")
st.title("🏗️ Construction AI Assistant")

agent_tab, docs_tab = st.tabs(["🤖 Project Assistant (agent)", "📄 Policy Q&A"])

# ---------------- Tab 1: Agent chat ----------------
with agent_tab:
    st.caption("Ask about active projects, delay risk, past project statistics, company policy, "
               "or today's field reports. The assistant picks the right tools and shows its work.")

    if "chat" not in st.session_state:
        st.session_state.chat = []      # what's shown on screen
        st.session_state.history = []   # what the agent remembers (last 3 exchanges)

    with st.sidebar:
        st.subheader("Try asking")
        st.markdown("- Which active projects are most at risk of running late?\n"
                    "- What does our contract say about hurricane delays?\n"
                    "- Average delay for past marina projects?\n"
                    "- What happened on site today?\n"
                    "- What documents do we need for final payment?")
        if st.button("Clear conversation"):
            st.session_state.chat, st.session_state.history = [], []
            st.rerun()

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("steps"):
                with st.expander(f"🔧 Tools used ({len(msg['steps'])})"):
                    for s in msg["steps"]:
                        st.markdown(f"**{s['tool']}** `{s['arguments']}`")

    question = st.chat_input("Ask the project assistant...")
    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking and checking project tools..."):
                try:
                    reply, steps = run_agent(question, st.session_state.history, verbose=False)
                except Exception:
                    reply, steps = ("The AI service is busy right now. Please try again in a "
                                    "few minutes."), []
            st.markdown(reply)
            if steps:
                with st.expander(f"🔧 Tools used ({len(steps)})"):
                    for s in steps:
                        st.markdown(f"**{s['tool']}** `{s['arguments']}`")
        st.session_state.chat.append({"role": "assistant", "content": reply, "steps": steps})
        st.session_state.history += [{"role": "user", "content": question},
                                     {"role": "assistant", "content": reply}]
        st.session_state.history = st.session_state.history[-6:]

# ---------------- Tab 2: Document Q&A ----------------
with docs_tab:
    st.caption("Answers come only from company documents, with sources.")

    @st.cache_resource
    def get_index():
        return load_index()

    doc_question = st.text_input("Your policy question")
    if st.button("Ask", type="primary") and doc_question.strip():
        with st.spinner("Searching company documents..."):
            try:
                reply, matches = answer(doc_question, get_index())
            except Exception:
                st.error("The AI service is busy right now. Please try again in a few minutes.")
                st.stop()
        st.subheader("Answer")
        st.markdown(reply)
        st.subheader("Sources used")
        for score, chunk in matches:
            with st.expander(f"{chunk['source']} > {chunk['section']}  (match: {score:.2f})"):
                st.text(chunk["text"])
