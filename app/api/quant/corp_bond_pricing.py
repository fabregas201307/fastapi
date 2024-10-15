import pandas as pd
from KalotayNative import AkaApi, corp_get_interest_rate_model, corp_bond_value
from KalotayNative import CorpBond as Bond
import csv

def get_oas(cur_df: pd.DataFrame):
    """
    cur_df:  pandas dataframe with columns 
        cusip(could be fake), trade_date, price, maturity_date, coupon, first_coupon_date, courpon_freq,

    """
    cur_price = cur_df["price"]
    if cur_price == "":
        return None
    else:
        cur_price = float(cur_price)

    cur_maturity_date = cur_df["maturity_date"]
