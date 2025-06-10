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

# 텔레그램 봇 초기화
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "OK", 200

@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

# 메시지 핸들러 함수
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

# 링크 메시지를 받기 위한 핸들러 등록
bot_app.add_handler(MessageHandler(filters.ALL, handle_message))

# 앱 실행
if __name__ == "__main__":
    bot_app.run_polling()
