from binascii import unhexlify
from binascii import hexlify
import pandas as pd

from enum import Enum


class Scenario(Enum):
    default = 1


class Normalizer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, scenario=Scenario.default):
        self.remove_list = []
        self.replace_dict = {}
        normalization_remove_loc = f'normalization/configs/{scenario.name}/normalization-remove.tbl'
        normalization_replace_loc = f'normalization/configs/{scenario.name}/normalization-replace.tbl'

        for line in open(normalization_remove_loc):
            # do not process commented lines
            if line.strip().startswith('#'):
                continue
            line = line.strip().replace("<0x", "").replace(">", "")
            if divmod(len(line), 2)[1] != 0:
                line = "0" + line
            if divmod(len(line), 4)[1] != 0:
                line = "00" + line
            self.remove_list.append(unhexlify(line).decode('utf-16-be'))

        for line in open(normalization_replace_loc):
            # do not process commented lines
            if line.strip().startswith('#'):
                continue
            kv = line.strip().split("\t")
            k = kv[0]
            v = kv[1]

            k = k.strip().replace("<0x", "").replace(">", "")
            if divmod(len(k), 2)[1] != 0:
                k = "0" + k
            if divmod(len(k), 4)[1] != 0:
                k = "00" + k
            k = (unhexlify(k).decode('utf-16-be'))

            v = v.strip().replace("<0x", "").replace(">", "")
            if divmod(len(v), 2)[1] != 0:
                v = "0" + v
            if divmod(len(v), 4)[1] != 0:
                v = "00" + v
            v = (unhexlify(v).decode('utf-16-be'))

            self.replace_dict[k] = v

    def normalize_str(self, s: str, remove_whitespace=False):
        if not s:
            return ""
        out = ""
        for char in s:
            if char in self.remove_list:
                continue
            elif char in self.replace_dict:
                out = out + self.replace_dict[char]
            else:
                out = out + char
        if remove_whitespace:
            out = out.replace(' ', '').replace('\t', '')
        return out

    def normalize_series(self, ds: pd.Series, remove_whitespace=False):
        return ds.apply(lambda x: self.normalize_str(x, remove_whitespace) if type(x) == str else x)

    def normalize_dataframe(self, df: pd.DataFrame, remove_whitespace=False):
        return df.applymap(lambda x: self.normalize_str(x, remove_whitespace) if type(x) == str else x)

    @staticmethod
    def char_to_hex(ch):
        return "<0x" + hexlify(ch.encode('utf-16-be')).decode('utf-8').upper() + ">"

    @staticmethod
    def str_to_hex(s):
        result = {}
        for ch in s:
            result[ch] = Normalizer.char_to_hex(ch)
        return result
