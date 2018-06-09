'''
此脚本目的：
1、登录淘宝网首页，输入框输入关键词搜索商品，抓取商品的简要信息
2、将抓取的信息存入本地数据库(MongoDB)
url:https://www.taobao.com

'''

# 实现首页输入关键词，然后等待页面加载完成
# 两种方式：
# 1. 使用selenium模拟用户，输入关键词，点击确定，跳转
# 2. 输入关键词，点击搜索后，可以观察到带有关键词参数的URL，直接输入该URL地址也可以直接跳转
# 例：https://s.taobao.com/search?q=ipad  修改ipad为指定关键词即可

import time
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
import pymongo

base_url = 'https://s.taobao.com/search?q='
# 不弹出浏览器，后端执行
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
# browser = webdriver.Chrome()
# 作用：显示等待，找到页面某个特定元素加载完成后，再继续执行后续代码.
# 此处设置超时时间10s，如果在10s内，指定的元素还没有出现在页面中，则抛出异常
wait = WebDriverWait(browser, 10)


def get_keyword_index_page(keyword, page):
    kw_url = base_url + str(keyword)
    browser.get(kw_url)
    try:
        if page > 1:
            input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#mainsrp-pager .input')))
            submit = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#mainsrp-pager .btn')))
            input.clear()
            input.send_keys(page)
            submit.click()
        print("正在抓取第{0}页信息".format(page))
        time.sleep(5)
        # 确认页面加载完成（指定元素出现在页面，可根据实际情况选择元素）
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                   '#mainsrp-itemlist .items .item.J_MouserOnverReq')))
        wait.until(EC.text_to_be_present_in_element((
            By.CSS_SELECTOR, '#mainsrp-pager .inner.clearfix ul > li.item.active > span'), str(page)))
        print("Loading page successfully")
        get_product_info()
    except TimeoutException:
        print("Failed to loading page")
        get_keyword_page(keyword, page)


# 保存结果至数据库
MONGO_URL = "localhost"
MONGO_DB = "taobao"
MONGO_COLLECTION = "lvxingbao"
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def save_to_mongo(result):
    try:
        if db[MONGO_COLLECTION].insert(result):
            print("保存至MongoDB成功")
    except Exception:
        print("保存至MongoDB失败")


# 获取搜索项主要信息
def get_product_info():
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item.J_MouserOnverReq').items()
    for item in items:
        product = {
            "image": item.find('.pic .img').attr('data-src'),
            "title": item.find('.ctx-box .title').text().replace('\n', ''),
            "price": item.find('.ctx-box .price').text().replace('\n', ''),
            "deal": item.find('.deal-cnt').text(),
            "shop": item.find('.ctx-box .shop').text(),
            "location": item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)


# 遍历前n页
def get_page(keyword, n):
    for i in range(1, n + 1):
        # print("正在抓取第{0}页商品信息".format(i))
        get_keyword_index_page(keyword, i)


# 程序主入口，可修改搜索关键词
if __name__ == '__main__':
    get_page('旅行包', 10)
