import calendar
import locale
import sqlite3
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

def generate_html(date_str, schedule_data, grades, prev_date, next_date):
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
    weekdays = ['日', '月', '火', '水', '木', '金', '土']
    weekday = weekdays[(date_obj.weekday() + 1) % 7]
    
    # 日付の表示形式
    display_date = f"{month}月{day}日({weekday})"
    
    prev_ref = f"../{prev_date[0:6]}/{prev_date}.html"
    next_ref = f"../{next_date[0:6]}/{next_date}.html"
    
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
        grid-template-rows: 50px repeat(4, 1fr);
        width: 100%;
        width-max: 1024px;
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
</head>
<body>
    <div class="container">
        <h1>{display_date}</h1>
    <div class="navigation">
        <a href="{prev_ref}">前の日</a>
        <a href="{next_ref}">次の日</a>
    </div>
        <div class="timetable">
"""

    # 時限の列を追加
    html += '        <div class="header cell">時限</div>\n'
    for grade in grades:
        html += f'        <div class="header cell">{grade}</div>\n'

    for period in range(1, 6):
        html += f'        <div class="period cell">{period}限</div>\n'
        for grade in grades:
            if period in schedule_data[grade]:
                course_data = schedule_data[grade][period]
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
    filename = f"schedule_day_all_{date_str}.html"
    
    # HTMLをファイルに書き込む
    with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(html)
    
    return filename

def generate_html_for_month(year, month):
    """
    指定された年月の全ての日についてHTMLを生成し保存する
    
    Args:
        year (int): 年
        month (int): 月
    """
    # 月の日数を取得
    num_days = calendar.monthrange(year, month)[1]
    
    # 各日についてHTMLを生成
    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        prev_date = (datetime.datetime(year, month, day) - datetime.timedelta(days=1)).strftime("%Y%m%d")
        next_date = (datetime.datetime(year, month, day) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        schedule_data, grades = get_schedule_data_for_day(date_str)
        
        # HTMLを生成
        html = generate_html(date_str, schedule_data, grades, prev_date, next_date)
        
        # 保存先ディレクトリを作成
        dir_path = f"./docs/{year}{month:02d}/"
        os.makedirs(dir_path, exist_ok=True)
        
        # HTMLをファイルに保存
        filename = f"{dir_path}{year}{month:02d}{day:02d}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTMLファイルが生成されました: {filename}")

def main():
    """
    メイン関数
    """
    # コマンドライン引数から年月を取得
    if len(sys.argv) != 2:
        for month in range(4, 10):
            generate_html_for_month(2025, month)
        print("使用法: python make_html_day_all.py YYYY-MM")        
        return
    
    date_input = sys.argv[1]
    try:
        # 入力された年月を解析
        date_obj = datetime.datetime.strptime(date_input, "%Y-%m")
        year = date_obj.year
        month = date_obj.month
    except ValueError:
        print("無効な年月形式です。YYYY-MM形式で入力してください。")
        return

    generate_html_for_month(year, month)

if __name__ == "__main__":
    main()
