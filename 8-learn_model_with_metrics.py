import os
import joblib
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier, GradientBoostingClassifier
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVR, SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils import shuffle
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.neural_network import MLPClassifier
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

news_df = pd.read_csv(r"D:\project\final_project\final_news.csv")
price_df = pd.read_csv(r"D:\project\final_project\final_prices_with_index_value.csv")

news_df['neutral_sentiment'] = news_df['sentiment'].apply(
    lambda x: float(x.split(" ")[0][1:]) * 100 if len(x.split(" ")) > 0 else 0
)

news_df['positive_sentiment'] = news_df['sentiment'].apply(
    lambda x: (lambda y: float(y) * 100 if y.replace('.', '', 1).isdigit() else 0)(x.split(" ")[1]) if len(
        x.split(" ")) > 1 else 0
)

news_df['negative_sentiment'] = news_df['sentiment'].apply(
    lambda x: (lambda y: float(y[:-1]) * 100 if y[:-1].replace('.', '', 1).isdigit() else 0)(x.split(" ")[2]) if len(
        x.split(" ")) > 2 else 0
)

price_df['price_label'] = pd.cut(
    price_df['price_change_percent_3d'],
    bins=[-float('inf'), -5, -0.5, 0.5, 5, float('inf')],
    labels=['HighDecrease', 'LowDecrease', 'NoChange', 'LowIncrease', 'HighIncrease']
)

import os
import pandas as pd
import re
from openpyxl import Workbook


