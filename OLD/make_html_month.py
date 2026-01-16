import locale
import sqlite3
import calendar
import datetime
import os
import sys

def get_schedule_data_for_month(year, month):
    """
    指定された年月の全学年のスケジュールデータを取得する
    
    Args:
        year (int): 年
        month (int): 月 (1-12)
    
    Returns:
        dict: 日付をキー、学年と時限をサブキーとするデータ辞書
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # 利用可能な学年を取得
    cursor.execute("SELECT DISTINCT grade FROM schedule")
    grades = [grade[0] for grade in cursor.fetchall()]
    
    # 月の最初と最後の日を取得
    _, last_day = calendar.monthrange(year, month)
    month_str = f"{month:02d}"
    start_date = f"{year}-{month_str}-01"
    end_date = f"{year}-{month_str}-{last_day}"
    
    # 指定された月の全学年のデータを取得
    query = """
    SELECT date, grade, period, courses, room, comment
    FROM schedule
    WHERE date BETWEEN ? AND ?
    ORDER BY date, grade, period
    """
    
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    
    # データ構造を作成
    schedule_data = {}
    
    # 月の各日付に対してデータ構造を初期化
    for day in range(1, last_day + 1):
        date_str = f"{year}-{month_str}-{day:02d}"
        schedule_data[date_str] = {}
        for grade in grades:
            schedule_data[date_str][grade] = {}
    
    # データを格納
    for date, grade, period, courses, room, comment in rows:
        if period == 0:  # コメント行の場合
            if 'comments' not in schedule_data[date][grade]:
                schedule_data[date][grade]['comments'] = []
            schedule_data[date][grade]['comments'].append(comment)
        else:
            schedule_data[date][grade][period] = {
                'courses': courses,
                'room': room
            }
    
    # 接続を閉じる
    conn.close()
    
    return schedule_data, grades

def generate_html_for_day(date_str, day_data, grades):
    """
    特定の日のスケジュールデータからHTMLを生成する
    
    Args:
        date_str (str): 日付 ('YYYY-MM-DD'形式)
        day_data (dict): その日のスケジュールデータ
        grades (list): 学年のリスト
    
    Returns:
        str: 生成されたHTML
    """
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day
    
    # 曜日を取得
    locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
    weekday = date_obj.strftime("%a")  # 曜日の略称 (月、火, etc.)
    
    # 日付の表示形式
    display_date = f"{month}/{day}({weekday})"
    
    # CSSスタイルを定義
    css = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
        color: #333;
        background-color: #f5f5f5;
        font-size: 16px;
    }
    
    .container {
        max-width: 100%;
        margin: 0 auto;
        padding: 10px;
    }
    
    h1 {
        color: #2c3e50;
        text-align: center;
        margin: 10px 0;
        font-size: 1.5em;
    }
    
    .grade-nav {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        margin: 10px 0;
        position: sticky;
        top: 0;
        background-color: #f5f5f5;
        padding: 10px 0;
        z-index: 100;
    }
    
    .grade-nav a {
        display: inline-block;
        padding: 8px 12px;
        margin: 0 5px 5px 0;
        background-color: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
    
    .grade-nav a.active {
        background-color: #2980b9;
    }
    
    .timetable {
        display: flex;
        flex-direction: column;
        width: 100%;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #ddd;
        border-radius: 5px;
        overflow: hidden;
        background-color: white;
        margin-bottom: 20px;
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
    
    .header-period {
        flex: 0 0 20%;
        text-align: center;
    }
    
    .row {
        display: flex;
        border-bottom: 1px solid #ddd;
    }
    
    .row:last-child {
        border-bottom: none;
    }
    
    .period-cell {
        flex: 0 0 20%;
        padding: 10px;
        font-weight: bold;
        text-align: center;
        border-right: 1px solid #ddd;
        background-color: #f2f2f2;
    }
    
    .course-container {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    
    .course {
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid #eee;
    }
    
    .course:last-child {
        border-bottom: none;
    }
    
    .room {
        font-size: 0.85em;
        color: #666;
        margin-top: 5px;
    }
    
    .empty-course {
        padding: 10px;
        background-color: #fafafa;
        color: #999;
        text-align: center;
        font-style: italic;
    }
    
    .comments {
        margin: 10px 0;
        padding: 10px;
        background-color: #fff9c4;
        border-left: 4px solid #ffd600;
        border-radius: 3px;
    }
    
    .comment {
        margin-bottom: 5px;
    }
    
    .comment:last-child {
        margin-bottom: 0;
    }
    
    .month-nav {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    .month-nav a {
        display: inline-block;
        padding: 8px 15px;
        margin: 0 10px;
        background-color: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
    }
    
    @media (max-width: 600px) {
        body {
            font-size: 14px;
        }
        
        .container {
            padding: 5px;
        }
        
        h1 {
            font-size: 1.3em;
            margin: 8px 0;
        }
        
        .grade-nav a {
            padding: 6px 10px;
            font-size: 0.9em;
        }
        
        .header-item, .period-cell, .course {
            padding: 8px 5px;
        }
    }
    """
    
    # HTMLのヘッダー部分
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year}年{month}月{day}日({weekday}) 時間割</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <h1>{year}年{display_date} 時間割</h1>
        
        <div class="grade-nav">
