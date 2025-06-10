from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os
import asyncio

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 환경 변수 불러오기
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = ScrapflyClient(key=SCRAPFLY_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# 메시지 처리 핸들러
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("http"):
        await update.message.reply_text("🔗 인스타그램 URL을 입력해주세요.")
        return

    await update.message.reply_text("🔍 분석 중입니다...")

    try:
        result = client.scrape(ScrapeConfig(url=text, render_js=True, asp=True))
        soup = BeautifulSoup(result.content, "html.parser")

        title = soup.find("meta", property="og:title")["content"]
        desc = soup.find("meta", property="og:description")["content"]

        reply = f"📌 *제목*: {title}\n📝 *설명*: {desc}\n🔗 [원본 링크]({text})"
        await update.message.reply_markdown(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ 오류 발생: {e}")

# 텔레그램 Webhook 처리
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app_telegram = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))
    app_telegram.process_update(update)
    return "OK", 200

# 루트 페이지
@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

# 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
