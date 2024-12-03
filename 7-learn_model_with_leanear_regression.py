import matplotlib
from pymongo import MongoClient

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import xgboost as xgb

# Define your model options in a dictionary
models = {
    "Linear Regression": LinearRegression(),
    "Logistic Regression": LogisticRegression(),
    "Support Vector Machine (SVM)": SVR(),
    "K-Nearest Neighbors (KNN)": KNeighborsRegressor(),
    "MLP (Neural Network)": MLPRegressor(hidden_layer_sizes=(50, 50), max_iter=1000, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(),
}

client = MongoClient('mongodb://localhost:27017/')
db = client['tse']
price_collection = db['IsinPrices']

news_df = pd.read_csv(r"D:\project\final_project\final_news.csv")
# price_df = pd.read_csv("final_prices_with_index_value_updated.csv")

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


def draw_plot(stock_symbol, test_date, predict, original):
    plt.figure(figsize=(12, 6))
    plt.plot(pd.DataFrame(test_date, columns=['date'])['date'],
             pd.DataFrame(original, columns=['original'])['original'], label='Actual Closing Price (Test)',
             color='blue')
    plt.plot(pd.DataFrame(test_date, columns=['date'])['date'],
             pd.DataFrame(predict, columns=['predict'])['predict'],
             label='Predicted Closing Price (Test)', color='red')
    plt.xlabel(' Date')
    plt.ylabel('Closing Price')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.title(f'{stock_symbol}')
    plt.savefig(f'{stock_symbol}.png')
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.plot(pd.DataFrame(test_date[-30:], columns=['date'])['date'],
             pd.DataFrame(original[-30:], columns=['original'])['original'], label='Actual Closing Price (Test)',
             color='blue')
    plt.plot(pd.DataFrame(test_date[-30:], columns=['date'])['date'],
             pd.DataFrame(predict[-30:], columns=['predict'])['predict'],
             label='Predicted Closing Price (Test)', color='red')
    plt.xlabel(' Date')
    plt.ylabel('Closing Price')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.title(f'Last month chart')
    plt.savefig(f'{stock_symbol}_last_month.png')
    plt.close()


def train_and_predict_for_stock(stock_symbol):
    documents_with_index_value = price_collection.find({"symbol": stock_symbol})
    price_df = pd.DataFrame(list(documents_with_index_value))
    price_df.rename(columns={'date': 'date_only'}, inplace=True)
    price_df = price_df.sort_values(by='date_only', ascending=True).reset_index(drop=True)
    price_df['price_change_percent'] = (price_df['price_change'] / price_df['yesterday_price']) * 100
    # فیلتر کردن دیتافریم برای سهام مورد نظر
    stock_df = price_df[price_df['symbol'] == stock_symbol].copy()

    stock_df = pd.merge(news_df, stock_df, on='date_only')
    # فیلتر کردن و مرتب‌سازی نهایی
    stock_df = stock_df[stock_df['symbol'] == stock_symbol].sort_values(by=['date_only', 'date'],
                                                                        ascending=[True, True])

    channel_mapping = {'IranintlTV': 0, 'Saberin_ir': 1, 'Tasnimnews': 2, 'akharinkhabar': 3, 'akhbarefori': 4,
                       'bbcpersian': 5, 'farsna': 6, 'irZagrosNews': 7, 'khabarfarda_ir': 8, 'tweet_Khabari': 9}

    stock_df['channel_name_encoded'] = stock_df['channel_name'].map(channel_mapping)

    positive_filter = stock_df['positive_sentiment'] > 0.3
    negative_filter = stock_df['negative_sentiment'] > 0.3
    neutral_filter = stock_df['neutral_sentiment'] > 98

    # ایجاد DataFrame جدید
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
            'new_closing_price': "first",
            'price_change_percent': "first",
        })
    ).sort_values(by=['date_only'], ascending=[True])

    # stock_df = stock_df[stock_df["neutral_sentiment"] < 95]

    # درصد یا مقدار
    price_change_type = 'price_change_percent'

    date_counts = stock_df['date_only'].value_counts().reset_index()
    date_counts.columns = ['date_only', 'count']
    test_date = sorted(list(date_counts['date_only']))
    test_data = []
    if len(test_date) < 10:
        print(f' دیتای سهم {stock_symbol}  کم است .')
        return

    for i in test_date:
        data_in_date = stock_df[stock_df["date_only"] == i]
        number_data_test = int(data_in_date.count().iloc[0] * 0.2)
        if number_data_test == 0:
            number_data_test = 1
        a = stock_df[stock_df["date_only"] == i]
        random_selection = a.sample(n=number_data_test)
        stock_df = stock_df.drop(random_selection.index)
        test_data.append(random_selection)

    stock_df_test = pd.concat(test_data)

    stock_df_train = stock_df.sample(frac=1).reset_index(drop=True)

    X_train = np.array(
        stock_df_train[['positive_sentiment_count', 'negative_sentiment_count', "neutral_sentiment_count",
                        "channel_name_encoded"]].values)
    y_train = stock_df_train[price_change_type]

    X_test = np.array(stock_df_test[['positive_sentiment_count', 'negative_sentiment_count', "neutral_sentiment_count",
                                     "channel_name_encoded"]].values)
    y_test = stock_df_test[price_change_type]


    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    # Loop through models and compare their performance
    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(
            f"Model: {model_name} => Stock: {stock_symbol} => Mean Squared Error: {mse:.2f} R^2 Score: {r2:.2f}")

        min_price = abs(stock_df['new_closing_price'].min())
        stock_df['new_closing_price'] += min_price
        original = []
        predict = []
        for i in range(0, len(test_date)):
            original.append(
                stock_df[stock_df["date_only"] == test_date[i]].iloc[0].to_dict()['new_closing_price'])
            if i != 0:
                befor_number_test += int(test_data[i].count().iloc[0])
            else:
                befor_number_test = 0

            after_number_test = int(test_data[i].count().iloc[0])
            prdict = y_pred[befor_number_test:befor_number_test + after_number_test]
            prdict_avg = sum(prdict) / len(prdict)
            yesterday_price = stock_df[stock_df["date_only"] == test_date[i - 1]].iloc[0].to_dict()['new_closing_price']

            prdict_avg = yesterday_price * prdict_avg / 100
            predict.append(yesterday_price + prdict_avg)

        draw_plot(stock_symbol + model_name, test_date[-365:], predict[-365:], original[-365:])

# اگر نیاز به آموزش کل مدل ها داشتید
# stock_symbols = list(dict.fromkeys(list(price_df['symbol'])))
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

for stock in stock_symbols:
    train_and_predict_for_stock(stock)
