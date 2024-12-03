import random

import time
from datetime import datetime
from persiantools.jdatetime import JalaliDate

import pymongo
from zeep import Client

from normalization.normalization import Normalizer

STOP_COUNT = 5000
DAY_REFRESH_RATE = 600
NIGHT_REFRESH_RATE = 3600
MAX_SIZE = -1  # -1 if you want all


class GetStockWorker:
    def __init__(self, user_tse, password_tse):

        self.user_tse = user_tse
        self.password_tse = password_tse
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = myclient["tse"]

    def loop(self):

        while True:

            try:
                self.run()
                print("done")
                time.sleep(24 * 60 * 60)

            except:
                time.sleep(3600)

    def run(self):
        tse_dat = self.get_tse_data("AdjPrice")

        for i in tse_dat:
            stock_summary = i['TseAdjPrice']

            gregorian_date = datetime.strptime(str(stock_summary["DEven"]), "%Y%m%d")

            formatted_gregorian_date = gregorian_date.strftime("%Y-%m-%d")

            jalali_date = JalaliDate.to_jalali(gregorian_date)

            stock_summary = {
                'DEven': stock_summary["DEven"],
                "date": formatted_gregorian_date,
                "jalali_date": str(jalali_date),
                'closing_price': float(stock_summary["PClosing"]),
                'before_closing_price': float(stock_summary["PClosingNoAdj"]),
                "ins_code": stock_summary['InsCode'],
                "_id":
                    str(stock_summary['InsCode']) + "_" + str(
                        stock_summary["DEven"]) + "_" + str(random.randint(1111, 9111)),
            }
            AdjPrice = self.mydb['AdjPrice']
            try:
                AdjPrice.insert_one(stock_summary)
            except:
                continue
        tse_dat = self.get_tse_data("ShareChange")

        for i in tse_dat:
            stock_summary = i['TseShare']

            normalizer = Normalizer()
            stock_summary["LVal18AFC"] = normalizer.normalize_str(stock_summary["LVal18AFC"])
            stock_summary['LVal30'] = normalizer.normalize_str(stock_summary['LVal30'])

            gregorian_date = datetime.strptime(str(stock_summary["DEven"]), "%Y%m%d")

            formatted_gregorian_date = gregorian_date.strftime("%Y-%m-%d")

            jalali_date = JalaliDate.to_jalali(gregorian_date)

            stock_summary = {
                'DEven': stock_summary["DEven"],
                "date": formatted_gregorian_date,  # تاريخ
                "jalali_date": str(jalali_date),  # تاريخ
                'NumberOfShareOld': int(stock_summary["NumberOfShareOld"]),
                'NumberOfShareNew': int(stock_summary["NumberOfShareNew"]),

                'full_name': stock_summary["LVal30"],
                'short_name': stock_summary["LVal18AFC"],

                "ins_code": stock_summary['InsCode'],
                "_id": str(stock_summary['InsCode']) + "_" + str(stock_summary["DEven"]) + "_" + str(
                    random.randint(1111, 9111))

            }
            ShareChange = self.mydb['ShareChange']
            try:
                ShareChange.insert_one(stock_summary)
            except:
                continue

    def get_tse_data(self, _type):
        tse_client = Client("http://service.tsetmc.com/WebService/TsePublicV2.asmx?WSDL")
        result = []
        for i in [1, 2, 3, 4, 5, 6, 7]:
            try:
                tse_request_body = {
                    "UserName": self.user_tse,
                    "Password": self.password_tse,
                    "Flow": i
                }

                res = tse_client.service[_type](**tse_request_body)
                result += res._value_1._value_1
            except:
                continue
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
            normalizer = Normalizer()
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
