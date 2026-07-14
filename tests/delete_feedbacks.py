import sqlite3

DATABASE = "data/chat_history.db"

conn = sqlite3.connect(DATABASE)

conn.execute("DELETE FROM feedback")
conn.execute("DELETE FROM sqlite_sequence WHERE name='feedback'")

conn.commit()
conn.close()

print("Feedback table has been cleared and IDs reset.")