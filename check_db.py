import sqlite3
import os

db_path = "SL-Back-end/stock_lab.db"
if not os.path.exists(db_path):
    print(f"DB file not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== DB Tables ===")
for table in tables:
    print(f"- {table[0]}")

# Check theme_sentiments
print("\n=== theme_sentiments Table ===")
try:
    cursor.execute("SELECT COUNT(*) FROM theme_sentiments")
    count = cursor.fetchone()[0]
    print(f"Total records: {count}")

    if count > 0:
        cursor.execute("SELECT theme, avg_sentiment_score, total_count, positive_count, negative_count, calculated_at FROM theme_sentiments LIMIT 5")
        print("\nTop 5 records:")
        for row in cursor.fetchall():
            print(f"  Theme: {row[0]}, Score: {row[1]}, Total: {row[2]}, Pos: {row[3]}, Neg: {row[4]}, Updated: {row[5]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
