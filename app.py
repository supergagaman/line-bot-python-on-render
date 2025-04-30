import os
import mysql.connector
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# Line Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# MySQL 連接配置
MYSQL_HOST = os.getenv("MYSQLHOST")
MYSQL_PORT = int(os.getenv("MYSQLPORT"))
MYSQL_USER = os.getenv("MYSQLUSER")
MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

def save_to_db(user_id, user_text):
    try:
        # 連接 MySQL 資料庫
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        # 插入資料到資料表
        cursor.execute(
            "INSERT INTO user_messages (user_id, user_text) VALUES (%s, %s)",
            (user_id, user_text)
        )
        conn.commit()
        
        # 關閉游標和連接
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

@app.route("/callback", methods=["POST"])
def callback():
    # 獲取請求的簽名
    signature = request.headers["X-Line-Signature"]

    # 解析 webhook 請求
    body = request.get_data(as_text=True)
    
    try:
        # 處理訊息
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    
    # 將用戶的訊息保存到資料庫
    save_to_db(user_id, user_text)
    
    # 回應用戶的訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"收到你的訊息: {user_text}")
    )

if __name__ == "__main__":
    app.run()
