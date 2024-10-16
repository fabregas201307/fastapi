import pandas as pd
from KalotayNative import AkaApi, corp_get_interest_rate_model, corp_bond_value
from KalotayNative import CorpBond as Bond
import csv

def t_1_settle_date(trade_date: str) -> str:
    result = (pd.to_datetime(trade_date) + pd.offsets.CustomBusinessDay(1)).strftime("%Y_%m_%d")
    return result

def add_call_schedule(call_schedule:str, trade_date:str, bond):
    call_schedule = call_schedule.split("|")
    if len(call_schedule) > 0:
        for call in call_schedule:
            if pd.to_datetime(call.split("@")[0], format="%m-%d-%Y") >= pd.to_datetime(trade_date):
                bond.SetCall(AkaApi.Date(int(call.split("@")[0][6:] + call.split("@")[0][:2] + call.split("@")[0][3:5]), float(call.split("@")[-1]))


def get_oas(cur_df: pd.DataFrame):
    """
    cur_df:  pandas dataframe with columns 
        cusip(could be fake), trade_date, price, maturity_date, coupon, first_coupon_date, courpon_freq,
        issue_date, oid_date, 

    """
    cur_price = cur_df["price"]
    if cur_price == "":
        return None
    else:
        cur_price = float(cur_price)

    cur_maturity_date = cur_df["maturity_date"]
    cur_df["settle_date"] = cur_df["trade_date"].apply(t_1_settle_date)
    cur_df["value_date"] = cur_df["settle_date"]

    ## overwrite value_date
    flag_1 = pd.to_datetime(cur_df["settle_date"]) < pd.to_datetime(cur_df["issue_date"])
    cur_df.loc[flag_1, "value_date"] = cur_df.loc[flag_1, "issue_date"]
    cur_df.loc[flag_1, "settle_date"] = cur_df.loc[flag_1, "issue_date"]

    flag_2 = pd.to_datetime(cur_df["issue_date"]) <= pd.to_datetime(cur_df["oid_date"])
    cur_df.loc[flag_2, "issue_date"] = cur_df.loc[flag_2, "oid_date"]

    cur_df["value_date"] = pd.to_datetime(cur_df["value_date"]).dt.strftime("%Y_%m_%d")
    cur_df["settle_date"] = pd.to_datetime(cur_df["settle_date"]).dt.strftime("%Y_%m_%d")

    # create AkaApi bonds
    cur_df["akaapi_bond"] = cur_df.apply(lambda row:
                                         AkaApi.Bond(
                                             row["cusip"],
                                             AkaApi.Date(int((str(row["issue_date"].year) + str(row["issue_date"].month).zfill(2) + str(row["issue_date"].day).zfill(2)))),
                                             AkaApi.Date(int((str(row["maturity_date"].year) + str(row["maturity_date"].month).zfill(2) + str(row["maturity_date"].day).zfill(2)))),
                                             row["cpn"]
                                         ), axis=1)
    
    data = cur_df.loc[~(cur_df["treat_as_preref"]) & (cur_df["callable"]=="Y") & (cur_df["call_schedule"].isnull())].copy()
    flag_3 = (data["treat_as_preref"] & (data["callable"]=="Y"))
    flag_4 = (data["treat_as_preref"] & (data["callable"]=="Y") & (data["call_status_for_defeased_bond"].isna())  \
              | ~data["call_status_for_defeased_bond"].str.contains("ORIGINAL CALL PROVISIONS WAIVED", na=False))  \
              & (data["call_freq"] == "T") & (data["zero_cpn"] == "N")
    flag_5 = (data["treat_as_preref"] & (data["callable"]=="Y") & (data["call_status_for_defeased_bond"].isna())  \
              | ~data["call_status_for_defeased_bond"].str.contains("ORIGINAL CALL PROVISIONS WAIVED", na=False))  \
              & (~((data["call_freq"] == "T") & (data["zero_cpn"] == "N")))      
    flag_6 = (data["treat_as_preref"] & (data["callable"]=="Y") & (data["call_status_for_defeased_bond"].isna())  \
              | ~data["call_status_for_defeased_bond"].str.contains("ORIGINAL CALL PROVISIONS WAIVED", na=False))

    data.loc[flag_3].apply(lambda row: add_call_schedule(row["call_schedule"], row["trade_date"], row["akaapi_bond"]), axis=1)
    data.loc[flag_4].apply(lambda row: row["akaapi_bond"].SetCallAmerican(True), axis=1)
    data.loc[flag_5].apply(lambda row: row["akaapi_bond"].SetCallAmerican(False), axis=1)
    data.loc[flag_6].apply(lambda row: row["akaapi_bond"].SetNoticePeriod(row["call_days_notice"]), axis=1)


