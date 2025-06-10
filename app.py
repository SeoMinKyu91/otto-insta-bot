
from flask import Flask, request
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = "7778973902:AAHcQtUzAgtDHmVDESsBwgQIsoeNo-OZfMQ"
SCRAPFLY_KEY = "scp-live-..."  # 여기에 본인 Scrapfly 키 입력
client = ScrapflyClient(key=SCRAPFLY_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("https://www.instagram.com/p/"):
        await update.message.reply_text("❗ 인스타그램 게시물 URL만 보내주세요.")
        return

    await update.message.reply_text("🔍 분석 중입니다. 잠시만 기다려주세요...")
    try:
        result = client.scrape(ScrapeConfig(url=url, render_js=True, asp=True))
        soup = BeautifulSoup(result.content, "html.parser")
        title = soup.find("meta", property="og:title")["content"]
        desc = soup.find("meta", property="og:description")["content"]

        reply = f"📌 *제목*: {title}\n📝 *내용*: {desc}\n🔗 [원본 링크]({url})\n\n"
        reply += "| 제목 | 설명 | 원본 링크 |\n|------|------|-----------|\n"
        escape = lambda txt: txt.replace("|","｜").replace("\n"," ").strip()
        reply += f"| {escape(title)} | {escape(desc)} | [바로가기]({url}) |"

        await update.message.reply_markdown(reply)
    except Exception as e:
        await update.message.reply_text(f"❌ 분석 실패: {e}")

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), ApplicationBuilder().token(TELEGRAM_TOKEN).build().bot)
    builder = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    builder.process_update(update)
    return "OK", 200

@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
