import locale
import sqlite3
import calendar
import datetime
import os
import sys

def get_schedule_data_for_day(date_str):
    """
    指定された日付の全学年のスケジュールデータを取得する
    
    Args:
        date_str (str): 日付 ('YYYY-MM-DD'形式)
    
    Returns:
        dict: 学年をキー、periodをサブキーとし、courses, roomを値とする辞書
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # 利用可能な学年を取得
    cursor.execute("SELECT DISTINCT grade FROM schedule")
    grades = [grade[0] for grade in cursor.fetchall()]
    
    # 指定された日付の全学年のデータを取得
    query = """
    SELECT grade, period, courses, room, comment
    FROM schedule
    WHERE date = ?
    ORDER BY grade, period
    """
    
    cursor.execute(query, (date_str,))
    rows = cursor.fetchall()
    
    # データ構造を作成
    schedule_data = {}
    for grade in grades:
        schedule_data[grade] = {}
    
    for grade, period, courses, room, comment in rows:
        # 日付をキー、periodをサブキーとする辞書を作成
        if period == 0:  # コメント行の場合
            if 'comments' not in schedule_data[grade]:
                schedule_data[grade]['comments'] = []
            schedule_data[grade]['comments'].append(comment)
        else:
            schedule_data[grade][period] = {
                'courses': courses,
                'room': room
            }
    
    # 接続を閉じる
    conn.close()
    
    return schedule_data, grades

def generate_html(date_str, schedule_data, grades):
    """
    スケジュールデータからHTMLを生成する
    
    Args:
        date_str (str): 日付 ('YYYY-MM-DD'形式)
        schedule_data (dict): スケジュールデータ
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
        if 'comments' in schedule_data[grade] and schedule_data[grade]['comments']:
            html += '            <div class="comments">\n'
            for comment in schedule_data[grade]['comments']:
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
            
            if period in schedule_data[grade]:
                course_data = schedule_data[grade][period]
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

def save_html(html, date_str):
    """
    生成されたHTMLをファイルに保存する
    
    Args:
        html (str): 生成されたHTML
        date_str (str): 日付 ('YYYY-MM-DD'形式)
    
    Returns:
        str: 保存されたファイルのパス
    """
    # ファイル名を作成
    filename = f"schedule_day_{date_str}.html"
    
    # HTMLをファイルに書き込む
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename

def main():
    """
    メイン関数
    """
    # コマンドライン引数を解析する代わりに、ユーザー入力を受け付ける
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        # 日付の入力を受け付ける
        date_input = input("日付を入力してください (YYYY-MM-DD): ")
        try:
            # 入力された日付を解析
            date_obj = datetime.datetime.strptime(date_input, "%Y-%m-%d")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print("無効な日付形式です。YYYY-MM-DD形式で入力してください。")
            return
    
    # 指定された日付のスケジュールデータを取得
    schedule_data, grades = get_schedule_data_for_day(date_str)
    
    if not any(schedule_data.values()):
        print(f"指定された日付 {date_str} のデータはありません。")
        return
    
    # HTMLを生成
    html = generate_html(date_str, schedule_data, grades)
    
    # HTMLをファイルに保存
    filename = save_html(html, date_str)
    
    print(f"HTMLファイルが生成されました: {filename}")

if __name__ == "__main__":
    main()
