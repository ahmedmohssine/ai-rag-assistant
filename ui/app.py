import requests
import os
import streamlit as st
from pathlib import Path
import json


st.set_page_config(
    page_title="AI RAG Assistant",
    page_icon=":material/smart_toy:",
    layout="wide",
)

API = os.getenv("API_URL", "http://localhost:8000")


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
        const userEmail = localStorage.getItem('rag_user_email');
        const urlParams = new URLSearchParams(window.location.search);
        
        // FIXED: If browser memory has data, but the URL is missing ANY of the parameters,
        // inject them all into the address bar and reload the workspace cleanly.
        if (token && userId && userEmail && (!urlParams.has('token') || !urlParams.has('user_id') || !urlParams.has('email'))) {
            urlParams.set('token', token);
            urlParams.set('user_id', userId);
            urlParams.set('email', userEmail);
            window.location.search = urlParams.toString();
        }
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

def save_browser_session(token, user_id, email):
    """Saves session info into permanent browser storage."""
    js_code = f"""
    <script>
        localStorage.setItem('rag_auth_token', '{token}');
        localStorage.setItem('rag_user_id', '{user_id}');
        localStorage.setItem('rag_user_email', '{email}'); // NEW
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

def clear_browser_session():
    """Deletes session info from browser storage on logout."""
    js_code = """
    <script>
        localStorage.removeItem('rag_auth_token');
        localStorage.removeItem('rag_user_id');
        localStorage.removeItem('rag_user_email'); // NEW
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)



# Check URL params on refresh BEFORE rendering the login page
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if not st.session_state.logged_in and "token" in st.query_params and "user_id" in st.query_params and "email" in st.query_params:
    st.session_state.logged_in = True
    st.session_state.user_id = int(st.query_params["user_id"])
    st.session_state.user_email = str(st.query_params["email"]).strip().lower()

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

        if st.button("Login", key="main_login_submit_btn"):
            response = requests.post(
                f"{API}/login",
                json={"email": email, "password": password},
            ).json()

            if response["success"]:
                st.session_state.logged_in = True
                st.session_state.user_id = response["user_id"]
                st.session_state.user_email = email.strip().lower()
                # Push into permanent browser memory
                save_browser_session(response["token"], str(response["user_id"]), email.strip().lower())

                # Update the URL bar immediately so it stays persistent on next refresh
                st.query_params["token"] = response["token"]
                st.query_params["user_id"] = str(response["user_id"])
                st.query_params["email"] = email.strip().lower()
                
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
            st.markdown("### :material/Link: Sources")
            for source in sources:
                url = source["url"]
                if url.startswith("http"):
                    st.link_button(
                        f":material/docs: {Path(source['document']).name}",
                        url=url,
                    )
                else:
                    st.caption(f":material/Link_2: {url}")

