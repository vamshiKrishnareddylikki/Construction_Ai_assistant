"""
Web app for the Construction AI Assistant.
Tab 1: chat with the AI agent (uses all tools).
Tab 2: simple document Q&A (RAG only).
Tab 3: upload a drawing set PDF for a pre-construction review.
Run with:  streamlit run src/app.py
"""
import os
import traceback
import streamlit as st
from ask_docs import load_index, answer
from agent import run_agent

st.set_page_config(page_title="Construction AI Assistant", page_icon="🏗️", layout="wide")
st.title("🏗️ Construction AI Assistant")

agent_tab, docs_tab, drawings_tab = st.tabs(
    ["🤖 Project Assistant (agent)", "📄 Policy Q&A", "📐 Drawing Review"])


def show_steps(steps):
    if steps:
        with st.expander(f"🔧 Tools used ({len(steps)})"):
            for s in steps:
                st.markdown(f"**{s['tool']}** `{s['arguments']}`")


# ---------------- Tab 1: Agent chat ----------------
with agent_tab:
    st.caption("Ask about active projects, delay risk, past project statistics, company policy, "
               "today's field reports, or drawing reviews. The assistant picks the right tools and shows its work.")

    if "chat" not in st.session_state:
        st.session_state.chat = []      # what's shown on screen
        st.session_state.history = []   # what the agent remembers (last 3 exchanges)

    with st.sidebar:
        st.subheader("Try asking")
        st.markdown("- Which active projects are most at risk of running late?\n"
                    "- What does our contract say about hurricane delays?\n"
                    "- Average delay for past marina projects?\n"
                    "- What happened on site today?\n"
                    "- What long-lead items are in the Palmetto Bay drawings?")
        if st.button("Clear conversation"):
            st.session_state.chat, st.session_state.history = [], []
            st.rerun()

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            show_steps(msg.get("steps"))

    question = st.chat_input("Ask the project assistant...")
    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking and checking project tools..."):
                try:
                    reply, steps = run_agent(question, st.session_state.history, verbose=False)
                except Exception as e:
                    traceback.print_exc()  # full error goes to the server logs for the maintainer
                    reply, steps = (f"Sorry, something went wrong ({type(e).__name__}). "
                                    "Please try again in a few minutes."), []
            st.markdown(reply)
            show_steps(steps)
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
            except Exception as e:
                traceback.print_exc()
                st.error(f"Sorry, something went wrong ({type(e).__name__}). Please try again in a few minutes.")
                st.stop()
        st.subheader("Answer")
        st.markdown(reply)
        st.subheader("Sources used")
        for score, chunk in matches:
            with st.expander(f"{chunk['source']} > {chunk['section']}  (match: {score:.2f})"):
                st.text(chunk["text"])

# ---------------- Tab 3: Drawing review ----------------
with drawings_tab:
    st.caption("Upload an architectural drawing set (PDF) for an AI-assisted pre-construction first pass: "
               "missing sheets, impact/NOA issues, long-lead items, and RFI candidates. "
               "Not included by design: quantity takeoffs, measurements, clash detection.")
    st.warning("Results are a DRAFT for PM / estimator review. Don't upload confidential drawings to a public demo.")

    uploaded = st.file_uploader("Drawing set PDF (max ~20 pages works best)", type=["pdf"])
    sample = "data/drawings/palmetto_bay_townhomes.pdf"
    use_sample = st.button("Or try the sample drawing set (Palmetto Bay Townhomes)")

    pdf_path = None
    if uploaded is not None:
        os.makedirs("data/drawings/uploads", exist_ok=True)
        pdf_path = os.path.join("data/drawings/uploads", os.path.basename(uploaded.name))
        with open(pdf_path, "wb") as f:
            f.write(uploaded.getbuffer())
    elif use_sample and os.path.exists(sample):
        pdf_path = sample

    if pdf_path and st.button("Run review", type="primary") or (use_sample and pdf_path):
        from review_drawings import review
        with st.spinner("Reading the drawings (this can take 30-60 seconds)..."):
            try:
                data, findings, report, report_path = review(pdf_path, use_cache=True)
            except Exception as e:
                traceback.print_exc()
                st.error(f"Sorry, the review failed ({type(e).__name__}). Please try again in a few minutes.")
                st.stop()
        counts = {k.replace("_", " ").title(): len(v) for k, v in findings.items()}
        cols = st.columns(len(counts))
        for col, (label, n) in zip(cols, counts.items()):
            col.metric(label, n)
        st.markdown(report)
        st.download_button("Download report (Markdown)", report,
                           file_name=os.path.basename(report_path), mime="text/markdown")
