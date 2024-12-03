import time
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
        mydb = myclient["tse"]
        self.es = mydb['symbol_info']

    def loop(self):
        while True:
            try:
                self.run()
                time.sleep(24 * 60 * 60)
            except:
                time.sleep(3600)

    def run(self):
        tse_dat = self.get_tse_data()
        res_tse = []
        insert_date = []
        for i in tse_dat:
            if get_instrument_type(str(i['TseInstruments']["InstrumentID"])) is None:
                continue
            stock_summary = i['TseInstruments']
            res_tse.append(stock_summary)
            if stock_summary["Valid"] == 1:
                active = True
            else:
                active = False
            normalizer = Normalizer()
            stock_summary['LSoc30'] = normalizer.normalize_str(stock_summary['LSoc30'])
            stock_summary["LVal18AFC"] = normalizer.normalize_str(stock_summary["LVal18AFC"])
            stock_summary['LVal30'] = normalizer.normalize_str(stock_summary['LVal30'])

            stock_summary = {'isin': stock_summary["InstrumentID"],
                             "ins_code": stock_summary['InsCode'],
                             "_id": str(stock_summary['InsCode']) + "_" + str(stock_summary["InstrumentID"]),
                             "sector_code": stock_summary["CSecVal"],
                             "sub_sector_code": stock_summary["CSoSecVal"],
                             'flow': stock_summary["Flow"],
                             'sector_name': stock_summary['LSoc30'],
                             'is_active': active,
                             'short_name': stock_summary["LVal18AFC"],
                             'stock_type': get_instrument_type(stock_summary["InstrumentID"]),
                             'full_name': stock_summary['LVal30'],

                             }

            if stock_summary is not None and active:
                insert_date.append(stock_summary)

        self.es.insert_many(insert_date)

    def get_tse_data(self):
        tse_client = Client("http://service.tsetmc.com/WebService/TsePublicV2.asmx?WSDL")
        result = []
        for i in [1, 2, 3, 4, 5, 6, 7]:
            try:
                tse_request_body = {
                    "UserName": self.user_tse,
                    "Password": self.password_tse,
                    "Flow": i
                }

                res = tse_client.service['Instrument'](**tse_request_body)
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

            time.sleep(10)