"""

    # 学年切り替え用のリンクを追加
    for grade in grades:
        grade_id = grade.replace('年生', '').replace('助産', '_josan')
        html += f'            <a href="#{grade_id}" onclick="showGrade(\'{grade_id}\')">{grade}</a>\n'

    html += """        </div>
        
"""

    # 各学年のデータを追加
    for grade in grades:
        grade_id = grade.replace('年生', '').replace('助産', '_josan')
        html += f'        <div id="{grade_id}" class="grade-section">\n'
        html += f'            <h2>{grade}</h2>\n'
        
        # コメントがあれば表示
        if 'comments' in day_data[grade] and day_data[grade]['comments']:
            html += '            <div class="comments">\n'
            for comment in day_data[grade]['comments']:
                html += f'                <div class="comment">{comment}</div>\n'
            html += '            </div>\n'
        
        html += '            <div class="timetable">\n'
        html += '                <div class="header">\n'
        html += '                    <div class="header-item header-period">時限</div>\n'
        html += '                    <div class="header-item" style="flex: 1;">科目 / 教室</div>\n'
        html += '                </div>\n'
        
        # 各時限のデータを追加
        for period in range(1, 6):
            html += '                <div class="row">\n'
            html += f'                    <div class="period-cell">{period}限</div>\n'
            html += '                    <div class="course-container">\n'
            
            if period in day_data[grade]:
                course_data = day_data[grade][period]
                courses = course_data['courses']
                room = course_data['room'] if course_data['room'] else ""
                
                html += f'                        <div class="course">{courses}\n'
                if room:
                    html += f'                            <div class="room">{room}</div>\n'
                html += '                        </div>\n'
            else:
                html += '                        <div class="empty-course">授業なし</div>\n'
            
            html += '                    </div>\n'
            html += '                </div>\n'
        
        html += '            </div>\n'
        html += '        </div>\n'
    
    # 前日と翌日へのリンク
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    prev_day = date_obj - datetime.timedelta(days=1)
    next_day = date_obj + datetime.timedelta(days=1)
    
    # 同じ月内かチェック
    if prev_day.month == date_obj.month:
        prev_link = f'schedule_day_{prev_day.strftime("%Y-%m-%d")}.html'
    else:
        prev_link = '#'
    
    if next_day.month == date_obj.month:
        next_link = f'schedule_day_{next_day.strftime("%Y-%m-%d")}.html'
    else:
        next_link = '#'
    
    html += f"""
        <div class="month-nav">
            <a href="{prev_link}" {'style="visibility: hidden;"' if prev_link == '#' else ''}>前日</a>
            <a href="index.html">月間カレンダー</a>
            <a href="{next_link}" {'style="visibility: hidden;"' if next_link == '#' else ''}>翌日</a>
        </div>
    """
    
    # JavaScriptを追加して学年切り替え機能を実装
    html += """
        <script>
            // 初期表示時は最初の学年を表示
            document.addEventListener('DOMContentLoaded', function() {
                const gradeSections = document.querySelectorAll('.grade-section');
                const gradeLinks = document.querySelectorAll('.grade-nav a');
                
                // 最初の学年以外を非表示
                for (let i = 1; i < gradeSections.length; i++) {
                    gradeSections[i].style.display = 'none';
                }
                
                // 最初のリンクをアクティブに
                if (gradeLinks.length > 0) {
                    gradeLinks[0].classList.add('active');
                }
            });
            
            // 学年切り替え関数
            function showGrade(gradeId) {
                const gradeSections = document.querySelectorAll('.grade-section');
                const gradeLinks = document.querySelectorAll('.grade-nav a');
                
                // すべての学年を非表示にし、リンクのアクティブ状態を解除
                gradeSections.forEach(section => {
                    section.style.display = 'none';
                });
                
                gradeLinks.forEach(link => {
                    link.classList.remove('active');
                });
                
                // 選択された学年を表示し、リンクをアクティブに
                document.getElementById(gradeId).style.display = 'block';
                
                // 対応するリンクをアクティブに
                for (let i = 0; i < gradeLinks.length; i++) {
                    if (gradeLinks[i].getAttribute('href') === '#' + gradeId) {
                        gradeLinks[i].classList.add('active');
                        break;
                    }
                }
                
                // スクロールを防止
                return false;
            }
        </script>
    </div>
