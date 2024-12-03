import os
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
import matplotlib
from tqdm import tqdm

matplotlib.use('Agg')


def draw_chart(df, ):
    output_dir = 'output_tadil_charts'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.figure(figsize=(10, 6))

    collection_symbol = db['symbol_info']
    symbol_info = list(collection_symbol.find({"ins_code": ins_code}))
    plt.plot(df['jalali_date'], df['closing_price'], marker='o', linestyle='-', label=f'{ins_code}')

    plt.xlabel('Jalali Date')
    plt.ylabel('Closing Price')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    if len(symbol_info) > 0:
        plt.title(f'{symbol_info[0]["isin"]}')
        plt.savefig(
            os.path.join(output_dir, f'{symbol_info[0]["isin"] + "_" + symbol_info[0]["short_name"]}.png'))
        plt.close()
    else:
        plt.title(f'Closing Price vs Date for {ins_code}')
        plt.savefig(os.path.join(output_dir, f'{ins_code}_closing_price_chart.png'))
        plt.close()


client = MongoClient("mongodb://localhost:27017/")
db = client["tse"]
collection = db['IsinPrices']

ins_codes = collection.distinct('ins_code')
stock_symbols = {
    "فولاد": 46348559193224090,
    "پارس": 6110133418282108,
    "کگل": 35700344742885862,
    "وخارزم": 7395271748414592,
    "وبملت": 778253364357513,
    "شستا": 2400322364771558,
    "شپنا": 7745894403636165,
    "خودرو": 65883838195688438,
    "دانا": 48511238766369097,
    "دارو": 67988012428906654,
    "ساروم": 15949743338644220,
}
ins_codes = list(stock_symbols.keys())
for ins_code in tqdm(ins_codes):
    ins_code = stock_symbols[ins_code]
    collection_symbol = db['symbol_info']
    symbol_info = list(collection_symbol.find({"ins_code": ins_code}))
    if len(symbol_info) > 0:
        myquery = {"ins_code": ins_code}
        newvalues = {"$set": {"isin": symbol_info[0]['isin']}}
        collection.update_many(myquery, newvalues)

    market_data = list(collection.find({"ins_code": ins_code}).sort("DEven", 1))
    change_market_data = list(collection.find({"ins_code": ins_code}).sort("DEven", 1))

    if len(market_data) > 10:
        date_action = {}
        capital_increase_data = list(
            db["ShareChange"].find({"DEven": {"$gt": market_data[0]["DEven"]}, "ins_code": ins_code}).sort('DEven', 1))
        cash_dividend_data = list(
            db["AdjPrice"].find({"DEven": {"$gt": market_data[0]["DEven"]}, "ins_code": ins_code}).sort('DEven', 1))

        for i in capital_increase_data:
            date_action.update({i["DEven"]: []})

        for i in cash_dividend_data:
            date_action.update({i["DEven"]: []})

        for i in capital_increase_data:
            i.update({"type": "increase"})
            date_action[i["DEven"]].append(i)

        for i in cash_dividend_data:
            i.update({"type": "cash"})
            date_action[i["DEven"]].append(i)

        dates = sorted(list(date_action.keys()))

        for date in dates:
            for i in date_action[date]:
                if i["type"] == "increase":
                    old_shares = int(i['NumberOfShareOld'])
                    new_shares = int(i['NumberOfShareNew'])
                    if new_shares == 0:
                        print(str(i['ins_code']) + " " + i['short_name'])
                        continue
                    x = old_shares / new_shares
                    for item in change_market_data:
                        if item['DEven'] < date:
                            item['closing_price'] = item['closing_price'] * x
                if i["type"] == "cash":
                    old_price = int(i['before_closing_price'])
                    new_price = int(i['closing_price'])
                    x = old_price - new_price

                    for item in change_market_data:
                        if item['DEven'] < date:
                            item['closing_price'] = item['closing_price'] - x

        for item in change_market_data:
            try:
                myquery = {"_id": item["_id"]}
                newvalues = {"$set": {"new_closing_price": item['closing_price']}}
                collection.update_one(myquery, newvalues)
            except:
                print(item["symbol"])

        # در صورتی که نیاز دارید نمودار بکشید
        # change_df = pd.DataFrame(change_market_data)
        # draw_chart(change_df, )
    else:
        continue
