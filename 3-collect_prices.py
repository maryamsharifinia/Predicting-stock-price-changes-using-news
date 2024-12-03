import json
import time
from datetime import datetime
from persiantools.jdatetime import JalaliDate

import pymongo
from elasticsearch import Elasticsearch
from zeep import Client

from normalization.normalization import Normalizer

STOP_COUNT = 5000
DAY_REFRESH_RATE = 600
NIGHT_REFRESH_RATE = 3600
MAX_SIZE = -1  # -1 if you want all

from datetime import datetime, timedelta
import calendar


def get_non_holiday_dates_from_today():
    end_date = datetime.today()

    start_date = end_date - timedelta(days=365*10)

    non_holiday_dates = []

    current_date = start_date
    while current_date <= end_date:
        if calendar.weekday(current_date.year, current_date.month, current_date.day) != 3 and calendar.weekday(
                current_date.year, current_date.month, current_date.day) != 4:
            non_holiday_dates.append(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)

    return non_holiday_dates


class GetStockWorker:
    def __init__(self, user_tse, password_tse):

        self.user_tse = user_tse
        self.password_tse = password_tse
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    def loop(self):

        while True:

            try:
                self.run()
                time.sleep(24 * 60 * 60)

            except:
                time.sleep(3600)

    def run(self):
        # گرفتن تاریخ‌ها
        dates = get_non_holiday_dates_from_today()
        for date in reversed(dates):

            tse_dat = self.get_tse_data(date)
            tse_dat_index = self.get_tse_data_index(date)
            index = {}
            for i in tse_dat_index:
                api_response = i['TseIndexB2']

                gregorian_date = datetime.strptime(str(api_response["DEven"]), "%Y%m%d")

                formatted_gregorian_date = gregorian_date.strftime("%Y-%m-%d")

                jalali_date = JalaliDate.to_jalali(gregorian_date)
                stock_data = {
                    "_id": str(api_response["InsCode"]) + "_" + str(api_response["DEven"]),  # استفاده از dot notation
                    "date": formatted_gregorian_date,  # تاریخ
                    "jalali_date": str(jalali_date),  # تاریخ جلالی
                    "trade_time": float(api_response["HEven"]),  # ساعت
                    "index_value": float(api_response["XNivInuClMresIbs"]),  # مقدار شاخص
                    "index_time": float(api_response["HNivInuClMresIbs"]),  # زمان شاخص
                    "first_index_value": float(api_response["XNivInuPrDifMresIbs"]),  # مقدار اولين انتشار شاخص
                    "first_index_time": float(api_response["HNivInuPrDifMresIbs"]),  # زمان اولين انتشار شاخص
                    "peak_index_value": float(api_response["XNivInuPhMresIbs"]),  # بيشترين شاخص در طول روز
                    "peak_index_time": float(api_response["HNivInuPhMresIbs"]),  # زمان بيشترين شاخص در طول روز
                    "peak_index_change_percent": float(api_response["XVarIdxPhJClV"]),
                    # درصد تغييرات بيشترين مقدار شاخص
                    "lowest_index_value": float(api_response["XNivInuPbMresIbs"]),  # كمترين شاخص در طول روز
                    "lowest_index_time": float(api_response["HNivInuPbMresIbs"]),  # زمان كمترين شاخص
                    "lowest_index_change_percent": float(api_response["XVarIdxPbJClV"]),
                    # درصد تغييرات كمترين مقدار شاخص
                    "decreasing_symbol_percent": float(api_response["XVarDrInuClV"]),  # درصد تغيير نمادهاي كاهش يافته
                    "net_dividend_value": float(api_response["QDvdNetJValIbs"]),  # مقدار سود خالص پرداختي
                    "capital_yesterday": float(api_response["QCapBsRfVIbs"]),  # مقدار سرمايه ديروز شاخص
                    "adjustment_coefficient": float(api_response["KAjCapBzIbs"]),  # ضريب تنظيم براي سرمايه پايه شاخص
                    "net_cash_return_index_value": float(api_response["XNivIrteNetClIbs"])  # مقدار شاخص بازده خالص نقدي
                }
                index.update({str(api_response["InsCode"]): float(stock_data['index_value'])})

            for i in tse_dat:
                api_response = i['TradeSelectedDate']

                normalizer = Normalizer()
                api_response["LVal18AFC"] = normalizer.normalize_str(api_response["LVal18AFC"])
                api_response['LVal30'] = normalizer.normalize_str(api_response['LVal30'])

                gregorian_date = datetime.strptime(str(api_response["DEven"]), "%Y%m%d")

                formatted_gregorian_date = gregorian_date.strftime("%Y-%m-%d")

                jalali_date = JalaliDate.to_jalali(gregorian_date)
                stock_data = {
                    "_id": str(api_response["InsCode"]) + "_" + str(api_response["DEven"]),  # نماد
                    "symbol": api_response["LVal18AFC"],  # نماد
                    "DEven": api_response["DEven"],  # تاريخ
                    "date": formatted_gregorian_date,  # تاريخ
                    "jalali_date": str(jalali_date),  # تاريخ
                    "total_transactions": float(api_response["ZTotTran"]),  # تعداد معاملات
                    "volume": float(api_response["QTotTran5J"]),  # حجم - تعداد سهام معامله شده
                    "total_value": float(api_response["QTotCap"]),  # ارزش معاملات
                    "ins_code": api_response["InsCode"],  # کد نماد
                    "description": api_response["LVal30"],  # توضيح
                    "closing_price": float(api_response["PClosing"]),  # قيمت نهايي
                    "last_price": float(api_response["PDrCotVal"]),  # آخرين قيمت معامله شده
                    "price_change": float(api_response["PriceChange"]),  # تغيير قيمت
                    "min_price": float(api_response["PriceMin"]),  # حداقل قيمت
                    "max_price": float(api_response["PriceMax"]),  # حداکثر قيمت
                    "first_price": float(api_response["PriceFirst"]),  # قيمت اولين معامله
                    "yesterday_price": float(api_response["PriceYesterday"]),  # قيمت ديروز
                    "index_value": index['32097828799138957']
                }
                mydb_tse = self.myclient["tse"]
                IsinPrices = mydb_tse['IsinPrices_live']
                if IsinPrices.count_documents(
                        {'ins_code': stock_data["ins_code"], 'jalali_date': stock_data["jalali_date"]}) != 0:
                    continue
                try:
                    IsinPrices.insert_one(stock_data)
                except:
                    print(stock_data)
                    continue

            print(str(dates.index(date)) + " :  " + str(date))


    def get_tse_data(self, SelDate):
        tse_client = Client("http://service.tsetmc.com/WebService/TsePublicV2.asmx?WSDL")
        result = []
        for i in [1, 2, 3, 4, 5, 6, 7]:
            try:
                tse_request_body = {
                    "UserName": self.user_tse,
                    "Password": self.password_tse,
                    "Flow": i,
                    "SelDate": SelDate
                }

                res = tse_client.service['TradeOneDay'](**tse_request_body)
                result += res._value_1._value_1
            except:
                continue
        return result

    def get_tse_data_index(self, SelDate):
        tse_client = Client("http://service.tsetmc.com/WebService/TsePublicV2.asmx?WSDL")
        result = []
        try:
            tse_request_body = {
                "UserName": self.user_tse,
                "Password": self.password_tse,
                "DEven": SelDate
            }

            res = tse_client.service['IndexB2'](**tse_request_body)
            result += res._value_1._value_1
        except:
            return result
        return result