</body>
</html>
"""
    
    return html

def generate_month_index_html(year, month, days_with_data):
    """
    月間インデックスページのHTMLを生成する
    
    Args:
        year (int): 年
        month (int): 月
        days_with_data (list): データがある日のリスト
    
    Returns:
        str: 生成されたHTML
    """
    month_name = {
        1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月',
        7: '7月', 8: '8月', 9: '9月', 10: '10月', 11: '11月', 12: '12月'
    }
    
    # CSSスタイルを定義
    css = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
        color: #333;
        background-color: #f5f5f5;
        font-size: 16px;
    }
    
    .container {
        max-width: 100%;
        margin: 0 auto;
        padding: 10px;
    }
    
    h1 {
        color: #2c3e50;
        text-align: center;
        margin: 20px 0;
        font-size: 1.8em;
    }
    
    .calendar {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        margin: 20px 0;
    }
    
    .calendar-header {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        margin-bottom: 5px;
    }
    
    .calendar-header div {
        text-align: center;
        font-weight: bold;
        padding: 10px;
    }
    
    .day {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .day a {
        display: block;
        width: 100%;
        height: 100%;
        text-decoration: none;
        color: #333;
    }
    
    .day.has-data {
        background-color: #e3f2fd;
    }
    
    .day.has-data a {
        color: #0d47a1;
        font-weight: bold;
    }
    
    .day.sunday {
        background-color: #ffebee;
    }
    
    .day.saturday {
        background-color: #e3f2fd;
    }
    
    .day.other-month {
        background-color: #f5f5f5;
        color: #aaa;
    }
    
    .month-nav {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    .month-nav a {
        display: inline-block;
        padding: 8px 15px;
        margin: 0 10px;
        background-color: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
    }
    
    @media (max-width: 600px) {
        body {
            font-size: 14px;
        }
        
        .container {
            padding: 5px;
        }
        
        h1 {
            font-size: 1.5em;
            margin: 15px 0;
        }
        
        .day {
            padding: 5px;
            min-height: 50px;
        }
    }
    """
    
    # HTMLのヘッダー部分
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year}年{month_name[month]} 時間割カレンダー</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <h1>{year}年{month_name[month]} 時間割カレンダー</h1>
        
        <div class="calendar-header">
            <div style="color: #e53935;">日</div>
            <div>月</div>
            <div>火</div>
            <div>水</div>
            <div>木</div>
            <div>金</div>
            <div style="color: #1e88e5;">土</div>
        </div>
        
        <div class="calendar">
