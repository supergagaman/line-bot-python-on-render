import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import mysql.connector

# ✅ 啟動確認 log
print("✅ Flask App 啟動中...")

# 初始化 Flask
app = Flask(__name__)

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
    return "✅ LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    print(f"📩 收到訊息：{user_text}，來自：{user_id}")

    # 回覆用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說了：{user_text}")
    )

    # 寫入 MySQL 資料庫（收到訊息後再連線）
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
        print("✅ 資料成功寫入 MySQL")
    except Exception as e:
        print("❌ 資料庫寫入失敗：", e)

# ✅ 本地測試時使用 Flask 啟動（Render 使用 gunicorn 不會執行這段）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