def save_model_and_results(model, accuracy, ins_code, results, stock_symbol, mode):
    # پوشه مقصد
    output_dir = r"D:\project\Predict_stock_price\results"
    os.makedirs(output_dir, exist_ok=True)

    # پاک‌سازی نام فایل
    safe_stock_symbol = re.sub(r'[^\w\s]', '_', stock_symbol)
    output_file = os.path.join(output_dir, f"results_{safe_stock_symbol}1.xlsx")

    # اگر فایل اکسل وجود ندارد، آن را ایجاد کنید
    if not os.path.exists(output_file):
        wb = Workbook()
        wb.save(output_file)

    # اضافه کردن داده‌ها به اکسل
    with pd.ExcelWriter(output_file, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
        sheet_name = f"Mode_{mode}"
        results.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Results for mode {mode} saved in sheet '{sheet_name}' of {output_file}")


def train_models(X_train, y_train, X_test, y_test, stock_symbol):
    """
    آموزش مدل‌ها و انتخاب بهترین مدل
    """
    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Support Vector Machine (SVM)": SVC(),
        "K-Nearest Neighbors (KNN)": KNeighborsClassifier(),
        "MLPClassifier": MLPClassifier(hidden_layer_sizes=(50, 50), max_iter=1000, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(),
    }

    best_model, best_accuracy = None, 0.0
    results = []

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        results.append({
            "Model": model_name,
            "Accuracy": accuracy,
            "Precision": report["weighted avg"]["precision"],
            "Recall": report["weighted avg"]["recall"],
            "F1-Score": report["weighted avg"]["f1-score"]
        })
        print({
            "Model": model_name,
            "Accuracy": accuracy,
            "Precision": report["weighted avg"]["precision"],
            "Recall": report["weighted avg"]["recall"],
            "F1-Score": report["weighted avg"]["f1-score"]
        })
        if accuracy > best_accuracy:
            best_model, best_accuracy = model, accuracy

    results_df = pd.DataFrame(results)
    return best_model, best_accuracy, results_df


# مثال استفاده از توابع بهینه‌شده در یکی از متدها
def train_and_predict_for_stock(stock_symbol, ins_code, features, news=True, mode="1"):
    global price_df
    price_df = price_df.sort_values(by='date_only', ascending=True).reset_index(drop=True)

    # فیلتر کردن دیتافریم برای سهام مورد نظر
    stock_df = price_df[price_df['symbol'] == stock_symbol].copy()

    if news:
        stock_df = pd.merge(news_df, stock_df, on='date_only')
        # فیلتر کردن و مرتب‌سازی نهایی
        stock_df = stock_df[stock_df['symbol'] == stock_symbol].sort_values(by=['date_only', 'date_x'],
                                                                            ascending=[True, True])
        daily_summary = stock_df.groupby('date_only').agg({
            'total_transactions': 'first',
            'volume': 'first',
            'total_value': 'first',
            'index_value': 'first',
        }).reset_index()

    else:
        # فیلتر کردن و مرتب‌سازی نهایی
        stock_df = stock_df[stock_df['symbol'] == stock_symbol].sort_values(by=['date_only'], ascending=[True])
        daily_summary = stock_df.groupby('date_only').agg({
            'total_transactions': 'first',
            'volume': 'first',
            'total_value': 'first',
            'index_value': 'first',
        }).reset_index()

    if daily_summary.count()["date_only"] < 10:
        print(f"سهم {stock_symbol} داده کافی برای آموزش ندارد (کلاس‌های کافی موجود نیستند).")
        return None
    # اضافه کردن ستون‌های روز قبل به daily_summary
    daily_summary['previous_total_transactions'] = daily_summary['total_transactions'].shift(1)
    daily_summary['previous_volume'] = daily_summary['volume'].shift(1)
    daily_summary['previous_total_value'] = daily_summary['total_value'].shift(1)
    daily_summary['previous_index_value'] = daily_summary['index_value'].shift(1)

    daily_summary['previous_total_transactions2'] = daily_summary['total_transactions'].shift(2)
    daily_summary['previous_volume2'] = daily_summary['volume'].shift(2)
    daily_summary['previous_total_value2'] = daily_summary['total_value'].shift(2)
    daily_summary['previous_index_value2'] = daily_summary['index_value'].shift(2)

    daily_summary['change_total_transactions'] = (daily_summary['previous_total_transactions'] - daily_summary[
        'previous_total_transactions2']) / daily_summary['previous_total_transactions2'] * 100

    daily_summary['change_volume'] = (daily_summary['previous_volume'] - daily_summary[
        'previous_volume2']) / daily_summary['previous_volume2'] * 100

    daily_summary['change_total_value'] = (daily_summary['previous_total_value'] - daily_summary[
        'previous_total_value2']) / daily_summary['previous_total_value2'] * 100

    daily_summary['change_index_value'] = (daily_summary['index_value'] - daily_summary[
        'previous_index_value2']) / daily_summary['previous_index_value2'] * 100

    stock_df = stock_df.merge(daily_summary[
                                  ['date_only', 'change_total_transactions', 'change_volume', "change_total_value",
                                   "change_index_value"]], on='date_only', how='left')

    stock_df.dropna(subset=['change_total_transactions', 'change_volume', 'change_index_value'], inplace=True)

    if news:
        channel_mapping = {'IranintlTV': 0, 'Saberin_ir': 1, 'Tasnimnews': 2, 'akharinkhabar': 3, 'akhbarefori': 4,
                           'bbcpersian': 5, 'farsna': 6, 'irZagrosNews': 7, 'khabarfarda_ir': 8, 'tweet_Khabari': 9}

        stock_df['channel_name_encoded'] = stock_df['channel_name'].map(channel_mapping)
        # stock_df = stock_df[stock_df["neutral_sentiment"] < 95]
        # stock_df = stock_df.dropna(subset=['positive_sentiment'])

        positive_filter = stock_df['positive_sentiment'] > 0.3
        negative_filter = stock_df['negative_sentiment'] > 0.3
        neutral_filter = stock_df['neutral_sentiment'] > 98

        stock_df = (
            stock_df.assign(
                positive_sentiment_count=positive_filter.astype(int),
                negative_sentiment_count=negative_filter.astype(int),
                neutral_sentiment_count=neutral_filter.astype(int)
            )
                .groupby(['channel_name_encoded', 'date_only'], as_index=False)
                .agg({
                'positive_sentiment_count': 'sum',
                'negative_sentiment_count': 'sum',
                'neutral_sentiment_count': 'sum',
                'change_total_transactions': 'first',
                'change_volume': 'first',
                'change_index_value': 'first',
                'price_label': 'first',
                "hour": "first"
            })
        ).sort_values(by=['date_only'], ascending=[True])

    if stock_df.shape[0] < 10:
        print(f"سهم {stock_symbol} داده کافی برای آموزش ندارد.")
        return None

    # آماده‌سازی ویژگی‌ها و برچسب‌ها

    stock_df = stock_df.dropna(subset=['change_total_transactions'])

    X = stock_df[features]
    y = stock_df['price_label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train)
    y_test = label_encoder.transform(y_test)

    best_model, best_accuracy, results_df = train_models(X_train, y_train, X_test, y_test, stock_symbol)
    save_model_and_results(best_model, best_accuracy, ins_code, results_df, stock_symbol, mode)
    return best_model


stock_symbols = {
    "فولاد": "46348559193224090",
    "پارس": '6110133418282108',
    "کگل": '35700344742885862',
    "وخارزم": '7395271748414592',
    "وبملت": '778253364357513',
    "شستا": '2400322364771558',
    "شپنا": '7745894403636165',
    "خودرو": '65883838195688438',
    "دانا": '48511238766369097',
    "دارو": '67988012428906654',
    "ساروم": '15949743338644220',
}
predictors = {}
modes = ["News_Only", "Metrics_Only", "News_And_Metrics", ]
for stock in list(stock_symbols.keys()):
    ins_code = stock_symbols[stock].split("_")[0]

    # حالت 1: فقط اخبار
    train_and_predict_for_stock(stock, ins_code, ['positive_sentiment_count',
                                                  'negative_sentiment_count',
                                                  'neutral_sentiment_count',
                                                  'channel_name_encoded',
                                                  ], mode=modes[0])
    #
    # # حالت 2: فقط داده‌های متریک
    train_and_predict_for_stock(stock, ins_code, [
        "change_total_transactions",
        "change_volume",
        "change_index_value",
    ], news=False, mode=modes[1])

    # حالت 3: اخبار و متریک با `split_day = False`
    best_model = train_and_predict_for_stock(stock, ins_code, ['positive_sentiment_count',
                                                               'negative_sentiment_count',
                                                               'neutral_sentiment_count',
                                                               'channel_name_encoded',
                                                               "change_total_transactions",
                                                               "change_volume",
                                                               "change_index_value",
                                                               ], mode=modes[2])

    joblib.dump(best_model, os.path.join(r"D:\project\Predict_stock_price\models", f"{ins_code}.pkl"))
