import os
import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from datetime import datetime, timedelta

ins_codes = {
    "46348559193224090": "فولاد",
    '6110133418282108': "پارس",
    '35700344742885862': "کگل",
    '7395271748414592': "وخارزم",
    '778253364357513': "وبملت",
    '2400322364771558': "شستا",
    '7745894403636165': "شپنا",
    '65883838195688438': "خودرو",
    '48511238766369097': "دانا",
    '67988012428906654': "دارو",
    '15949743338644220': "ساروم"
}


import joblib

mongo_client_news = MongoClient('mongodb://localhost:27017/')
db_news = mongo_client_news['telegram_data']
collection_news = db_news['messages']

mongo_client_metrics = MongoClient('mongodb://localhost:27017/')
db_metrics = mongo_client_metrics['tse']
collection_metrics = db_metrics['IsinPrices_live']
MODELS_DIR = r"D:\project\Predict_stock_price\models"


def load_model(stock_symbol):
    model_file = os.path.join(MODELS_DIR, f"{stock_symbol}.pkl")
    if not os.path.exists(model_file):
        return None
    return joblib.load(model_file)


def process_data():
    start_time = datetime.now() - timedelta(days=1)
    start_time = start_time.replace(hour=12, minute=30, second=0, microsecond=0)
    end_time = datetime.now()

    pipeline_news = [
        {
            "$match": {
                "date": {"$gte": start_time, "$lt": end_time},
                "$or": [
                    {"positive": {"$gt": 0.003}},
                    {"negative": {"$gt": 0.003}},
                    {"neutral": {"$gt": 0.98}}
                ]
            }
        },
        {
            "$group": {
                "_id": "$channel",
                "positive_sentiment_count": {"$sum": {"$cond": [{"$gt": ["$positive", 0.003]}, 1, 0]}},
                "negative_sentiment_count": {"$sum": {"$cond": [{"$gt": ["$negative", 0.003]}, 1, 0]}},
                "neutral_sentiment_count": {"$sum": {"$cond": [{"$gt": ["$neutral", 0.98]}, 1, 0]}},
                "total_messages": {"$sum": 1}
            }
        }
    ]

    news_results = list(collection_news.aggregate(pipeline_news))

    ins_codes_prediction = {}
    for ins_code in list(ins_codes.keys()):
        data = list(collection_metrics.find({"ins_code": int(ins_code)}).sort('DEven', -1))
        latest_metric = data[-1]['total_transactions']
        previous_metric = data[-2]['total_transactions']
        change_total_transactions = (latest_metric - previous_metric) / previous_metric * 100

        metrics = {
            "change_total_transactions": change_total_transactions,
            "change_volume": (data[-1]['volume'] - data[-2]['volume']) / data[-1]['volume'] * 100,
            "change_index_value": (data[-1]['index_value'] - data[-2]['index_value']) / data[-1]['index_value'] * 100
        }
        channel_mapping = {'IranintlTV': 0, 'Saberin_ir': 1, 'Tasnimnews': 2, 'akharinkhabar': 3, 'akhbarefori': 4,
                           'bbcpersian': 5, 'farsna': 6, 'irZagrosNews': 7, 'khabarfarda_ir': 8, 'tweet_Khabari': 9}
        model = load_model(ins_code)
        predictions = []
        for news in news_results:
            channel_code = channel_mapping[news["_id"]]
            test_data = pd.DataFrame({
                "positive_sentiment_count": [news['positive_sentiment_count']],
                "negative_sentiment_count": [news['negative_sentiment_count']],
                "neutral_sentiment_count": [news['neutral_sentiment_count']],
                "channel_name_encoded": [channel_code],
                "change_total_transactions": [metrics['change_total_transactions']],
                "change_volume": [metrics['change_volume']],
                "change_index_value": [metrics['change_index_value']],
            })
            predictions.append(int(model.predict(test_data)[0]))

        ins_codes_prediction.update({ins_code: (sum(predictions) / len(predictions))})

    return ins_codes_prediction


# تابع پاسخ‌دهی به کاربر
def report(update: Update, context: CallbackContext) -> None:
    data = process_data()
    if not data:
        update.message.reply_text("⚠️ داده‌ای برای پردازش در بازه زمانی مشخص شده یافت نشد.")
        return

    range_res = {
        0: "📉 کاهش شدید",
        1: "📉 کاهش جزئی",
        2: "⚖️ بدون تغییر",
        3: "📈 افزایش جزئی",
        4: "📈 افزایش قابل توجه",
    }
    response = "📊 **گزارش پیش‌بینی تغییرات بازار سهام**\n\n"
    for ins_code, prediction in data.items():
        stock_name = ins_codes.get(ins_code, "نامشخص")
        response += f"   - {stock_name}: {range_res[int(prediction)]}\n"

    response += "\n🔹 این تغییرات بر اساس تحلیل‌های احتمالی ارائه شده‌اند و برای سه روزه آینده هستند."
    update.message.reply_text(response, parse_mode="Markdown")

def main():
    # توکن ربات خود را اینجا وارد کنید
    TELEGRAM_TOKEN = ''

    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # ثبت دستور `/report`
    dispatcher.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
