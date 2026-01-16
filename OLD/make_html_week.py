#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import locale
import sqlite3
import datetime
import os
import sys

def get_schedule_data_for_week(grade, start_date):
    """
    指定された学年と開始日の週のスケジュールデータを取得する
    
    Args:
        grade (str): 学年
        start_date (datetime): 週の開始日（月曜日）
    
    Returns:
        dict: 日付をキー、periodをサブキーとし、courses, roomを値とする辞書
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # 週の5日間の日付を生成
    dates = []
    for i in range(5):  # 月曜から金曜までの5日間
        date = start_date + datetime.timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    # 指定された週と学年のデータを取得
    query = """
    SELECT date, period, courses, room, comment
    FROM schedule
    WHERE date IN (?, ?, ?, ?, ?) AND grade = ?
    ORDER BY date, period
    """
    
    cursor.execute(query, (*dates, grade))
    rows = cursor.fetchall()
    
    # データ構造を作成
    schedule_data = {}
    for date in dates:
        schedule_data[date] = {}
    
    for date, period, courses, room, comment in rows:
        # 日付をキー、periodをサブキーとする辞書を作成
        if period == 0:  # コメント行の場合
            if 'comments' not in schedule_data[date]:
                schedule_data[date]['comments'] = []
            schedule_data[date]['comments'].append(comment)
        else:
            schedule_data[date][period] = {
                'courses': courses,
                'room': room
            }
    
    # 接続を閉じる
    conn.close()
    
    return schedule_data, dates

def get_available_grades():
    """
    利用可能な学年のリストを取得する
    
    Returns:
        list: 学年のリスト
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # 利用可能な学年を取得
    cursor.execute("SELECT DISTINCT grade FROM schedule ORDER BY grade")
    grades = [grade[0] for grade in cursor.fetchall()]
    
    # 接続を閉じる
    conn.close()
    
    return grades

def get_monday_of_week(date_obj):
    """
    指定された日付の週の月曜日を取得する
    
    Args:
        date_obj (datetime): 日付
    
    Returns:
        datetime: 週の月曜日の日付
    """
    # 曜日を取得（0:月, 1:火, ..., 6:日）
    weekday = date_obj.weekday()
    
    # 週の月曜日を計算
    monday = date_obj - datetime.timedelta(days=weekday)
    
    return monday

