import requests
import streamlit as st

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI RAG Assistant",
    page_icon="🤖",
    layout="wide",
)

conversations = requests.get(
    f"{API}/conversations"
).json()

for conv in conversations:

    col1, col2 = st.sidebar.columns([4,1])

    with col1:

        if st.button(
            f"Conversation {conv['id']}",
            key=f"open_{conv['id']}",
            use_container_width=True,
        ):

            st.session_state.conversation_id = conv["id"]

            history = requests.get(
                f"{API}/history/{conv['id']}"
            ).json()

            st.session_state.messages = history

            st.rerun()

    with col2:

        if st.button(
            "🗑️",
            key=f"delete_{conv['id']}"
        ):

            requests.delete(
                f"{API}/conversation/{conv['id']}"
            )

            if st.session_state.conversation_id == conv["id"]:

                st.session_state.conversation_id = None

                st.session_state.messages = []

            st.rerun()

st.title("AI RAG Assistant")

if st.sidebar.button(
        f"Conversation {conv['id']}",
        key=f"conv_{conv['id']}"
    ):

    st.session_state.conversation_id = conv["id"]

    history = requests.get(
        f"{API}/history/{conv['id']}"
    ).json()

    st.session_state.messages = history

    st.rerun()
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


# Show previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Wait for user input
question = st.chat_input("Ask a question about FastAPI...")

if question:

    # show user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # ask backend
    response = requests.post(
        f"{API}/chat",
        json={
            "question": question,
            "conversation_id": st.session_state.conversation_id,
        },
    )

    data = response.json()

    st.session_state.conversation_id = data["conversation_id"]

    answer = data["answer"]

    # save assistant answer
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # display assistant answer
    with st.chat_message("assistant"):
        st.markdown(answer)

        st.caption(f"Confidence: {data['confidence']:.2f}")

        with st.expander("Sources"):

            for source in data["sources"]:
                st.write("📄", source["document"])