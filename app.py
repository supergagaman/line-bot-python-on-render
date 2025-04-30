import os
import mysql.connector
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from openai import OpenAI  # ✅ 使用新版 SDK

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI 設定 (新版)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MySQL 設定
MYSQL_HOST = os.getenv("MYSQLHOST")
MYSQL_PORT = int(os.getenv("MYSQLPORT"))
MYSQL_USER = os.getenv("MYSQLUSER")
MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

def save_to_db(user_id, user_text):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_messages (user_id, user_text) VALUES (%s, %s)", (user_id, user_text))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving to database: {e}")

def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 或 "gpt-4"（視你的帳號授權）
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT Error: {e}")
        return "抱歉，無法取得回覆。"

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # 存入資料庫
    save_to_db(user_id, user_text)

    # 呼叫 GPT 回覆
    gpt_reply = ask_gpt(user_text)
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=gpt_reply)
    )

if __name__ == "__main__":
    app.run(debug=True)

