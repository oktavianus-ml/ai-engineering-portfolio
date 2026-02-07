import streamlit as st
from api.chat_engine import handle_chat_engine


st.set_page_config(
    page_title="CNI AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 CNI AI Chatbot")
st.caption("Produk • SOP • Customer Service")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("Contoh: alur pelayanan customer service")

if query:
    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    with st.spinner("🤖 AI sedang berpikir..."):
        answer = handle_chat_engine(query)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.rerun()
