import pandas as pd
from KalotayNative import AkaApi, corp_get_interest_rate_model, corp_bond_value
from KalotayNative import CorpBond as Bond
import csv

def t_1_settle_date(trade_date: str) -> str:
    result = (pd.to_datetime(trade_date) + pd.offsets.CustomBusinessDay(1)).strftime("%Y_%m_%d")
    return result

def add_call_schedule(call_schedule:str, trade_date:pd.Series, bond):
    trade_date = trade_date.unique()[0]  ## temporarily assume only one unique trade_date
    call_schedule = call_schedule.split("|")
    if len(call_schedule) > 0:
        for call in call_schedule:
            if pd.to_datetime(call.split("@")[0], format="%m-%d-%Y") >= pd.to_datetime(trade_date):
                bond.SetCall(AkaApi.Date(int(call.split("@")[0][6:] + call.split("@")[0][:2] + call.split("@")[0][3:5])), float(call.split("@")[-1]))


def add_put_schedule(call_schedule:str, trade_date:pd.Series, bond):
    trade_date = trade_date.unique()[0]  ## temporarily assume only one unique trade_date
    call_schedule = call_schedule.split("|")
    if len(call_schedule) > 0:
        for call in call_schedule:
            if pd.to_datetime(call.split("@")[0], format="%m-%d-%Y") >= pd.to_datetime(trade_date):
                bond.SetCall(AkaApi.Date(int(call.split("@")[0][6:] + call.split("@")[0][:2] + call.split("@")[0][3:5])), float(call.split("@")[-1]))

def add_step_schedule(step_schedule:str, bond):
    trade_date = trade_date.unique()[0]  ## temporarily assume only one unique trade_date
    call_schedule = call_schedule.split("|")
    if len(call_schedule) > 0:
        for call in call_schedule:
            if pd.to_datetime(call.split("@")[0], format="%m-%d-%Y") >= pd.to_datetime(trade_date):
                bond.SetCall(AkaApi.Date(int(call.split("@")[0][6:] + call.split("@")[0][:2] + call.split("@")[0][3:5])), float(call.split("@")[-1]))


