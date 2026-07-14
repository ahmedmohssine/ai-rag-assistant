import sqlite3
import json
import bcrypt

DATABASE = "data/chat_history.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()

    try:
        conn.execute("""
        ALTER TABLE messages
        ADD COLUMN sources TEXT
        """)
    except sqlite3.OperationalError:
        pass

    conn.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT 'New Conversation',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,
        content TEXT,
        confidence REAL,
        sources TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        message_id INTEGER,
        rating TEXT,
        comment TEXT,
        sources TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    try:
        conn.execute("""
        ALTER TABLE conversations
        ADD COLUMN user_id INTEGER
        """)
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def create_conversation(title: str = "New Conversation",user_id: int = None):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations(title, user_id)
        VALUES(?,?)
         """,
        (title,user_id),
    )

    conn.commit()

    conversation_id = cursor.lastrowid

    conn.close()

    return conversation_id


def add_message(
    conversation_id,
    role,
    content,
    confidence=0,
    sources=None,
):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages(
            conversation_id,
            role,
            content,
            confidence,
            sources
        )
        VALUES(?,?,?,?,?)
        """,
        (
            conversation_id,
            role,
            content,
            confidence,
            json.dumps(sources or []),
        ),
    )

    conn.commit()

    message_id = cursor.lastrowid

    conn.close()

    return message_id

def get_history(conversation_id: int):
    print(">>> get_history() called")
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT role, content, confidence, created_at, sources
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
        """,
        (conversation_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_conversations(user_id: int):
    conn = get_connection()

    rows = conn.execute("""
        SELECT id, title
        FROM conversations
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
        ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_messages(conversation_id: int, user_id: int):
    print(">>> get_messages() called")
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            m.id,
            m.role,
            m.content,
            m.confidence,
            m.sources
        FROM messages m
        JOIN conversations c
            ON m.conversation_id = c.id
        WHERE
            m.conversation_id = ?
            AND c.user_id = ?
        ORDER BY m.id
    """, (conversation_id, user_id)).fetchall()
    
    conn.close()

    return [
        {
            "message_id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "confidence": row["confidence"],
            "sources": json.loads(row["sources"] or "[]"),
        }
        for row in rows
    ]


def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Safely deletes a conversation only if it belongs to the requesting user."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verify ownership before executing the delete sequence
    cursor.execute(
        "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    )
    if cursor.fetchone() is None:
        conn.close()
        return False  # Ownership verification failed

    # 2. Proceed with cascade deletion now that it's safe
    cursor.execute(
        "DELETE FROM messages WHERE conversation_id = ?",
        (conversation_id,),
    )
    cursor.execute(
        "DELETE FROM conversations WHERE id = ?",
        (conversation_id,),
    )

    conn.commit()
    conn.close()
    return True


def verify_conversation_owner(conversation_id: int, user_id: int) -> bool:
    """Helper function to verify if a conversation belongs to a specific user."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    ).fetchone()
    conn.close()
    return row is not None



def add_feedback(
    conversation_id: int,
    message_id: int,
    rating: str,
    comment: str = "",
    sources: str = None,
):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO feedback(
            conversation_id,
            message_id,
            rating,
            comment,
            sources
        )
        VALUES(?, ?, ?, ?, ?)
        """,
        (
            conversation_id,
            message_id,
            rating,
            comment,
            sources,
        ),
    )

    conn.commit()
    conn.close()


def create_user(email: str, password: str):
    conn = get_connection()

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(),
    ).decode()

    try:
        conn.execute(
            """
            INSERT INTO users(email, password_hash)
            VALUES(?, ?)
            """,
            (email, password_hash),
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return False

    conn.close()
    return True

def verify_user(email: str, password: str):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT id, password_hash
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    if bcrypt.checkpw(
        password.encode(),
        row["password_hash"].encode(),
    ):
        return row["id"]

    return None


def delete_user(user_id: int):
    conn = get_connection()

    conn.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


