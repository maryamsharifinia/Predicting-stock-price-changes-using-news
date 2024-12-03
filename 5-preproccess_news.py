from pymongo import MongoClient
import pandas as pd
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["telegram_data"]
collections = db.list_collection_names()

db_price = client["tse"]
collection_price = db_price['IsinPrices']

market_close_time = datetime.strptime("12:30:00", "%H:%M:%S").time()
for collection in collections:
    coll = db[collection]

    data = list(coll.find({}))

    for i in data:

        original_date = i.get('date')

        if original_date:
            date_only = original_date.date().isoformat()
            time_only = datetime.combine(datetime(1900, 1, 1), original_date.time())
            hour = int(original_date.time().isoformat()[:2])

            coll.update_one(
                {"_id": i["_id"]},
                {
                    "$set": {
                        "date_only": date_only,
                        "time_only": time_only,
                        "hour":hour
                    }
                }
            )

    data = list(coll.find({}))



news_df = pd.read_csv(r"D:\project\final_project\combined_sentiment.csv")
price_df = pd.read_csv(r"D:\project\final_project\merged_file_stocks.csv")

news_df['date'] = pd.to_datetime(news_df['date'])
price_df['date'] = pd.to_datetime(price_df['date'])

distinct_dates = collection_price.distinct('date')

# مرتب‌سازی تاریخ‌ها
market_days = sorted(distinct_dates)

news_df['time'] = news_df['date'].dt.time
news_df['hour'] = news_df['date'].dt.hour
market_close_time = pd.to_datetime("12:30").time()
news_df_before_close = news_df[news_df['time'] <= market_close_time]
news_df_after_close = news_df[news_df['time'] > market_close_time]

news_df_after_close['date_only'] = news_df_after_close['date'].dt.date + pd.Timedelta(days=1)

# برای اخبار قبل از زمان بسته شدن تاریخ همان است
news_df_before_close['date_only'] = news_df_before_close['date'].dt.date
news_df = pd.concat([news_df_before_close, news_df_after_close])
news_df = news_df.sort_values(by=['date'])

market_days_date = []
for i in market_days:
    market_days_date.append(str(i.date()))


def get_next_market_day(current_date):
    max_attempts = 15
    attempts = 0
    # چک کردن تاریخ‌های بعدی
    while str(current_date) not in market_days_date and attempts < max_attempts:
        current_date += pd.Timedelta(days=1)
        attempts += 1
    return current_date if attempts < max_attempts else None


# تغییر تاریخ اخبار بعد از بسته شدن بازار به روز باز بعدی
news_df['date_only'] = news_df['date_only'].apply(get_next_market_day)
price_df['date_only'] = price_df['date'].dt.date


# تابع برای محاسبه تغییر سه روزه برای هر ردیف
def calculate_price_change_3d(row):
    current_date = row['date_1']
    count = 0
    sum_price_change = row['shift_1']
    future_dates = []

    # پیدا کردن دو تاریخ معاملاتی بعدی
    for i in range(1, 20):
        potential_date = current_date + pd.Timedelta(days=i)
        if potential_date in market_days:
            future_dates.append(potential_date)
            count += 1
        if count == 2:
            break

    # اضافه کردن قیمت‌های تغییر یافته بر اساس تاریخ‌های پیدا شده
    if len(future_dates) >= 1:
        if row['date_2'] == future_dates[0]:
            sum_price_change += row['shift_2']
        if len(future_dates) == 2:
            if row['date_2'] == future_dates[1]:
                sum_price_change += row['shift_2']
            if row['date_3'] == future_dates[1]:
                sum_price_change += row['shift_3']

    return sum_price_change


# تابع اصلی برای محاسبه تغییر سه روزه معاملاتی برای هر نماد
def calculate_3d_change(group):
    # فیلتر کردن روزهای معاملاتی بعدی
    group['shift_1'] = group['price_change']
    group['shift_2'] = group['price_change'].shift(-1)
    group['shift_3'] = group['price_change'].shift(-2)

    # بررسی اینکه تاریخ‌های جابجا شده باید در فاصله سه روزه باشند
    group['date_1'] = group['date']
    group['date_2'] = group['date'].shift(-1)
    group['date_3'] = group['date'].shift(-2)

    # استفاده از تابع جداگانه برای محاسبه تغییرات سه روزه
    group['price_change_3d'] = group.apply(calculate_price_change_3d, axis=1)

    # حذف ستون‌های کمکی
    group.drop(columns=['shift_1', 'shift_2', 'shift_3', 'date_1', 'date_2', 'date_3'], inplace=True)

    return group


# اعمال تابع به هر نماد
price_df = price_df.groupby('symbol', group_keys=False).apply(calculate_3d_change)
price_df['price_change_percent_3d'] = (price_df['price_change_3d']) / price_df['yesterday_price'] * 100
