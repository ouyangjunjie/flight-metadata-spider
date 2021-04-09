import requests
from requests.exceptions import RequestException
import re
import json
from multiprocessing import Pool


def get_one_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            return response.text
        return None
    except RequestException:
        return None


def parse_one_page(html):
    pattern = re.compile('<a .*?target="_blank">(.*?)<br />(.*?)</a>.*?<a .*?target="_blank">(.*?)<br />(.*?)</a>.*?<a .*?target="_blank">(.*?)</a>.*?<a .*?target="_blank">.*?</a>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'cityChineseName': item[0].replace("\n", "").replace("\t", ""),
            'cityEnglishName': item[1].replace("\n", "").replace("\t", ""),
            'airportChineseName': item[2].replace("\n", "").replace("\t", ""),
            'airportEnglishName': item[3].replace("\n", "").replace("\t", ""),
            'airportCode': item[4].replace("\n", "").replace("\t", ""),
            'countryCode': 'CN'
        }


def write_to_file(content):
    with open('airport_cn.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


def main(offset):
    url = 'http://airport.anseo.cn/c-china'
    if offset > 1:
        url = 'http://airport.anseo.cn/c-china__page-' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


def get_proxy_ip():
    proxy_url = 'http://localhost:5555/random'
    response = requests.get(proxy_url)
    print(response.text)


# 获取国家二字码
def get_country_code():
    url = 'http://www.pfcexpress.com/Manage/WebManage/OrderInner.aspx?ContentID=33&ParentID=56&StyleID=57'
    html = get_one_page(url)
    pattern = re.compile('<tr.*?>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?</tr>', re.S)
    items = re.findall(pattern, html)
    countries = {}
    for item in items:
        country_code = item[0].replace("\r", "").replace("\n", "").replace("\t", "").replace(" ", "")
        country_name = item[1].replace("\r", "").replace("\n", "").replace("\t", "")
        country = item[2].replace("\r", "").replace("\n", "").replace("\t", "")
        print(country_code)
        if len(country) == 2:
            countries[country_code] = country
    return countries


# 爬取航点数据
if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [i for i in range(9)])
    # get_country_code()