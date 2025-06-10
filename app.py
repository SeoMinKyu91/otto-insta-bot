from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask(__name__)

# 🔑 환경변수
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = ScrapflyClient(key=SCRAPFLY_KEY)

# ✅ Telegram Bot 객체
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 🔧 Message Handler 등록
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        return
    await update.message.reply_text("🔍 인스타 링크를 분석 중입니다...")
    try:
        result = client.scrape(ScrapeConfig(url=text))
        soup = BeautifulSoup(result.content, "html.parser")
        title = soup.find("meta", property="og:title")["content"]
        desc = soup.find("meta", property="og:description")["content"]
        msg = f"📌 *제목*: {title}\n📝 *설명*: {desc}\n🔗 *링크*: {text}"
        await update.message.reply_markdown(msg)
    except Exception as e:
        await update.message.reply_text(f"❗ 오류 발생: {e}")

bot_app.add_handler(MessageHandler(filters.ALL, handle_message))

# ✅ Webhook 처리 라우트 (Flask는 동기)
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    asyncio.run(bot_app.process_update(update))
    return "OK", 200

@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

# ✅ Render 환경에서 포트 명시
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
