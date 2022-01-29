import csv
import sys
import time
import re
import os
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from os import path
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_binary
from selenium.webdriver.chrome.options import Options
import logging

logger = logging.getLogger(__name__)  # ファイルの名前を渡す

now_datetime = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
options = Options()
options.add_argument('--headless')  # ヘッドレスモードに
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

URL = "https://db.netkeiba.com/?pid=race_search_detail"
driver.get(URL)
time.sleep(1)
wait.until(EC.presence_of_all_elements_located)

OWN_FILE_NAME = path.splitext(path.basename(__file__))[0]
RACR_URL_DIR = "race_url"
RACR_HTML_DIR = "race_html"
CSV_DIR = "csv"

race_data_columns = [
    'race_id',
    'race_round',
    'race_title',
    'race_course',
    'weather',
    'ground_status',
    'time',
    'date',
    'where_racecourse',
    'total_horse_number',
    'frame_number_first',
    'horse_number_first',
    'frame_number_second',
    'horse_number_second',
    'frame_number_third',
    'horse_number_third',
    'tansyo',
    'hukusyo_first',
    'hukusyo_second',
    'hukusyo_third',
    'wakuren',
    'umaren',
    'wide_1_2',
    'wide_1_3',
    'wide_2_3',
    'umatan',
    'renhuku3',
    'rentan3'
]

horse_data_columns = [
    'race_id',
    'rank',
    'frame_number',
    'horse_number',
    'horse_id',
    'sex_and_age',
    'burden_weight',
    'rider_id',
    'goal_time',
    'goal_time_dif',
    'time_value',
    'half_way_rank',
    'last_time',
    'odds',
    'popular',
    'horse_weight',
    'tame_time',
    'tamer_id',
    'owner_id'
]

# 月ごとに検索
year = 2021
month = 1
# ファイルのタイトル

# 期間を選択 初めの年月と終わりの年月を入れる　runする際はクロームをとしてから
start_year_element = driver.find_element_by_name('start_year')
start_year_select = Select(start_year_element)
start_year_select.select_by_value(str(2017))
start_mon_element = driver.find_element_by_name('start_mon')
start_mon_select = Select(start_mon_element)
start_mon_select.select_by_value(str(1))
end_year_element = driver.find_element_by_name('end_year')
end_year_select = Select(end_year_element)
end_year_select.select_by_value(str(2021))
end_mon_element = driver.find_element_by_name('end_mon')
end_mon_select = Select(end_mon_element)
end_mon_select.select_by_value(str(12))

# 中央競馬場をチェック
for i in range(1, 11):
    terms = driver.find_element_by_id("check_Jyo_" + str(i).zfill(2))
    terms.click()

# 表示件数を選択(20,50,100の中から最大の100へ)
list_element = driver.find_element_by_name('list')
list_select = Select(list_element)
list_select.select_by_value("100")

# フォームを送信
frm = driver.find_element_by_css_selector("#db_search_detail_form > form")
frm.submit()
time.sleep(5)
wait.until(EC.presence_of_all_elements_located)

with open(str(year) + "-" + str(month) + ".txt", mode='w') as f:  # 書き込み
    while True:
        time.sleep(5)
        wait.until(EC.presence_of_all_elements_located)
        all_rows = driver.find_element_by_class_name('race_table_01').find_elements_by_tag_name("tr")
        for row in range(1, len(all_rows)):
            race_href = all_rows[row].find_elements_by_tag_name("td")[4].find_element_by_tag_name("a").get_attribute(
                "href")
            f.write(race_href + "\n")
        try:
            target = driver.find_elements_by_link_text("次")[0]
            driver.execute_script("arguments[0].click();", target)  # javascriptでクリック処理
        except IndexError:
            break

save_dir = "html" + "/" + str(year) + "/" + str(month)
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)

with open(str(year) + "-" + str(month) + ".txt", "r") as f:
    urls = f.read().splitlines()
    for url in urls:
        list = url.split("/")
        race_id = list[-2]
        save_file_path = save_dir + "/" + race_id + '.html'
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        html = response.text
        time.sleep(5)
        with open(save_file_path, 'w') as file:
            file.write(html)

CSV_DIR = "csv"
if not os.path.isdir(CSV_DIR):
    os.makedirs(CSV_DIR)
save_race_csv = CSV_DIR + "/race-" + str(year) + "-" + str(month) + ".csv"
horse_race_csv = CSV_DIR + "/horse-" + str(year) + "-" + str(month) + ".csv"


