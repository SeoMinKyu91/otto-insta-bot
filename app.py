from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters

app = Flask(__name__)

# 환경변수 가져오기
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = ScrapflyClient(key=SCRAPFLY_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

# 메시지 핸들러
async def handle_message(update: Update, context):
    print("✅ 여기까지 실행됨 - handle_message 진입")

    try:
        url = update.message.text.strip()
        print(f"🔗 수신된 URL: {url}")

        result = client.scrape(ScrapeConfig(url=url))
        soup = BeautifulSoup(result.content, "html.parser")

        title_tag = soup.find("meta", property="og:title")
        desc_tag = soup.find("meta", property="og:description")

        title = title_tag["content"] if title_tag else "제목 없음"
        desc = desc_tag["content"] if desc_tag else "설명 없음"

        print(f"📌 파싱 결과 - title: {title}, desc: {desc}")

        reply = f"📌 *제목:* {title}\n📝 *설명:* {desc}"
        await update.message.reply_markdown(reply)
        print("✅ 메시지 전송 성공")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        await update.message.reply_text(f"❌ 오류 발생: {e}")

# 웹훅 수신 엔드포인트
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    print("📬 Webhook 호출됨")
    update = Update.de_json(request.get_json(force=True), bot)

    app_telegram = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_telegram.process_update(update)

    return "OK", 200

# 헬스체크용 루트
@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
