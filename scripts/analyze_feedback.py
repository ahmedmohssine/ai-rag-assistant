import sqlite3

DATABASE = "data/chat_history.db"

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
SELECT rating, comment
FROM feedback
ORDER BY created_at
""").fetchall()

conn.close()

likes = 0
dislikes = 0

positive_comments = []
negative_comments = []

for row in rows:
    rating = row["rating"]
    comment = (row["comment"] or "").strip()

    if rating == "up":
        likes += 1
        if comment:
            positive_comments.append(comment)
    elif rating == "down":
        dislikes += 1
        if comment:
            negative_comments.append(comment)


feed_back = [
    f"""
    {"=" * 50}
    Feedback Report
    {"=" * 50}

    Likes:    {likes}
    Dislikes: {dislikes}

    {"=" * 50}
    Positive Comments
    {"=" * 50}"""
]

if positive_comments:
    for i, comment in enumerate(positive_comments, 1):
        feed_back.append(f"     {i}. {comment}")
else:
    feed_back.append("\n     No positive comments.")

feed_back.append(f"""
    {"=" * 50}  
    Negative Comments
    {"=" * 50} 
""")

if negative_comments:
    for i, comment in enumerate(negative_comments, 1):
        feed_back.append(f"     {i}. {comment}")
else:
    feed_back.append("     No negative comments.")


final_report = "\n".join(feed_back)
print(final_report)

with open(
        "data/feedback_report.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(final_report)