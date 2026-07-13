import requests
import streamlit as st
from pathlib import Path

API = "http://127.0.0.1:8000"

st.markdown("""
<style>

/* Rounded buttons only */
div.stButton > button {
    border-radius: 8px;
}

/* Center icon buttons */
div.stButton > button {
    display: flex;
    justify-content: center;
    align-items: center;
}

</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.logged_in:

    st.title("🔐 Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:

        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button("Login"):

            response = requests.post(
                f"{API}/login",
                json={
                    "email": email,
                    "password": password,
                },
            ).json()

            if response["success"]:

                st.session_state.logged_in = True
                st.session_state.user_id = response["user_id"]

                st.rerun()

            else:
                st.error(response["message"])

    with tab2:

        email = st.text_input("Email", key="register_email")
        password = st.text_input(
            "Password",
            type="password",
            key="register_password",
        )

        if st.button("Register"):

            response = requests.post(
                f"{API}/register",
                json={
                    "email": email,
                    "password": password,
                },
            ).json()

            if response["success"]:
                st.success("Account created successfully!")
            else:
                st.error(response["message"])

    st.stop()

def render_assistant_message(message):
    confidence = message.get("confidence")
    sources = message.get("sources")
    msg_id = message["message_id"]

    with st.chat_message("assistant"):

        st.markdown(message["content"])

        # Already submitted
        if st.session_state.get(f"feedback_sent_{msg_id}", False):
            st.caption("✅ Feedback submitted")

        else:

            # Save the thumb selection
            if f"rating_{msg_id}" not in st.session_state:

                feedback = st.feedback(
                    "thumbs",
                    key=f"feedback_{msg_id}",
                )

                if feedback is not None:
                    st.session_state[f"rating_{msg_id}"] = (
                        "up" if feedback == 1 else "down"
                    )

            # Optional comment button
            if st.button(
                ":material/forum: Send Feedback",
                key=f"feedback_button_{msg_id}",
            ):
                st.session_state[f"show_feedback_{msg_id}"] = True

            if st.session_state.get(f"show_feedback_{msg_id}", False):

                st.text_area(
                    "Tell us how we can improve:",
                    key=f"comment_{msg_id}",
                    placeholder="The answer was missing details...",
                )

            # Show submit button whenever a rating OR comment form exists
            if (
                f"rating_{msg_id}" in st.session_state
                or st.session_state.get(f"show_feedback_{msg_id}", False)
            ):

                if st.button(
                    "Submit Feedback",
                    key=f"submit_feedback_{msg_id}",
                ):

                    requests.post(
                        f"{API}/feedback",
                        json={
                            "conversation_id": st.session_state.conversation_id,
                            "message_id": msg_id,
                            "rating": st.session_state.get(
                                f"rating_{msg_id}",
                                "comment",
                            ),
                            "comment": st.session_state.get(
                                f"comment_{msg_id}",
                                "",
                            ),
                        },
                    )

                    st.session_state[f"feedback_sent_{msg_id}"] = True
                    st.session_state.pop(f"show_feedback_{msg_id}", None)
                    st.session_state.pop(f"rating_{msg_id}", None)
                    st.session_state.pop(f"comment_{msg_id}", None)

                    st.rerun()

        if confidence is not None:
            with st.expander("Confidence"):
                st.write(f"{confidence:.2f}")

        if sources:
            st.markdown("### 📚 Sources")

            for source in sources:
                st.link_button(
                    label=f"📄 {Path(source['document']).name}",
                    url=source["url"],
                )  

st.set_page_config(
    page_title="AI RAG Assistant",
    page_icon="🤖",
    layout="wide",
)

with st.sidebar:

    st.title("💬 Conversations")

    # New chat button
    if st.button(
        ":material/add: New Chat",
        key="new_chat",
        use_container_width=True,
    ):  
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()

    conversations = requests.get(
        f"{API}/conversations"
    ).json()
    
    for conv in conversations:

        col1, col2 = st.columns([8.5, 1.5])

        with col1:

            if st.button(
                conv.get("title", f"Conversation {conv['id']}"),
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
                ":material/delete:",
                key=f"delete_{conv['id']}",
                type="secondary",
            ):

                requests.delete(
                    f"{API}/conversation/{conv['id']}"
                )

                if st.session_state.conversation_id == conv["id"]:
                    st.session_state.conversation_id = None
                    st.session_state.messages = []

                st.rerun()


st.title("AI RAG Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


# Show previous messages
for message in st.session_state.messages:

    if message["role"] == "assistant":

        render_assistant_message(message)
        confidence = message.get("confidence")
        sources = message.get("sources")
    else:

        with st.chat_message("user"):
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
    with st.spinner("Thinking..."):
        response = requests.post(
            f"{API}/chat",
            json={
                "question": question,
                "conversation_id": st.session_state.conversation_id,
            },
        )
    print(response.status_code)
    print(response.text)
    data = response.json()
    print(data)
    st.session_state.conversation_id = data["conversation_id"]

    answer = data["answer"]

    # save assistant answer
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "message_id": data["assistant_message_id"],
            "sources": data["sources"],
            "confidence": data.get("confidence"),
        }
    )

    st.rerun()