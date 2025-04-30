from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import mysql.connector
import os

app = Flask(__name__)

# LINE 憑證
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# webhook endpoint
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 訊息處理邏輯
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    store_to_mysql(user_id, user_text)
    reply = TextSendMessage(text=f"你說的是：{user_text}")
    line_bot_api.reply_message(event.reply_token, reply)

# 儲存訊息到 Railway MySQL
def store_to_mysql(user_id, user_text):
    conn = mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT"))
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(64),
            message TEXT
        );
    """)
    cursor.execute("INSERT INTO user_messages (user_id, message) VALUES (%s, %s);", (user_id, user_text))
    conn.commit()
    cursor.close()
    conn.close()

# 健康檢查
@app.route("/")
def index():
    return "LINE Bot 啟動成功"