def get_instrument_type(isin):
    if isin[0:4] == 'IRO6' or isin[0:7] == 'IRO3MSZ':
        return "MORTGAGE"
    elif isin[0:3] == 'IRT':
        return "ETF"
    elif isin[0:3] == 'IRB':
        return "BOND"
    elif isin[0:4] == 'IRO9' or isin[0:4] == 'IROF' or isin[0:3] == 'IRS':
        return "OPTION"
    elif isin[0:4] == 'IRO3' or isin[0:4] == 'IRO7' or isin[0:4] == 'IRO5' \
            or isin[0:4] == 'IRR3' or isin[0:4] == 'IRR7' or isin[0:4] == 'IRR5' or isin[0:4] == 'IROT':
        return "IFB"
    elif isin[0:4] == 'IRO1' or isin[0:4] == 'IRR1':
        return "TSE"
    elif isin[0:3] == 'IRK1A' or isin[0:4] == 'IRK1H' or isin[0:4] == 'IRK1K' or isin[0:4] == 'IRK1M' \
            or isin[0:4] == 'IRK1P' or isin[0:4] == 'IRK1T':
        return "FUTURE"
    elif isin[0:3] == 'IRE':
        return "ENERGY"
    else:
        return None


if __name__ == "__main__":
    while True:
        try:

            user_tse = ""
            password_tse = ""

            worker = GetStockWorker(
                user_tse=user_tse,
                password_tse=password_tse
            )

            worker.loop()
        except Exception as e:
            # tb.print_tb(e.__traceback__)
            time.sleep(10)
            # print("Trying to restart the order schedule worker...")
