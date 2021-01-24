from selenium import webdriver
import time
import re
import json
from functools import reduce
import datetime

##  配置
# 爬取链接
LINKS = ['http://zq.win007.com/cn/League/36.html']
# 赛季年份（备选参数，非必传，默认是最新年份，其他年份参考上面的网址，如 2017-2018）
SELECTED_YEAR = ''
# 开始的轮次
START_ROUND = 0
# 结束的轮次，-1 为爬取到最后一轮
END_ROUND = -1

##  静态变量
"""chromedriver 的路径
需要替换为自己操作系统的版本，参考 https://chromedriver.chromium.org/downloads
对于 macOS，运行前可能会提示无法安全问题，需要先到【设置-通用】里允许权限
"""
DRIVER_PATH = './chromedriver_mac64'
# 页面切换和表格数据加载所需等待的时间
MAIN_TIME_SLEEP = 3
# 赛季年份切换选项的 ID
SEASON_LIST_SELECT_ID = 'seasonList'
# 【亚指】选项的 ID
ASIAN_HANDICAP_ID = 'rdoL'
# 【大小】选项的 ID
BIG_AND_SMALL_ID = 'rdoT'
# 【欧指】选项的 ID
EUROPEAN_HANDICAP_ID = 'rdoO'
# 轮次切换所需等待的时间
ROUND_CHANGE_TIME_SLEEP = 1
# 赔率数据切换所需等待的时间
ODDS_COMPANY_CHANGE_TIME_SLEEP = 0.1
# 轮次的 XPath
ROUNDS_XPATH = '//td[@id="showRound"]//tbody//td'
# 选中轮次的 XPath
SELECTED_ROUND_XPATH = '//td[@id="selectName"]'
# 表格行的 XPath
RECORDS_XPATH = '//table[@class="tdlink lh17 fixedtable"]/tbody/tr[@align="center"]'
# 庄家
ODDS_COMPANY_LIST = ['澳门','Crown','Bet365','易胜博','金宝博','利记','立博','明陞']
# 庄家选择框 ID
ODDS_COMPANY_SELECT_ID = 'oddsCompany'

## 主函数
""" main 传参
link 爬取链接
"""
def main(link):
    year = SELECTED_YEAR
    result = []
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    try:
        driver.get(link)
        time.sleep(MAIN_TIME_SLEEP)
        title_raw = driver.find_element_by_id('TitleLeft').text
        title = f'{title_raw.split(" ")[0]}{title_raw.split(" ")[1]}'
        season_list_select = driver.find_element_by_id(SEASON_LIST_SELECT_ID)
        season_list_options = season_list_select.find_elements_by_tag_name('option')
        # 如果传入赛季年份，则切换到对应的时间
        if year:
            for option in season_list_options:
                if (option.get_attribute('value') == year):
                    option.click()
                    time.sleep(MAIN_TIME_SLEEP)
                    break
        else:
            year = season_list_options[0].get_attribute('value')
        # 切换赔率为【大小】
        driver.find_element_by_id(BIG_AND_SMALL_ID).click()
        time.sleep(ODDS_COMPANY_CHANGE_TIME_SLEEP)
        # 轮次列表
        rounds = driver.find_elements_by_xpath(ROUNDS_XPATH)
        for i, current_round in enumerate(rounds[1:]):
            if (START_ROUND != 0 and i < START_ROUND) or (END_ROUND != -1 and i > END_ROUND):
                continue
            current_round.click()
            time.sleep(ROUND_CHANGE_TIME_SLEEP)
            selected_round = driver.find_element_by_xpath(SELECTED_ROUND_XPATH).text
            print(selected_round)
            # 存储当前轮次的数据
            current_round_results = []
            def append_data():
                odds_company_select = driver.find_element_by_id(ODDS_COMPANY_SELECT_ID)
                odds_company_options = odds_company_select.find_elements_by_tag_name('option')
                for option in odds_company_options:
                    if option.text in ODDS_COMPANY_LIST:
                        option.click()
                        time.sleep(ODDS_COMPANY_CHANGE_TIME_SLEEP)
                        records = driver.find_elements_by_xpath(RECORDS_XPATH)
                        for j, record in enumerate(records):
                            record_items_list = record.find_elements_by_xpath('./td')
                            set_list = list(map(float, (record_items_list[6].text or '0').split('/')))
                            if len(current_round_results) == len(records):
                                current_round_results[j]['odds'][option.text] = {
                                    "big": float(record_items_list[5].text or '0'),
                                    "set": reduce(lambda x, y: x + y, set_list) / len(set_list),
                                    "small": float(record_items_list[7].text or '0')
                                }
                            else:
                                current_round_results.append({
                                    'year': year,
                                    'time': record_items_list[1].text.replace('\n', ' '),
                                    'round': selected_round,
                                    'home_team': re.sub('\\[.*?\\]', '', record_items_list[2].text),
                                    'away_team': re.sub('\\[.*?\\]', '', record_items_list[4].text),
                                    'odds': {
                                        option.text: {
                                            "big": float(record_items_list[5].text or '0'),
                                            "set": reduce(lambda x, y: x + y, set_list) / len(set_list),
                                            "small": float(record_items_list[7].text or '0')
                                        }
                                    }
                                })
            try:
                append_data()
            except:
                print(f'Except, round: {selected_round}')
                current_round_results = []
                append_data()
            result = result + current_round_results
        with open(f'{title}.json', 'a', encoding='utf-8') as file:
            file.truncate(0)
            json.dump(result, file, ensure_ascii=False)
            file.close()
    finally:
        driver.quit()

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    for link in LINKS:
        main(link)
    end_time = datetime.datetime.now()
    seconds = (end_time - start_time).seconds
    # 统计脚本执行时间
    print(f'脚本执行时间：{(seconds - seconds % 60) / 60}min{seconds % 60}s')
