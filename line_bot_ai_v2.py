
# line_bot_ai_v2.py - 最終防呆版（即時回應 + 防卡死）
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import subprocess
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_ACCESS_TOKEN = "jPdXQZ+8hP5dj89V3fvDpOfB7jRF+CcAs4gQbprxzQAuvew1Fwg/RPzS6+ryoIpHFelapnqe/6Qtfq35vEByBv4GodBRPnGcyaDastMr7wqw/5iGJvkWOc81pvp+NmChhX324gJH1cPIJXooVojuWgdB04t89/1O/w1cDnyilFU="  # 已重新產生
CHANNEL_SECRET = "c5b8d2d787f4d85ec4c16bbc47a62f68"

app = Flask(__name__)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def ask_ai_async(question, reply_token):
    """非同步呼叫 Llama3，避免 Flask 卡住"""
    try:
        logger.info(f"非同步問 AI: {question}")
        result = subprocess.run(
            ['ollama', 'run', 'llama3'],
            input=question,
            text=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=60  # 最多等 60 秒
        )
        reply = result.stdout.strip()[:1900]
        if reply:
            line_bot_api.push_message(
                "Ud6d0471b884cc564e7a1a3cd9fd45424",  # 你的 userId
                TextSendMessage(text=reply)
            )
            logger.info("AI 回覆已推送！")
        else:
            line_bot_api.push_message(
                "Ud6d0471b884cc564e7a1a3cd9fd45424",
                TextSendMessage(text="AI 正在思考中，請稍後～")
            )
    except Exception as e:
        logger.error(f"AI 錯誤: {e}")
        line_bot_api.push_message(
            "Ud6d0471b884cc564e7a1a3cd9fd45424",
            TextSendMessage(text="AI 小問題，請稍後再試～")
        )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info(f"收到 Webhook: {body[:200]}...")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("簽名錯誤")
        abort(400)
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    user_id = event.source.user_id
    logger.info(f"準備回覆: {user_text}")

    # 1. 先立即回應（避免 Line timeout）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="AI 正在思考中，請稍等 10-30 秒～")
    )
    logger.info("已送出「思考中」回覆")

    # 2. 非同步問 AI
    thread = threading.Thread(
        target=ask_ai_async,
        args=(user_text, event.reply_token)
    )
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    print("AI Line Bot v2 上線！（即時回應 + 防卡死）")
    app.run(host='0.0.0.0', port=5000, debug=False)
