from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import openai
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os

# 读取环境变量
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_URL = "https://newsapi.org/v2/top-headlines?country=de&apiKey=" + NEWS_API_KEY

# 定时任务调度器
scheduler = BackgroundScheduler()

# 配置日志
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_news():
    """ 获取最新的德国新闻 """
    response = requests.get(NEWS_API_URL)
    data = response.json()
    articles = data.get("articles", [])[:5]  # 取前 5 条新闻
    news_summary = "\n\n".join([f"🔹 {a['title']}\n{a['url']}" for a in articles])
    return news_summary if news_summary else "❌ 暂无新闻"

def send_news(update: Update, context: CallbackContext):
    """ 用户主动请求新闻 """
    news = get_news()
    update.message.reply_text(f"📰 今日德国新闻：\n\n{news}")

def ask_ai(update: Update, context: CallbackContext):
    """ 处理用户对新闻的提问，调用 ChatGPT API """
    user_message = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "你是一个新闻助手，帮助用户解析新闻内容"},
                  {"role": "user", "content": user_message}]
    )
    answer = response["choices"][0]["message"]["content"]
    update.message.reply_text(f"🤖 AI 解答：\n{answer}")

def scheduled_news(context: CallbackContext):
    """ 定时推送新闻 """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")  # 你的 Telegram 个人或群组 ID
    news = get_news()
    context.bot.send_message(chat_id=chat_id, text=f"📰 定时新闻推送：\n\n{news}")

def start(update: Update, context: CallbackContext):
    """ 处理 /start 命令 """
    update.message.reply_text("👋 欢迎使用新闻机器人！\n发送 /news 获取今日新闻\n直接提问 AI 获取新闻解析！")

def main():
    """ 运行 Telegram Bot """
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # 绑定命令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("news", send_news))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, ask_ai))

    # 设置定时任务（每天 20:00 推送）
    scheduler.add_job(scheduled_news, 'cron', hour=20, minute=0, args=[dp.job_queue])
    scheduler.start()

    # 开始轮询
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