"""
    
    # カレンダーを生成
    cal = calendar.monthcalendar(year, month)
    
    for week in cal:
        for day in week:
            if day == 0:
                # 当月以外の日
                html += '            <div class="day other-month"></div>\n'
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                weekday = date_obj.weekday()
                
                # 曜日に応じたクラスを追加
                day_class = "day"
                if weekday == 6:  # 日曜日
                    day_class += " sunday"
                elif weekday == 5:  # 土曜日
                    day_class += " saturday"
                
                # データがある日かチェック
                if date_str in days_with_data:
                    day_class += " has-data"
                    html += f'            <div class="{day_class}"><a href="schedule_day_{date_str}.html">{day}</a></div>\n'
                else:
                    html += f'            <div class="{day_class}">{day}</div>\n'
    
    html += """        </div>
        
        <div class="month-nav">
"""
    
    # 前月と翌月へのリンク
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    
    html += f'            <a href="../{prev_year}{prev_month:02d}/index.html">前月</a>\n'
    html += f'            <a href="../{next_year}{next_month:02d}/index.html">翌月</a>\n'
    
    html += """        </div>
    </div>
</body>
</html>
"""
    
    return html

def save_html_files(year, month, schedule_data, grades):
    """
    生成されたHTMLをファイルに保存する
    
    Args:
        year (int): 年
        month (int): 月
        schedule_data (dict): スケジュールデータ
        grades (list): 学年のリスト
    
    Returns:
        list: 保存されたファイルのパスのリスト
    """
    # docsフォルダ内に年月のフォルダを作成
    month_dir = f"docs/{year}{month:02d}"
    os.makedirs(month_dir, exist_ok=True)
    
    saved_files = []
    days_with_data = []
    
    # 各日のHTMLを生成して保存（全ての日を生成）
    for date_str, day_data in schedule_data.items():
        # データがあるかチェック
        has_data = False
        for grade_data in day_data.values():
            if grade_data and isinstance(grade_data, dict) and any(k != 'comments' for k in grade_data.keys()):
                has_data = True
                break
        
        # データがある日をリストに追加
        if has_data:
            days_with_data.append(date_str)
        
        # 全ての日のHTMLを生成（データがなくても生成）
        html = generate_html_for_day(date_str, day_data, grades)
        
        # ファイル名を作成
        filename = f"{month_dir}/schedule_day_{date_str}.html"
        
        # HTMLをファイルに書き込む
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        saved_files.append(filename)
    
    # 月間インデックスページを生成して保存
    index_html = generate_month_index_html(year, month, days_with_data)
    index_filename = f"{month_dir}/index.html"
    
    with open(index_filename, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    saved_files.append(index_filename)
    
    return saved_files

def main():
    """
    メイン関数
    """
    # コマンドライン引数を解析する代わりに、ユーザー入力を受け付ける
    if len(sys.argv) > 2:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # 年月の入力を受け付ける
        year_input = input("年を入力してください (例: 2025): ")
        month_input = input("月を入力してください (1-12): ")
        
        try:
            year = int(year_input)
            month = int(month_input)
            
            if month < 1 or month > 12:
                print("無効な月です。1から12の間で入力してください。")
                return
        except ValueError:
            print("無効な入力です。年は整数、月は1から12の整数で入力してください。")
            return
    
    # 指定された年月のスケジュールデータを取得
    schedule_data, grades = get_schedule_data_for_month(year, month)
    
    # HTMLファイルを生成して保存
    saved_files = save_html_files(year, month, schedule_data, grades)
    
    print(f"{year}年{month}月の時間割HTMLファイルが生成されました。")
    print(f"合計 {len(saved_files)} 個のファイルが docs/{year}{month:02d}/ フォルダに保存されました。")
    print(f"インデックスページ: docs/{year}{month:02d}/index.html")

if __name__ == "__main__":
    main()
