import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import mysql.connector
from celery import Celery

# 初始化 Flask
app = Flask(__name__)

# 設定 Celery
celery = Celery(app.name, broker='redis://localhost:6379/0')

# 環境變數設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# 初始化 LINE Bot SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# Celery 背景任務
@celery.task
def insert_to_db(user_id, user_text):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(50), message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        cursor.execute(
            "INSERT INTO messages (user_id, message) VALUES (%s, %s)",
            (user_id, user_text)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        app.logger.error(f"❌ 資料庫寫入失敗：{e}")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # 回覆用戶訊息
    reply = f"你說了：{user_text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

    # 異步執行資料庫插入操作
    insert_to_db.apply_async(args=[user_id, user_text])
