import sqlite3
import datetime

# SQLiteデータベースに接続
conn = sqlite3.connect('schedule.db')
cursor = conn.cursor()

# テーブルのスキーマを表示
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='schedule'")
schema = cursor.fetchone()
print("テーブルスキーマ:")
print(schema[0])
print("\n")

# サンプルデータを表示
cursor.execute("SELECT * FROM schedule LIMIT 10")
rows = cursor.fetchall()
print("サンプルデータ (最初の10件):")
for row in rows:
    print(row)
print("\n")

# 利用可能な学年（grade）を表示
cursor.execute("SELECT DISTINCT grade FROM schedule")
grades = cursor.fetchall()
print("利用可能な学年:")
for grade in grades:
    print(grade[0])
print("\n")

# 日付の範囲を表示
cursor.execute("SELECT MIN(date), MAX(date) FROM schedule")
date_range = cursor.fetchone()
print(f"日付の範囲: {date_range[0]} から {date_range[1]}")
print("\n")

# 月ごとのデータ数を表示
cursor.execute("""
SELECT substr(date, 6, 2) as month, COUNT(*) as count 
FROM schedule 
GROUP BY month 
ORDER BY month
""")
month_counts = cursor.fetchall()
print("月ごとのデータ数:")
for month, count in month_counts:
    print(f"月: {month}, データ数: {count}")

# 接続を閉じる
conn.close()
