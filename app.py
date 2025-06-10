from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask(__name__)

# 환경 변수에서 키 불러오기
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = ScrapflyClient(key=SCRAPFLY_KEY)

# 응답 핸들러 함수
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "instagram.com" not in text:
        await update.message.reply_text("❌ 유효한 인스타그램 링크가 아닙니다.")
        return
    await update.message.reply_text("🔍 분석 중입니다...")

    try:
        result = client.scrape(ScrapeConfig(url=text, render_js=True))
        soup = BeautifulSoup(result.content, "html.parser")
        title = soup.find("meta", property="og:title")["content"]
        desc = soup.find("meta", property="og:description")["content"]

        reply = f"📌 *제목*: {title}\n📝 *설명*: {desc}\n🔗 [원본 링크]({text})"
        await update.message.reply_markdown(reply)
    except Exception as e:
        await update.message.reply_text(f"⚠️ 오류 발생: {e}")

# 텔레그램 webhook 수신
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(app_telegram.process_update(update))
    return "OK", 200

# 기본 라우트
@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

# 텔레그램 핸들러 설정
bot = None
app_telegram = None
def setup_bot():
    global bot, app_telegram
    bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    global app_telegram
    app_telegram = bot

setup_bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