def get_oas(cur_df: pd.DataFrame):
    """
    cur_df:  pandas dataframe with columns 
        cusip(could be fake), trade_date, 
        price, maturity_date, coupon, first_coupon_date, courpon_freq,
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

    if len(data.loc[data["put_typ"] == "MANDATORY"]) > 0:
        flag_7 = (data["put_typ"] == "MANDATORY") & ((~data["nxt_put_px"].isna()) | (~(data["nxt_put_px"] == 0))) & (~data["put_schedule"].isna())
        flag_8 = (data["put_typ"] == "MANDATORY") & ((~data["nxt_put_px"].isna()) | (~(data["nxt_put_px"] == 0)))
        data.loc[flag_7, "nxt_put_px"] = data.loc[flag_8, "put_schedule"].str.split("@").str[1]
        data.loc[flag_7, "nxt_put_dt"] = data.loc[flag_8, "put_schedule"].str.split("@").str[0]

    flag_9 = ~((data["put_typ"]=="MANDATORY") & (data["nxt_put_px"].isnull() | (data["nxt_put_px"] == 0)))
    data = data.loc[flag_9]
    idx = list((~data["treat_as_preref"]) & (data["put_typ"] == "MANDATORY"))

    if len(data.loc[idx]) > 0:
        data.loc[idx, "maturity_date"] = data.loc[idx, "nxt_put_dt"]
        data.loc[idx, "akaapi_bond"] = data.loc[idx].apply(lambda row:
                                                           AkaApi.Bond(
                                                               row["cusip"],
                                                               AkaApi.Date(int((str(row["issue_date"].year) + str(row["issue_date"].month).zfill(2) + str(row["issue_date"].day).zfill(2)))),
                                                               AkaApi.Date(int((str(row["maturity_date"].year) + str(row["maturity_date"].month).zfill(2) + str(row["maturity_date"].day).zfill(2)))),
                                                               row["cpn"]
                                                           ), axis=1)
        data.loc[idx].apply(lambda row: row["akaapi_bond"].SetRedemptionPrice(float(row["nxt_put_px"])), axis=1)

    # process bonds that are completely called
    data = data.loc[~((data["completely_called"] == "Y") & (data["nxt_call_dt"].isna()))]
    idx = ((~data["treat_as_preref"]) & (data["completely_called"] == "Y"))

    if len(data.loc[idx]) > 0:
        data.loc[idx, "maturity_date"] = data.loc[idx, "nxt_call_dt"]
        data.loc[idx, "akaapi_bond"] = data.loc[idx].apply(lambda row:
                                                           AkaApi.Bond(
                                                               row["cusip"],
                                                               AkaApi.Date(int((str(row["issue_date"].year) + str(row["issue_date"].month).zfill(2) + str(row["issue_date"].day).zfill(2)))),
                                                               AkaApi.Date(int((str(row["maturity_date"].year) + str(row["maturity_date"].month).zfill(2) + str(row["maturity_date"].day).zfill(2)))),
                                                               row["cpn"]
                                                           ), axis=1)
        data.loc[idx & (data["completely_called"] == "Y")].apply(lambda row: add_call_schedule(row["call_schedule"], row["trade_date"], row["AKAAPI_BOND"]), axis=1)
        data.loc[idx].apply(lambda row: row["akaapi_bond"].SetRedemptionPrice(row["nxt_call_px"]), axis=1)

    # add call schedule if not reated as preref
    flag_10 = ~((~data["treat_as_preref"]) & (data["callable"] == "Y") & (data["completely_called"] == "N") & (data["call_schedule"].isnull()))
    flag_11 = ((~data["treat_as_preref"]) & (data["callable"] == "Y") & (data["completely_called"] == "N"))
    flag_12 = flag_11 & (data["call_freq"] == "T") & (data["zero_cpn"] == "N")
    flag_13 = flag_11 & (~data["call_freq"] == "T") & (data["zero_cpn"] == "N")

    data = data.loc[flag_10]
    data.loc[flag_11].apply(lambda row: add_call_schedule(row["call_schedule"], row["trade_date"], row["akaapi_bond"]), axis=1)
    data.loc[flag_11].apply(lambda row: row["akaapi_bond"].SetNoticePeriod(row["call_days_notice"]), axis=1)
    data.loc[flag_12].apply(lambda row: row["akaapi_bond"].SetCallAmerican(True), axis=1)
    data.loc[flag_13].apply(lambda row: row["akaapi_bond"].SetCallAmerican(False), axis=1)

    # set the daycount
    data.loc[data["day_cnt_des"].isna(), "day_cnt_des"] = "US MUNI: 30/360"   # TODO: change to corp bond
    data.loc[~data["day_cnt_des"].str.contains("US MUNI", na=False), "day_cnt_des"] = "US MUNI: " + data.loc[~data["day_cnt_des"].str.contains("US MUNI"), "day_cnt_des"]   # TODO: change to corp bond
    data.loc[data["day_cnt_des"] == "US MUNI: 30/360"].apply(lambda row: row["akaapi_bond"].SetDayCount(AkaApi.Bond.DC_30_360), axis=1)
    data.loc[data["day_cnt_des"] == "US MUNI:ACT/360"].apply(lambda row: row["akaapi_bond"].SetDayCount(AkaApi.Bond.DC_ACT_360), axis=1)
    data.loc[data["day_cnt_des"] == "US MUNI: ACT/365"].apply(lambda row: row["akaapi_bond"].SetDayCount(AkaApi.Bond.DC_ACT_365), axis=1)
    data.loc[data["day_cnt_des"] == "US MUNI: ACT/ACT"].apply(lambda row: row["akaapi_bond"].SetDayCount(AkaApi.Bond.DC_ACT_ACT), axis=1)
    data.loc[data["day_cnt_des"] == "US MUNI: ACT/ACT NON-EO"].apply(lambda row: row["akaapi_bond"].SetDayCount(AkaApi.Bond.DC_NO_LEAP_365), axis=1)

    # set the coupon frequency
    data.loc[data["cpn_freq"] == 1].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_ANNUAL), axis=1)
    data.loc[data["cpn_freq"] == 2].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_SEMIANNUAL), axis=1)
    data.loc[data["cpn_freq"] == 4].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_QUARTERLY), axis=1)
    data.loc[data["cpn_freq"] == 12].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_MONTHLY), axis=1)
    data.loc[data["cpn_freq"] == 52].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_ANNUAL_BY_WEEKS), axis=1)
    data.loc[~data["cpn_freq"].isin(1,2,4,12,52)].apply(lambda row: row["akaapi_bond"].SetFrequency(AkaApi.Bond.FREQ_INT_AT_MATURITY), axis=1)

    # add step schedule
    data.loc[(~data["stepup_cpn_schedule"].isnull())].apply(lambda row: add_step_schedule(row["stepup_cpn_schedule"], row["akaapi_bond"]), axis=1)

    # add put schedule
    data.loc[(~data["stepup_cpn_schedule"].isnull())].apply(lambda row: add_put_schedule(row["put_schedule"], row["trade_date"], row["akaapi_bond"]), axis=1)



