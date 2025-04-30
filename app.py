from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # 這裡可以加上處理 LINE 訊息邏輯
    print("Webhook received:", request.json)
    return "OK", 200

if __name__ == "__main__":
    app.run()
