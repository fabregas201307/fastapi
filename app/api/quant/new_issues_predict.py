import pandas as pd
import numpy as np
import abdata
import os
import re
from abAlphaUtils.timezone_utils import get_eastern_time_day
import platform
import openpyxl

class NewIssuesPredict:
    def __init__(self):
        self.platform = platform.system().lower()
        self.folder = ""
        if self.platform == "windows":
            self.folder = "\\\\nasapps1\\fiquantit\\fiquant\\new_issue_data\\"
        elif self.platform == "linux":
            self.folder = "/fiquant/new_issue_data/"
        else:
            raise Exception(f"""Platform {self.platform} not supported""")
        
        self.new_issues = pd.DataFrame()
        # self.today = get_eastern_time_day()
        self.today = "2024-08-01"
        self.today_file = f"""{self.folder}{self.today}.xlsx"""

    def load_latest_new_issues(self):
        if self.platform == "windows":
            # load the workbook
            workbook = openpyxl.load_workbook(self.today_file)
            # select the worksheet
            worksheet = workbook["Sheet1"]
            # read the data
            data = []
            for row in worksheet.iter_rows(values_only=True):
                data.append(row)
            # convert to a DataFrame
            self.new_issues = pd.DataFrame(data[1:], columns=data[0])
        elif self.platform == "linux":
            self.new_issues = pd.read_excel(self.today_file)
        else:
            raise Exception(f"""Platform {self.platform} not supported""")
        
        print(f"""Loaded new issues from {self.today_file}""")

