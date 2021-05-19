import math
from functools import partial

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
        proxies = {
            "http": "socks5://127.0.0.1:7890",
            "https": "socks5://127.0.0.1:7890",
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
    with open('airport.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


def main(offset, lon_lat_items):
    url = 'http://airport.anseo.cn/c-china'
    if offset > 1:
        url = 'http://airport.anseo.cn/c-china__page-' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        iata = item['airportCode']
        if len(iata) > 0 and iata in lon_lat_items:
            lon_lat_item = lon_lat_items[iata]
            if lon_lat_item is not None:
                item.update(lon_lat_item)
        print(item)
        write_to_file(item)


def get_lat_lon():
    # 设置经纬度及时区
    # url = 'https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E6%9C%BA%E5%9C%BA%E5%88%97%E8%A1%A8'
    fo = open("airport.html", "r", encoding="utf-8")
    html = fo.read()
    lat_lon_items = {}
    for item in parse_lat_lon(html):
        print(item)
        lat_lon_items[item['iata']] = item
    return lat_lon_items


def calculate_lon(longitude):
    base_timezone = int(longitude / 15)
    cal_timezone = math.fabs(longitude % 15)
    if cal_timezone <= 7.5:
        timezone = base_timezone
    else:
        timezone = base_timezone + (1 if longitude > 0 else -1)
    return str(int(math.fabs(timezone))) if timezone >= 0 else "-" + str(int(math.fabs(timezone)))


# '<tr .*?>.*?<td align="left"><a .*?>(.*?)</a>.*?</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>.*?<span class="latitude">(.*?)</span>.*?<span class="longitude">(.*?)</span>.*?</td>.*?</tr>',

def parse_lat_lon(html):
    pattern = re.compile('<tr.*?>.*?<td align="left"><a .*?>(.*?)</a>.*?</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td><a .*?>(.*?)</a>.*?</td>.*?<td>.*?<span class="latitude">(.*?)</span>.*?<span class="longitude">(.*?)</span>.*?</td>.*?</tr>', re.S)
    airport_items = re.findall(pattern, html)
    for item in airport_items:
        icao = item[1]
        iata = item[2]
        if icao is None or len(icao) == 0:
            continue
        latitude = item[7].replace("°", ".").replace("′", "").replace("″", "")
        latitude = float(latitude.replace("N", "") if latitude.endswith('N') else '-' + latitude.replace("S", ""))

        longitude = item[8].replace("°", ".").replace("′", "").replace("″", "")
        longitude = float(longitude.replace("E", "") if longitude.endswith('E') else '-' + longitude.replace("W", ""))
        timezone = calculate_lon(longitude)
        yield {
            # 'airportName': item[0],
            'icao': icao,
            'iata': item[2],
            'status': item[3],
            'startTime': item[4],
            'flightLevel': item[5],
            'latitude': latitude,
            'longitude': longitude,
            'timeZone': timezone
        }


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
    items = get_lat_lon()

    # pool = Pool()
    # partial_main = partial(main, lon_lat_items=items)
    # offset = [i for i in range(9)]
    # pool.map(partial_main, offset)
    for i in range(9):
        main(i, items)
