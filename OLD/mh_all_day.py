import calendar
import locale
import json
import datetime
import os
import sys
from urllib.parse import urlparse, parse_qs

def get_schedule_data_for_day(date_str, grade):
    """
    指定された日付と学年のスケジュールデータを取得する
    
    Args:
        date_str (str): 日付 ('YYYY-MM-DD'形式)
        grade (str): 学年
    
    Returns:
        dict: periodをサブキーとし、courses, roomを値とする辞書
    """
    # JSONファイルからデータを読み取る
    with open('schedule.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 指定された日付と学年のデータをフィルタリング
    schedule_data = {}
    for entry in data:
        if entry['date'] == date_str and entry['grade'] == grade:
            period = entry['period']
            courses = entry['courses']
            room = entry['room']
            comment = entry['comment']
            
            if period == 0:  # コメント行の場合
                if 'comments' not in schedule_data:
                    schedule_data['comments'] = []
                schedule_data['comments'].append(comment)
            else:
                schedule_data[period] = {
                    'courses': courses,
                    'room': room
                }
    
    return schedule_data

def generate_html(date_str, schedule_data, grade, prev_date, next_date):
    """
    スケジュールデータからHTMLを生成する
    
    Args:
        date_str (str): 日付 ('YYYY-MM-DD'形式)
        schedule_data (dict): スケジュールデータ
        grade (str): 学年
    
    Returns:
        str: 生成されたHTML
    """
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day
    
    # 曜日を取得
    weekdays = ['日', '月', '火', '水', '木', '金', '土']
    weekday = weekdays[(date_obj.weekday() + 1) % 7]
    
    # 日付の表示形式
    display_date = f"{month}月{day}日({weekday})"
    
    prev_ref = f"schedule.html?grade={grade}&day={prev_date}"
    next_ref = f"schedule.html?grade={grade}&day={next_date}"
    
    # CSSスタイルを定義
    css = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        touch-action: pan-y; /* 縦スクロールは許可、横はJSで扱う */
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

    .cell {
        padding: 10px;
        text-align: center;
        vertical-align: middle;
        height: 100px;
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
    <title>{year}年{month}月{day}日({weekday}) 時間割</title>
    <style>
{css}
    </style>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>{display_date} - {grade}</h1>
    <div class="navigation">
        <a href="{prev_ref}">前の日</a>
        <a href="{next_ref}">次の日</a>
    </div>
        <div class="timetable">
"""

    # 時限の列を追加
    html += '        <div class="header cell">時限</div>\n'
    html += f'        <div class="header cell">{grade}</div>\n'

    for period in range(1, 6):
        html += f'        <div class="period cell">{period}限</div>\n'
        if period in schedule_data:
            course_data = schedule_data[period]
            courses = course_data['courses']
            room = course_data['room'] if course_data['room'] else ""
            
            html += f'        <div class="cell">{courses}\n'
            if room:
                html += f'            <div class="room">{room}</div>\n'
            html += '        </div>\n'
        else:
            html += '        <div class="cell empty-course">授業なし</div>\n'
    
    html += """
        </div>
    </div>
    
<script>
  let touchStartX = 0;
  let touchEndX = 0;

  const threshold = 50; // スワイプ判定のしきい値（px）

  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
  });

  document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  });

  function handleSwipe() {
    const deltaX = touchEndX - touchStartX;

    if (Math.abs(deltaX) > threshold) {
      if (deltaX > 0) {
        // 右スワイプ
        window.location.href = '""" + prev_ref + """';
      } else {
        // 左スワイプ
        window.location.href = '""" + next_ref + """';
      }
    }
  }
</script>

</body>
</html>
"""
    
    return html

def save_html(html, grade, date_str):
    """
    生成されたHTMLをファイルに保存する
    
    Args:
        html (str): 生成されたHTML
        grade (str): 学年
        date_str (str): 日付 ('YYYY-MM-DD'形式)
    
    Returns:
        str: 保存されたファイルのパス
    """
    # ファイル名を作成
    filename = f"schedule_{grade}_{date_str}.html"
    
    # HTMLをファイルに書き込む
    with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(html)
    
    return filename

def main():
    """
    メイン関数
    """
    # コマンドライン引数からURLを取得
    if len(sys.argv) != 2:
        print("使用法: python mh_all_day.py 'schedule.html?grade=1年生&day=20250401'")
        return
    
    url = sys.argv[1]
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    
    grade = params.get('grade', [None])[0]
    day = params.get('day', [None])[0]
    
    if not grade or not day:
        print("URLにgradeとdayのパラメータが必要です。")
        return
    
    # 日付を解析
    try:
        date_obj = datetime.datetime.strptime(day, "%Y%m%d")
        date_str = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print("無効な日付形式です。YYYYMMDD形式で入力してください。")
        return
    
    # スケジュールデータを取得
    schedule_data = get_schedule_data_for_day(date_str, grade)
    
    # 前日と翌日の日付を計算
    prev_date = (date_obj - datetime.timedelta(days=1)).strftime("%Y%m%d")
    next_date = (date_obj + datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    # HTMLを生成
    html = generate_html(date_str, schedule_data, grade, prev_date, next_date)
    
    # HTMLをファイルに保存
    filename = save_html(html, grade, date_str)
    
    print(f"HTMLファイルが生成されました: {filename}")

if __name__ == "__main__":
    main()