def generate_html(grade, start_date, schedule_data, dates, all_grades):
    """
    スケジュールデータからHTMLを生成する
    
    Args:
        grade (str): 学年
        start_date (datetime): 週の開始日（月曜日）
        schedule_data (dict): スケジュールデータ
        dates (list): 週の日付のリスト
        all_grades (list): 利用可能な全学年のリスト
    
    Returns:
        str: 生成されたHTML
    """
    # 曜日の表示用リスト
    weekdays = ['月', '火', '水', '木', '金']
    
    # タイトル用の日付の範囲を作成
    end_date = start_date + datetime.timedelta(days=4)
    title_date_range = f"{start_date.year}年{start_date.month}月{start_date.day}日〜{end_date.month}月{end_date.day}日"
    
    # 前週と次週のリンク用の日付を計算
    prev_week = start_date - datetime.timedelta(days=7)
    next_week = start_date + datetime.timedelta(days=7)
    
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
        background-color: #fcfcfc;
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

    .timetable {
        display: grid;
        grid-template-columns: 10% repeat(5, 1fr);
        grid-template-rows: 50px repeat(5, 1fr);
        width: 100%;
        max-width: 1024px;
        margin: 0 auto;
        margin-bottom: 20px;
        gap: 1px;
    }

    .navigation {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
    }

    .grade-selection {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        margin: 10px 0;
        gap: 10px;
    }

    .grade-link {
        padding: 5px 10px;
        background-color: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 3px;
    }

    .grade-link.active {
        background-color: #2c3e50;
    }

    .cell {
        padding: 10px;
        text-align: center;
        vertical-align: middle;
        height: 80px;
        background-color: white;
        
        word-break: break-word;
        white-space: normal;
        overflow-wrap: break-word;
    }

    .period {
        background-color: #f2f2f2;
        font-weight: bold;
        
        /* 中央ぞろえ */
        display: flex;
        align-items: center; 
        justify-content: center;
    }

    .header {
        background-color: #3498db;
        color: white;
        font-weight: bold;
        text-align: center;
        padding: 5px;
    }

    .date-header {
        font-size: 0.9em;
    }

    .empty-course {
        color: #999;
        background-color: #f3f3f3;
    }

    .room {
        font-size: 0.8em;
        color: #666;
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
            font-size: 11px;
        }
        
        .container {
            padding: 5px;
        }
        
        h1 {
            font-size: 1.3em;
            margin: 8px 0;
        }
        
        .header, .course {
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
    <title>{grade} 週間時間割 {title_date_range}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <h1>{grade} 週間時間割</h1>
        <h2 style="text-align: center; font-size: 1.2em; margin-bottom: 15px;">{title_date_range}</h2>
        
        <div class="grade-selection">
"""

    # 学年選択リンクを追加
    for g in all_grades:
        active_class = " active" if g == grade else ""
        html += f'            <a href="?grade={g}&date={start_date.strftime("%Y-%m-%d")}" class="grade-link{active_class}">{g}</a>\n'

    html += """
        </div>
        
        <div class="navigation">
            <a href="?grade=""" + str(grade) + "&date=" + prev_week.strftime("%Y-%m-%d") + """">前の週</a>
            <a href="?grade=""" + str(grade) + "&date=" + next_week.strftime("%Y-%m-%d") + """">次の週</a>
        </div>
        
        <div class="timetable">
            <div class="header cell">時限</div>
"""

    # 曜日と日付のヘッダーを追加
    for i, date in enumerate(dates):
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        day = date_obj.day
        month = date_obj.month
        weekday = weekdays[i]
        html += f'            <div class="header cell">{weekday}<br /><span class="date-header">{month}/{day}</span></div>\n'

    # 時限と授業内容を追加
    for period in range(1, 6):  # 1限から5限まで
        html += f'            <div class="period cell">{period}限</div>\n'
        
        for date in dates:
            if period in schedule_data[date]:
                course_data = schedule_data[date][period]
                courses = course_data['courses']
                room = course_data['room'] if course_data['room'] else ""
                
                html += f'            <div class="cell">{courses}\n'
                if room:
                    html += f'                <div class="room">{room}</div>\n'
                html += '            </div>\n'
            else:
                html += '            <div class="cell empty-course">授業なし</div>\n'
    
    # コメントを表示（ある場合）
    comments_exist = False
    comments_html = '        <div class="comments">\n'
    
    for date in dates:
        if 'comments' in schedule_data[date] and schedule_data[date]['comments']:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            day = date_obj.day
            month = date_obj.month
            weekday = weekdays[dates.index(date)]
            
            comments_exist = True
            comments_html += f'            <div class="comment"><strong>{month}/{day}({weekday})</strong>: {" / ".join(schedule_data[date]["comments"])}</div>\n'
    
    comments_html += '        </div>\n'
    
    if comments_exist:
        html += comments_html
    
    # HTMLの終了部分
    html += """
        </div>
    </div>
    
    <script>
        // URLパラメータから値を取得する関数
        function getUrlParam(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        }
        
        // フォーム送信時の処理
        function handleSubmit(event) {
            event.preventDefault();
            const gradeSelect = document.getElementById('grade-select');
            const dateInput = document.getElementById('date-input');
            
            window.location.href = `?grade=${gradeSelect.value}&date=${dateInput.value}`;
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('filter-form');
            if (form) {
                form.addEventListener('submit', handleSubmit);
            }
        });
    </script>
</body>
</html>
"""
    
    return html

def save_html(html, grade, start_date):
    """
    生成されたHTMLをファイルに保存する
    
    Args:
        html (str): 生成されたHTML
        grade (str): 学年
        start_date (datetime): 週の開始日
    
    Returns:
        str: 保存されたファイルのパス
    """
    # ファイル名を作成
    date_str = start_date.strftime("%Y-%m-%d")
    filename = f"schedule_week_{grade}_{date_str}.html"
    
    # HTMLをファイルに書き込む
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename

def main():
    """
    メイン関数
    """
    # コマンドライン引数からパラメータを取得
    if len(sys.argv) < 2:
        print("使用法: python make_html_week.py 学年 [YYYY-MM-DD]")
        print("例: python make_html_week.py \"1年生\" 2025-04-07")
        return
    
    grade = sys.argv[1]
    
    # 日付が指定されていれば解析、なければ今日の日付を使用
    if len(sys.argv) >= 3:
        try:
            date_obj = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%d")
        except ValueError:
            print("無効な日付形式です。YYYY-MM-DD形式で入力してください。")
            return
    else:
        date_obj = datetime.datetime.now()
    
    # 指定された日付の週の月曜日を取得
    monday = get_monday_of_week(date_obj)
    
    # 利用可能な学年のリストを取得
    all_grades = get_available_grades()
    
    if grade not in all_grades:
        print(f"指定された学年 {grade} は利用できません。")
        print(f"利用可能な学年: {', '.join(map(str, all_grades))}")
        return
    
    # 週のスケジュールデータを取得
    schedule_data, dates = get_schedule_data_for_week(grade, monday)
    
    # HTMLを生成
    html = generate_html(grade, monday, schedule_data, dates, all_grades)
    
    # HTMLをファイルに保存
    filename = save_html(html, grade, monday)
    
    print(f"HTMLファイルが生成されました: {filename}")

if __name__ == "__main__":
    main()