def get_rade_and_horse_data_by_html(race_id, html):
    race_list = [race_id]
    horse_list_list = []
    soup = BeautifulSoup(html, 'html.parser')

    # race基本情報
    data_intro = soup.find("div", class_="data_intro")
    race_list.append(data_intro.find("dt").get_text().strip("\n"))  # race_round
    race_list.append(data_intro.find("h1").get_text().strip("\n"))  # race_title
    race_details1 = data_intro.find("p").get_text().strip("\n").split("\xa0/\xa0")
    race_list.append(race_details1[0])  # race_course
    race_list.append(race_details1[1])  # weather
    race_list.append(race_details1[2])  # ground_status
    race_list.append(race_details1[3])  # time
    race_details2 = data_intro.find("p", class_="smalltxt").get_text().strip("\n").split(" ")
    race_list.append(race_details2[0])  # date
    race_list.append(race_details2[1])  # where_racecourse

    result_rows = soup.find("table", class_="race_table_01 nk_tb_common").findAll('tr')  # レース結果
    # 上位3着の情報
    race_list.append(len(result_rows) - 1)  # total_horse_number
    for i in range(1, 4):
        row = result_rows[i].findAll('td')
        race_list.append(row[1].get_text())  # frame_number_first or second or third
        race_list.append(row[2].get_text())  # horse_number_first or second or third

    # 払い戻し(単勝・複勝・三連複・3連単)
    pay_back_tables = soup.findAll("table", class_="pay_table_01")

    pay_back1 = pay_back_tables[0].findAll('tr')  # 払い戻し1(単勝・複勝)
    race_list.append(pay_back1[0].find("td", class_="txt_r").get_text())  # tansyo
    hukuren = pay_back1[1].find("td", class_="txt_r")
    tmp = []
    for string in hukuren.strings:
        tmp.append(string)
    for i in range(3):
        try:
            race_list.append(tmp[i])  # hukuren_first or second or third
        except IndexError:
            race_list.append("0")

    # 枠連
    try:
        race_list.append(pay_back1[2].find("td", class_="txt_r").get_text())
    except IndexError:
        race_list.append("0")

    # 馬連
    try:
        race_list.append(pay_back1[3].find("td", class_="txt_r").get_text())
    except IndexError:
        race_list.append("0")

    pay_back2 = pay_back_tables[1].findAll('tr')  # 払い戻し2(三連複・3連単)

    # wide 1&2
    wide = pay_back2[0].find("td", class_="txt_r")
    tmp = []
    for string in wide.strings:
        tmp.append(string)
    for i in range(3):
        try:
            race_list.append(tmp[i])  # hukuren_first or second or third
        except IndexError:
            race_list.append("0")

    # umatan
    race_list.append(pay_back2[1].find("td", class_="txt_r").get_text())  # umatan

    race_list.append(pay_back2[2].find("td", class_="txt_r").get_text())  # renhuku3
    try:
        race_list.append(pay_back2[3].find("td", class_="txt_r").get_text())  # rentan3
    except IndexError:
        race_list.append("0")

    # horse data
    for rank in range(1, len(result_rows)):
        horse_list = [race_id]
        result_row = result_rows[rank].findAll("td")
        # rank
        horse_list.append(result_row[0].get_text())
        # frame_number
        horse_list.append(result_row[1].get_text())
        # horse_number
        horse_list.append(result_row[2].get_text())
        # horse_id
        horse_list.append(result_row[3].find('a').get('title'))
        # sex_and_age
        horse_list.append(result_row[4].get_text())
        # burden_weight
        horse_list.append(result_row[5].get_text())
        # rider_id
        horse_list.append(result_row[6].find('a').get('title'))
        # goal_time
        horse_list.append(result_row[7].get_text())
        # goal_time_dif
        horse_list.append(result_row[8].get_text())
        # time_value(premium)
        horse_list.append(result_row[9].get_text())
        # half_way_rank
        horse_list.append(result_row[10].get_text())
        # last_time(上り)
        horse_list.append(result_row[11].get_text())
        # odds
        horse_list.append(result_row[12].get_text())
        # popular
        horse_list.append(result_row[13].get_text())
        # horse_weight
        horse_list.append(result_row[14].get_text())
        # tame_time(premium)
        horse_list.append(result_row[15].get_text())
        # 16:コメント、17:備考
        # tamer_id
        horse_list.append(result_row[18].find('a').get('title'))
        # owner_id
        horse_list.append(result_row[19].find('a').get('title'))

        horse_list_list.append(horse_list)

    return race_list, horse_list_list


# def update_csv():


# race_data_columns, horse_data_columnsは長くなるので省略
race_df = pd.DataFrame(columns=race_data_columns)
horse_df = pd.DataFrame(columns=horse_data_columns)

html_dir = "html" + "/" + str(year) + "/" + str(month)
if os.path.isdir(html_dir):
    file_list = os.listdir(html_dir)
    for file_name in file_list:
        with open(html_dir + "/" + file_name, "r") as f:
            html = f.read()
            list = file_name.split(".")
            race_id = list[-2]
            race_list, horse_list_list = get_rade_and_horse_data_by_html(race_id, html)  # 長くなるので省略
            for horse_list in horse_list_list:
                horse_se = pd.Series(horse_list, index=horse_df.columns)
                horse_df = horse_df.append(horse_se, ignore_index=True)
            race_se = pd.Series(race_list, index=race_df.columns)
            race_df = race_df.append(race_se, ignore_index=True)

race_df.to_csv(save_race_csv, header=True, index=False)
horse_df.to_csv(horse_race_csv, header=True, index=False)

# 時間情報を抜き出して、日付情報と結合。datetime型にする
race_df["time"] = race_df["time"].str.replace('発走 : (\d\d):(\d\d)(.|\n)*', r'\1時\2分')
race_df["date"] = race_df["date"] + race_df["time"]
race_df["date"] = pd.to_datetime(race_df['date'], format='%Y年%m月%d日%H時%M分')
# もともとのtimeは不要なので削除
race_df.drop(['time'], axis=1, inplace=True)

# 何ラウンド目かのカラムに余分なRや空白・改行が含まれているので取り除く
race_df['race_round'] = race_df['race_round'].str.strip('R \n')
