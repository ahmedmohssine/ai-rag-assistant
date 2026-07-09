import sqlite3

DATABASE = "data/chat_history.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def create_conversation():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO conversations DEFAULT VALUES"
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
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO messages(
            conversation_id,
            role,
            content,
            confidence
        )
        VALUES(?,?,?,?)
        """,
        (
            conversation_id,
            role,
            content,
            confidence,
        ),
    )

    conn.commit()

    conn.close()


def get_history(conversation_id: int):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT role, content, confidence, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
        """,
        (conversation_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_conversations():
    conn = get_connection()

    rows = conn.execute("""
        SELECT id
        FROM conversations
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_messages(conversation_id: int):
    conn = get_connection()

    rows = conn.execute("""
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
    """, (conversation_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]

def delete_conversation(conversation_id: int):
    conn = get_connection()

    conn.execute(
        "DELETE FROM messages WHERE conversation_id = ?",
        (conversation_id,),
    )

    conn.execute(
        "DELETE FROM conversations WHERE id = ?",
        (conversation_id,),
    )

    conn.commit()
    conn.close()