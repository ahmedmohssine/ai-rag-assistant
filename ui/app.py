import requests
import streamlit as st
from pathlib import Path
import json


st.set_page_config(
    page_title="AI RAG Assistant",
    page_icon=":material/smart_toy:",
    layout="wide",
)

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

# Advanced Browser Sync Helpers via URL Query Parameters
def sync_browser_to_url():
    """If Python doesn't know who is logged in, use JS to read localStorage and put it in the URL."""
    js_code = """
    <script>
        const token = localStorage.getItem('rag_auth_token');
        const userId = localStorage.getItem('rag_user_id');
        const urlParams = new URLSearchParams(window.location.search);
        
        // If localStorage has data but the URL doesn't, inject them into the URL and reload
        if (token && userId && !urlParams.has('token')) {
            urlParams.set('token', token);
            urlParams.set('user_id', userId);
            window.location.search = urlParams.toString();
        }
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

def save_browser_session(token, user_id):
    """Saves session info into permanent browser storage."""
    js_code = f"""
    <script>
        localStorage.setItem('rag_auth_token', '{token}');
        localStorage.setItem('rag_user_id', '{user_id}');
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

def clear_browser_session():
    """Deletes session info from browser storage on logout."""
    js_code = """
    <script>
        localStorage.removeItem('rag_auth_token');
        localStorage.removeItem('rag_user_id');
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)


# Check URL params on refresh BEFORE rendering the login page
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# If the URL contains the session parameters, auto-login the Python state!
if not st.session_state.logged_in and "token" in st.query_params and "user_id" in st.query_params:
    st.session_state.logged_in = True
    st.session_state.user_id = int(st.query_params["user_id"])

# If Python still doesn't know, trigger the JS scanner to check browser memory
if not st.session_state.logged_in:
    sync_browser_to_url()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


# --- LOGIN / REGISTER OVERLAY ---
if not st.session_state.logged_in:
    st.title(":material/account_box: Login")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            response = requests.post(
                f"{API}/login",
                json={"email": email, "password": password},
            ).json()

            if response["success"]:
                st.session_state.logged_in = True
                st.session_state.user_id = response["user_id"]
                
                # Push into permanent browser memory
                save_browser_session(response["token"], str(response["user_id"]))
                
                # Update the URL bar immediately so it stays persistent on next refresh
                st.query_params["token"] = response["token"]
                st.query_params["user_id"] = str(response["user_id"])
                
                st.rerun()
            else:
                st.error(response["message"])

    with tab2:
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")

        if st.button("Register"):
            response = requests.post(
                f"{API}/register",
                json={"email": email, "password": password},
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

        if st.session_state.get(f"feedback_sent_{msg_id}", False):
            st.caption(":material/check: Feedback submitted")
        else:
            if f"rating_{msg_id}" not in st.session_state:
                feedback = st.feedback("thumbs", key=f"feedback_{msg_id}")
                if feedback is not None:
                    st.session_state[f"rating_{msg_id}"] = "up" if feedback == 1 else "down"

            if st.button(":material/add_comment: Send Feedback", key=f"feedback_button_{msg_id}"):
                st.session_state[f"show_feedback_{msg_id}"] = True

            if st.session_state.get(f"show_feedback_{msg_id}", False):
                st.text_area(
                    "Tell us how we can improve:",
                    key=f"comment_{msg_id}",
                    placeholder="The answer was missing details...",
                )

            if f"rating_{msg_id}" in st.session_state or st.session_state.get(f"show_feedback_{msg_id}", False):
                if st.button(
                    "Submit Feedback",
                    key=f"submit_feedback_{msg_id}",
                ):
                    
                    requests.post(
                        f"{API}/feedback",
                        json={
                            "conversation_id": st.session_state.conversation_id,
                            "user_id": st.session_state.user_id,
                            "message_id": msg_id,
                            "rating": st.session_state.get(f"rating_{msg_id}", "comment"),
                            "comment": st.session_state.get(f"comment_{msg_id}", ""),
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
            st.markdown("### :material/Link_2: Sources")
            for source in sources:
                st.link_button(
                    label=f":material/docs: {Path(source['document']).name}",
                    url=source["url"],
                )  


# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.title(":material/chat_bubble: Conversations")

    if st.button(":material/add: New Chat", key="new_chat", use_container_width=True):  
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --- RETRIEVAL CONFIGURATION PANEL ---
    st.subheader(":material/settings: Retrieval Controls")
    
    # Configurable Top-K Slider
    top_k_val = st.slider(
        "Context Count (Top-K)", 
        min_value=1, 
        max_value=10, 
        value=5, 
        help="Number of document chunks to retrieve for context."
    )
    
    # Document Source Metadata Filter
    source_filter_val = st.text_input(
        "Filter by Document/Path", 
        value="", 
        placeholder="e.g., fastapi/tutorial",
        help="Leave empty to search all ingested documentation files."
    )
    
    st.divider()



    response = requests.get(f"{API}/conversations", params={"user_id": st.session_state.user_id})
    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    conversations = response.json()
    
    for conv in conversations:
        col1, col2 = st.columns([8.5, 1.5])
        with col1:
            if st.button(
                conv.get("title", f"Conversation {conv['id']}"),
                key=f"open_{conv['id']}",
                use_container_width=True,
            ):
                st.session_state.conversation_id = conv["id"]

                # FIXED: Added type-validation safety checks to prevent dict-to-string loops
                history_response = requests.get(
                    f"{API}/history/{conv['id']}",
                    params={"user_id": st.session_state.user_id}
                )
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    st.session_state.messages = history_data if isinstance(history_data, list) else []
                else:
                    st.error(f"Failed to load chat history: {history_response.text}")
                    st.session_state.messages = []
                
                st.rerun()

        with col2:
            if st.button(
                ":material/delete:",
                key=f"delete_{conv['id']}",
                type="secondary",
            ):
                requests.delete(
                    f"{API}/conversation/{conv['id']}",
                    params={"user_id": st.session_state.user_id}
                )

                if st.session_state.conversation_id == conv["id"]:
                    st.session_state.conversation_id = None
                    st.session_state.messages = []

                st.rerun()

    st.divider()
    st.subheader(":material/person: Account")

    if st.button("Logout", use_container_width=True):
        clear_browser_session()
        st.query_params.clear()
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()
    
    if st.button("Delete Account", type="secondary", use_container_width=True):
        st.session_state.show_delete_account = True

    if st.session_state.get("show_delete_account", False):
        st.warning(":material/warning: This will permanently delete your account.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", type="primary", use_container_width=True):
                requests.delete(f"{API}/user/{st.session_state.user_id}")
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.conversation_id = None
                st.session_state.messages = []
                st.session_state.show_delete_account = False
                st.rerun()


# --- MAIN CHAT INTERFACE ---
# Render historical messages safely (only loops if it's confirmed to be a clean list)
if isinstance(st.session_state.get("messages"), list):
    for msg in st.session_state.messages:
        if isinstance(msg, dict) and "role" in msg:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            elif msg["role"] == "assistant":
                render_assistant_message(msg)

# Handle new user messaging input
if prompt := st.chat_input("Ask something about the documentation..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    payload = {
        "question": prompt,
        "user_id": st.session_state.user_id,
        "conversation_id": st.session_state.conversation_id,
        "top_k": top_k_val,
        "source_filter": source_filter_val if source_filter_val.strip() else None,
    }
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(f"{API}/chat", json=payload, stream=True)
            stream_iterator = response.iter_content(chunk_size=None, decode_unicode=True)
            first_chunk = next(stream_iterator, None)

        def chunk_generator():
            # FIXED: Safely parse JSON metadata immediately if it drops inside the first_chunk
            if first_chunk:
                if "__METADATA__:" in first_chunk:
                    parts = first_chunk.split("__METADATA__:")
                    yield parts[0]
                    try:
                        st.session_state["last_stream_metadata"] = json.loads(parts[1].strip())
                    except Exception:
                        st.session_state["last_stream_metadata"] = {}
                    return
                yield first_chunk

            metadata_str = ""
            for chunk in stream_iterator:
                if chunk:
                    if "__METADATA__:" in chunk:
                        parts = chunk.split("__METADATA__:")
                        yield parts[0]
                        metadata_str = parts[1]
                        break
                    yield chunk
            
            if metadata_str:
                try:
                    st.session_state["last_stream_metadata"] = json.loads(metadata_str.strip())
                except Exception:
                    pass

        st.write_stream(chunk_generator())

    meta = st.session_state.pop("last_stream_metadata", {})
    if isinstance(meta, dict):
        if st.session_state.conversation_id is None:
            st.session_state.conversation_id = meta.get("conversation_id")
            
    # FIXED: Check the backend response code before assigning history lists
    history_response = requests.get(
        f"{API}/history/{st.session_state.conversation_id}",
        params={"user_id": st.session_state.user_id}
    )
    
    if history_response.status_code == 200:
        history_data = history_response.json()
        st.session_state.messages = history_data if isinstance(history_data, list) else []
    else:
        st.error(f"Error synchronization layout mismatch: {history_response.text}")
        st.session_state.messages = []
    
    st.rerun()


