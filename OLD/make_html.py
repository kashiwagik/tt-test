import locale
import sqlite3
import calendar
import datetime
import os
from collections import defaultdict

def get_schedule_data(grade, month):
    """
    指定された学年と月のスケジュールデータを取得する
    
    Args:
        grade (str): 学年 ('1年生', '2年生', '3年生', '4年生', '4年生助産')
        month (int): 月 (1-12)
    
    Returns:
        dict: 日付とperiodをキーとし、courses, roomを値とする辞書
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # 指定された学年と月のデータを取得
    month_str = f"{month:02d}"  # 月を2桁の文字列に変換 (例: 4 -> "04")
    year = 2025  # parse1.pyから取得した年
    
    # 月の最初と最後の日を取得
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month_str}-01"
    end_date = f"{year}-{month_str}-{last_day}"
    
    # データを取得するクエリ
    query = """
    SELECT date, period, courses, room
    FROM schedule
    WHERE grade = ? AND date BETWEEN ? AND ?
    ORDER BY date, period
    """
    
    cursor.execute(query, (grade, start_date, end_date))
    rows = cursor.fetchall()
    
    # データ構造を作成
    schedule_data = defaultdict(dict)
    for date, period, courses, room in rows:
        # 日付をキー、periodをサブキーとする辞書を作成
        schedule_data[date][period] = {
            'courses': courses,
            'room': room
        }
    
    # 接続を閉じる
    conn.close()
    
    return schedule_data

def generate_html(grade, month, schedule_data):
    """
    スケジュールデータからHTMLを生成する
    
    Args:
        grade (str): 学年
        month (int): 月
        schedule_data (dict): スケジュールデータ
    
    Returns:
        str: 生成されたHTML
    """
    year = 2025  # parse1.pyから取得した年
    month_name = calendar.month_name[month]
    
    # CSSスタイルを定義
    css = """
    .biz-udpgothic-regular {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 400;
        font-style: normal;
        }

    .biz-udpgothic-bold {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 700;
        font-style: normal;
    }

    body {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 400;
        font-style: normal;
        font-size: 0.8em;
        /* font-family: 'Helvetica Neue', Arial, sans-serif; */
        margin: 20px;
        color: #333;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        margin-bottom: 20px;
    }
    .timetable {
        display: flex;
        flex-direction: column;
        width: 100%;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #ddd;
    }
    .header {
        display: flex;
        background-color: #3498db;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .header-item {
        padding: 10px;
        border-right: 1px solid #ddd;
    }
    .header-date {
        flex: 0 0 40px;
    }
    .header-day {
        flex: 0 0 30px;
    }
    .header-period {
        flex: 1;
        display: flex;
                border-bottom: 1px solid #ddd;

    }
    .header-period-title {
        flex: 0 0 calc(20% - 21px);
        max-width: calc(20% - 21px);
        padding: 10px;
        border-right: 1px solid #ddd;
    }
    .subheader {
        display: flex;
        background-color: #3498db;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .subheader-item {
        padding: 10px;
        border-right: 1px solid #ddd;
    }
    .subheader-empty {
        flex: 0 0 40px;
    }
    .subheader-empty2 {
        flex: 0 0 30px;
    }
    .subheader-course {
        flex: 0 0 calc(14% - 21px); /* 固定幅 */
        max-width: calc(14% - 21px);
        padding: 10px;
        border-right: 1px solid #ddd;
    }
    .subheader-room {
        flex: 0 0 calc(6% - 21px); /* 固定幅 */
        max-width: calc(6% - 21px);
        font-size: 0.8em;
        padding: 10px;
        border-right: 1px solid #ddd;
    }
    .row {
        display: flex;
        border-bottom: 1px solid #ddd;
    }
    .row:hover {
        background-color: #f5f5f5;
    }
    .date-cell {
        flex: 0 0 40px;
        padding: 10px;
        font-weight: bold;
        text-align: center;
        border-right: 1px solid #ddd;
    }
    .day-cell {
        flex: 0 0 30px;
        padding: 10px;
        text-align: center;
        border-right: 1px solid #ddd;
    }
    .period-container {
        flex: 1;
        display: flex;
    }
    .course {
        flex: 0 0 calc(14% -13px); /* 固定幅 */
        max-width: calc(14% - 13px);
        min-width: calc(14% - 13px);
        padding: 6px;
        text-align: left;
        border-right: 1px solid #ddd;
        overflow: hidden;
        word-wrap: break-word;
        word-break: break-all;
        line-height: 1.2;
        white-space: normal;
    }
    .room {
        flex: 0 0 calc(6% - 13px); /* 固定幅 */
        max-width: calc(6% - 13px);
        padding: 6px;
        text-align: center;
        font-size: 0.8em;
        border-right: 1px solid #ddd;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .empty-course {
        flex: 0 0 calc(14% - 21px); /* 固定幅 */
        max-width: calc(14% - 21px);
        padding: 10px;
        background-color: #fafafa;
        border-right: 1px solid #ddd;
    }
    .empty-room {
        flex: 0 0 calc(6% - 21px); /* 固定幅 */
        max-width: calc(6% - 21px);
        padding: 10px;
        background-color: #fafafa;
        border-right: 1px solid #ddd;
    }
    .saturday {
        background-color: #e3f2fd; /* 薄い青 */
    }
    .sunday {
        background-color: #ffebee; /* 薄い赤 */
    }
    """
    
    # HTMLのヘッダー部分
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{grade} {year}年{month}月 時間割</title>
    <style>
{css}
    </style>
</head>
<body>
    <h1>{grade} {year}年{month}月 時間割</h1>
    <div class="timetable">
        <div class="header">
            <div class="header-item header-date">日</div>
            <div class="header-item header-day">曜</div>
            <div class="header-period">
                <div class="header-period-title">1限</div>
                <div class="header-period-title">2限</div>
                <div class="header-period-title">3限</div>
                <div class="header-period-title">4限</div>
                <div class="header-period-title">5限</div>
            </div>
        </div>
        <div class="subheader">
            <div class="subheader-item subheader-empty">付</div>
            <div class="subheader-item subheader-empty2">日</div>
            <div class="header-period">
                <div class="subheader-item subheader-course">科目</div>
                <div class="subheader-item subheader-room">教室</div>
                <div class="subheader-item subheader-course">科目</div>
                <div class="subheader-item subheader-room">教室</div>
                <div class="subheader-item subheader-course">科目</div>
                <div class="subheader-item subheader-room">教室</div>
                <div class="subheader-item subheader-course">科目</div>
                <div class="subheader-item subheader-room">教室</div>
                <div class="subheader-item subheader-course">科目</div>
                <div class="subheader-item subheader-room">教室</div>
            </div>
        </div>
"""
    
    # 月の最初と最後の日を取得
    _, last_day = calendar.monthrange(year, month)
    
    # 各日のデータを追加
    for day in range(1, last_day + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')

        weekday = date_obj.strftime("%a")  # 曜日の略称 (月、火, etc.)
        
        # 日付の表示形式
        display_date = f"{month}/{day}"
        
        # 土曜日と日曜日の行に特別なクラスを追加
        row_class = "row"
        if weekday == "土":
            row_class += " saturday"
        elif weekday == "日":
            row_class += " sunday"
        
        html += f"        <div class=\"{row_class}\">\n"
        html += f"            <div class=\"date-cell\">{display_date}</div>\n"
        html += f"            <div class=\"day-cell\">{weekday}</div>\n"
        html += f"            <div class=\"header-period\">\n"

        
        # 各時限のデータを追加
        for period in range(1, 6):
            if date_str in schedule_data and period in schedule_data[date_str]:
                course_data = schedule_data[date_str][period]
                courses = course_data['courses']
                room = course_data['room'] if course_data['room'] else ""
                
                # コースと教室の情報を別々のdivに表示
                html += f"            <div class=\"course\">{courses}</div>\n"
                html += f"            <div class=\"room\">{room}</div>\n"
            else:
                # データがない場合は空divを表示（科目と教室の2つのdiv）
                html += f"            <div class=\"empty-course\"></div>\n"
                html += f"            <div class=\"empty-room\"></div>\n"

        html += f"            </div>\n"
        html += f"        </div>\n"
    
    # HTMLのフッター部分
    html += """    </div>
</body>
</html>
"""
    
    return html

def save_html(html, grade, month):
    """
    生成されたHTMLをファイルに保存する
    
    Args:
        html (str): 生成されたHTML
        grade (str): 学年
        month (int): 月
    
    Returns:
        str: 保存されたファイルのパス
    """
    # ファイル名を作成
    grade_simplified = grade.replace('年生', '').replace('助産', '_josan')
    filename = f"schedule_{grade_simplified}_{month:02d}.html"
    
    # HTMLをファイルに書き込む
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename

def main():
    """
    メイン関数
    """
    # 利用可能な学年のリスト
    available_grades = ['1年生', '2年生', '3年生', '4年生', '4年生助産']
    
    # コマンドライン引数を解析する代わりに、ユーザー入力を受け付ける
    print("利用可能な学年:")
    for i, grade in enumerate(available_grades, 1):
        print(f"{i}. {grade}")
    
    grade_idx = int(input("学年を選択してください (1-5): ")) - 1
    if grade_idx < 0 or grade_idx >= len(available_grades):
        print("無効な選択です。")
        return
    
    grade = available_grades[grade_idx]
    
    # 月の入力を受け付ける
    month = int(input("月を入力してください (4-9): "))
    if month < 4 or month > 9:
        print("無効な月です。データは4月から9月までのみ利用可能です。")
        return
    
    # スケジュールデータを取得
    schedule_data = get_schedule_data(grade, month)
    
    # HTMLを生成
    html = generate_html(grade, month, schedule_data)
    
    # HTMLをファイルに保存
    filename = save_html(html, grade, month)
    
    print(f"HTMLファイルが生成されました: {filename}")

if __name__ == "__main__":
    main()
