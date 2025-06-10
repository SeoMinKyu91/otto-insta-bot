from flask import Flask, request
from scrapfly import ScrapflyClient, ScrapeConfig
from bs4 import BeautifulSoup
import os
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Flask 서버 시작
app = Flask(__name__)

# 환경 변수에서 키 불러오기
SCRAPFLY_KEY = os.getenv("SCRAPFLY_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Scrapfly Client 생성
client = ScrapflyClient(key=SCRAPFLY_KEY)

# 텔레그램 봇 초기화
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 기본 index 경로
@app.route("/")
def index():
    return "✅ Telegram Insta Bot is running!"

# 텔레그램 Webhook 수신 엔드포인트
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "OK", 200

# 메시지 핸들러 함수
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        return

    await update.message.reply_text("🔍 인스타그램 링크를 분석 중입니다...")

    try:
        result = client.scrape(ScrapeConfig(url=text))
        soup = BeautifulSoup(result.content, "html.parser")

        title_tag = soup.find("meta", property="og:title")
        desc_tag = soup.find("meta", property="og:description")

        if not title_tag or not desc_tag:
            raise ValueError("메타 정보 없음")

        title = title_tag["content"]
        desc = desc_tag["content"]

        msg = f"📌 *제목*: {title}\n📝 *설명*: {desc}\n🔗 *링크*: {text}"
        await update.message.reply_markdown(msg)
    except Exception:
        await update.message.reply_text(
            "⚠️ 게시물에 접근하려면 Instagram 로그인이 필요할 수 있어요.\n"
            "직접 링크를 눌러 확인해보세요 👇\n" + text
        )

# 핸들러 등록
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 웹서버 실행 (Render용 포트 명시)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