# --- SIDEBAR COMPONENT ---
with st.sidebar:

    # --- NON-PROFESSIONAL DOCUMENT MANAGER PANEL ---
    with st.expander(":material/folder_open: Knowledge Base Manager", expanded=False):
        st.markdown("<small>Drag & drop files or an entire folder here to rebuild the database.</small>", unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose a document", 
            type=["md", "txt", "pdf", "json"],
            accept_multiple_files=True,
            key="knowledge_base_uploader"
        )
        
        if uploaded_files:
            if st.button("Wipe & Re-index Database", type="primary", use_container_width=True):
                
                # Initialize placeholders for the progress indicators
                status_text = st.empty()
                progress_bar = st.progress(0)
                
                try:
                    # Package multiple file buffers into a list format matching multi-form requirements
                    multipart_form_data = [
                        ("files", (file.name, file.getvalue(), file.type)) 
                        for file in uploaded_files
                    ]
                    
                    with requests.post(f"{API}/admin/upload", files=multipart_form_data, stream=True) as response:
                        for line in response.iter_lines(decode_unicode=True):
                            if line:
                                if line.startswith("PROGRESS:"):
                                    payload = line.replace("PROGRESS:", "")
                                    percentage_str, message = payload.split("|", 1)
                                    progress_bar.progress(int(percentage_str))
                                    status_text.caption(f":material/sync: {message}")
                                elif line.startswith("SUCCESS:"):
                                    msg = line.replace("SUCCESS:", "")
                                    status_text.success(msg)
                                    progress_bar.empty()
                                elif line.startswith("ERROR:"):
                                    msg = line.replace("ERROR:", "")
                                    status_text.error(msg)
                                    progress_bar.empty()
                except Exception as e:
                    status_text.error(f"Network processing drop: {str(e)}")
                    progress_bar.empty()
                                    
                except Exception as e:
                    status_text.error(f"Network processing drop: {str(e)}")
                    progress_bar.empty()

     # --- RETRIEVAL CONFIGURATION PANEL ---
    with st.expander(":material/settings: Retrieval Controls", expanded=False):
    
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

    st.title(":material/chat_bubble: Conversations")

    if st.button(":material/add: New Chat", key="new_chat", use_container_width=True):  
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    response = requests.get(f"{API}/conversations", params={"user_id": st.session_state.user_id})
    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    conversations = response.json() 

    chat_list_container = st.container(height=300, border=False)

    with chat_list_container:
        for conv in conversations:
            col1, col2 = st.columns([8.5, 1.5])
            with col1:
                if st.button(
                    conv.get("title", f"Conversation {conv['id']}"),
                    key=f"open_{conv['id']}",
                    use_container_width=True,
                ):
                    st.session_state.conversation_id = conv["id"]

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

    st.markdown("<div style='position: relative; bottom: 0; width: 100%;'>", unsafe_allow_html=True)
    st.divider()
    st.subheader(":material/person: Account")

    if st.session_state.get("user_email") == "admin@gmail.com":
        if st.checkbox(":material/dashboard: Open Feedback Dashboard", key="admin_dashboard_toggle_checkbox"):
            st.session_state.viewing_admin = True
        else:
            st.session_state.viewing_admin = False
        
        if st.button(":material/analytics: Print Evaluation", use_container_width=True):

            with st.spinner("Running evaluation..."):

                response = requests.post(
                    f"{API}/admin/eval",
                    params={
                        "email": st.session_state.user_email
                    }
                )

                if response.status_code == 200:
                    st.session_state.eval_results = response.json()
                else:
                    st.error(response.text)
        if "eval_results" in st.session_state:

            report = st.session_state.eval_results
            metrics = report["metrics"]
            st.header("Evaluation Results")

            # ---------------- Retrieval ----------------

            st.subheader("Retrieval")

            r1, r2, r3, r4 = st.columns(4)

            r1.metric("Recall@1", f"{metrics['document_recall@1']:.1%}")
            r2.metric("Recall@3", f"{metrics['document_recall@3']:.1%}")
            r3.metric("Recall@5", f"{metrics['document_recall@5']:.1%}")
            r4.metric("MRR", f"{metrics['document_mrr']:.3f}")

            st.divider()

            # ---------------- LLM Judge ----------------

            st.subheader("LLM Judge")

            j1, j2, j3, j4 = st.columns(4)

            j1.metric("Faithfulness", f"{metrics['faithfulness']:.2f}/5")
            j2.metric("Correctness", f"{metrics['correctness']:.2f}/5")
            j3.metric("Relevance", f"{metrics['relevance']:.2f}/5")
            j4.metric("Hallucination", f"{metrics['hallucination_rate']:.1%}")

            st.divider()

            # ---------------- Timing ----------------

            t1, t2 = st.columns(2)

            t1.metric(
                "Average Retrieval Time",
                f"{metrics['average_retrieval_time']:.3f}s"
            )

            t2.metric(
                "Average Generation Time",
                f"{metrics['average_generation_time']:.3f}s"
            )
    else:
        st.session_state.viewing_admin = False

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
    st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN CHAT INTERFACE ---
if st.session_state.get("viewing_admin", False):
# --- MAIN WORKSPACE ROUTING LAYOUT ---
    if st.session_state.get("viewing_admin", False):
        st.title(":material/analytics: User Feedback & Quality Dashboard")
        st.markdown("Review system alignment, track low-quality generation reports, and read user comments.")
        
        feedback_res = requests.get(f"{API}/admin/feedback", params={"email": st.session_state.user_email})
    
    if feedback_res.status_code == 200:
        reports = feedback_res.json()
        
        if not reports:
            st.info("No feedback metrics have been logged by active users yet.")
        else:
            # Compute baseline metrics summaries
            likes = sum(1 for r in reports if r["rating"] == "up")
            dislikes = sum(1 for r in reports if r["rating"] == "down")
            total = len(reports)
            ratio = (likes / total) if total else 0
            
            # Render a summary layout
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Submissions", total)
            m2.metric("Thumbs Up (Likes)", likes)
            m3.metric("Approval Rating Ratio", f"{ratio:.1%}")
            
            st.divider()
            
            # Loop through and draw cards for every logged element
            for item in reports:
                # Assign icodns based on value strings
                rating_icon = ":material/thumb_up:" if item["rating"] == "up" else ":material/thumb_down:"
                card_color = "🟢" if item["rating"] == "up" else "🔴"
                
                with st.expander(f"{card_color} Feedback #{item['feedback_id']} - Chat ID: {item['conversation_id']} ({item['created_at']})"):
                    st.markdown(f"**User Question:**\n>{item.get('user_question') or '*No leading text prompt extracted*'}")
                    st.markdown(f"**Assistant Generation:**\n{item['assistant_answer']}")
                    
                    if item.get("comment"):
                        st.warning(f"**User Written Comments:**\n{item['comment']}")
    else:
        st.error(f"Failed to fetch administrative reports: {feedback_res.text}")
    
    st.stop() # Prevents default chat strings loop layout from drawing underneath

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


