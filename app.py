from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 환경 변수에서 키 불러오기
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 인스턴스 초기화
client = ScrapflyClient(key=SCRAPFLY_KEY)
app = Flask(__name__)
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 텔레그램 Webhook 요청 처리
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "OK", 200

# 기본 루트 페이지 확인용
@app.route("/")
def index():
    return "Telegram Insta Bot is running!"

# 메시지 처리 핸들러
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        return

    await update.message.reply_text("🔍 인스타그램 링크를 분석 중입니다...")

    try:
        result = client.scrape(ScrapeConfig(url=text))
        soup = BeautifulSoup(result.content, "html.parser")
        title = soup.find("meta", property="og:title")["content"]
        desc = soup.find("meta", property="og:description")["content"]
        msg = f"📌 *제목*: {title}\n📝 *설명*: {desc}\n🔗 *링크*: {text}"
        await update.message.reply_markdown(msg)
    except Exception as e:
        await update.message.reply_text(f"❗ 오류 발생: {e}")

# 핸들러 등록
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Render가 할당한 포트를 열어서 Flask 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
