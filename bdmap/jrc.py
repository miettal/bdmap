import json
import datetime
import time
import re

import requests

from pydams import DAMS
from pydams.helpers import pretty_print

from bs4 import BeautifulSoup


DAMS.init_dams()


def geocode(place):
    geocoded = DAMS.geocode(place)
    pretty_print(geocoded)
    print(geocoded)
    print('---')

    if len(geocoded['candidates']) == 0:
        return None
    return geocoded['candidates'][0][-1]


def get_center_list():
    time.sleep(0.5)
    response = requests.get('http://www.jrc.or.jp/search/bloodcenter/')
    soup = BeautifulSoup(response.content, 'html.parser')
    center_list = []
    for tr in soup.select('.td-header tbody tr'):
        if len(tr.select('th')) == 3:  # header
            pass
        elif len(tr.select('th')) == 1:  # block
            pass
        else:
            td_list = tr.select('td')
            url = td_list[0].find('a')['href']
            name = td_list[0].get_text()
            address = td_list[1].get_text()
            phone = td_list[2].get_text()

            m = re.match('(.+)血液センター', name)
            block = m.group(1)[-4:] == 'ブロック'
            if block:
                area_name = m.group(1)[:-4]
            else:
                area_name = m.group(1)[:-4]

            center_list.append({
                'name': name,
                'url': url,
                'address': address,
                'phone': phone,
                'block': block,
                'area_name': area_name,
            })
    return center_list


def get_center_status(url):
    # url = 'https://www.bs.jrc.or.jp/hkd/hokkaido/'
    time.sleep(0.5)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    status = {}
    for (head, body) in zip(soup.select('.center-main-today-btns li') or soup.select('.block-main-today-btns li'), soup.select('.mod-tabSecs ul')):
        donation_type = head.get_text()
        status[donation_type] = {}
        for li in body.select('li'):
            blood_type = li.select('p span')[0].get_text()
            src = li.select('div figure img')[0]['src']

            # amount = int(re.match('.*/ico_bloodHeart_([0-9]+)_[a-z]+.svg', src).group(1)) / 100
            amount = '{:3d}%'.format(int(re.match('.*/ico_bloodHeart_([0-9]+)_[a-z]+.svg', src).group(1)))
            status[donation_type][blood_type] = amount

    return status

def get_room_list(url):
    # parse top page
    time.sleep(0.5)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    for a in soup.select('footer a'):
        if a.get_text() == '献血ルーム紹介':
            room_list_url = url + a.get('href')
            break
    else:
        raise Exception()

    # parse room list page
    time.sleep(0.5)
    response = requests.get(room_list_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    room_header_table = {
        '場所': 'address',
        '電話': 'phone',
        '受付時間': 'reception_time',
        '定休日': 'regular_holiday',
    }

    room_list = []
    for a in soup.select('.mod-post-main a'):
        room_url = '/'.join(room_list_url.split('/')[:-1]) + '/' + a.get('href')
        time.sleep(0.5)
        response = requests.get(room_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # room
        room = {}
        for h1 in soup.select('#mod-mainContent h1'):
            room['name'] = h1.get_text()
        for li in soup.select('.mod-room-single-main-specs li'):
            head = li.select('.mod-room-single-main-specs-h')[0].get_text().strip()
            text = li.select('.mod-room-single-main-specs-txt')[0].get_text().strip()
            room[room_header_table[head]] = text
            if head == '場所':
                for place in text.split('\n'):
                    if place.startswith('〒'):
                        continue
                    location = geocode(place)
                    if location is not None:
                        room['location'] = location
                        break
        if room != {}:
            room['url'] = room_url
            room_list.append(room)
            continue
    return room_list


def get_bus_list(url):
    # parse top page
    time.sleep(0.2)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    for a in soup.select('footer a'):
        if a.get_text() == '献血バス運行スケジュール':
            bus_url = url + a.get('href')
            break
    else:
        for a in soup.select('.mod-posts04-item a'):
            if a.get_text() == '献血バス運行スケジュール':
                bus_url = url + a.get('href')
                break
        else:
            raise Exception()

    # parse bus page
    time.sleep(0.5)
    response = requests.get(bus_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    bus_header_table = {
        '市区町村': 'area',
        '献血会場': 'address',
        '受付時間': 'reception_time',
    }

    bus_list = []
    pattern = '(\\d+)月 *(\\d+)日\\(.+\\)'  # 12月27日(&#26085;)
    date_p_list = [p for p in soup.select('.mod-iconIndent01 p') if re.match(pattern, p.get_text().strip())]
    for (p, table) in zip(date_p_list, soup.select('.mod-ReservationTable')):
        m = re.match(pattern, p.get_text().strip())
        date = datetime.date(2020, int(m.group(1)), int(m.group(2)))
        for tr in table.select('tbody tr'):
            bus = {}
            for (th, td) in zip(table.select('thead tr th'), tr.select('td')):
                head = th.get_text().strip()
                text = td.get_text().strip()
                bus[bus_header_table[head]] = text
                if head == '献血会場':
                    for place in text.split('\n'):
                        if place.startswith('〒'):
                            continue
                        location = geocode(place)
                        if location is not None:
                            bus['location'] = location
                            break
            if bus != {}:
                bus['url'] = bus_url
                bus['date'] = date
                bus_list.append(bus)

    return bus_list


if __name__ == '__main__':
    center_list = get_center_list()
    # for center in center_list:
    #     if center['block'] is not True:
    #         continue
    #     print(center['url'])
    #     status = get_center_status(center['url'])
    #     print(center['name'], end='')
    #     print(' ' * 2 * (16 - len(center['name'])), end='')
    #     print(status)
    #     time.sleep(0.2)
    # bus_list = get_bus_list('https://www.bs.jrc.or.jp/ktks/nagano/')

    for (i, center) in enumerate(center_list):
        if center['block'] is True:
            continue
        print(center['name'])
        center_list[i]['status'] = get_center_status(center['url'])
        center_list[i]['room_list'] = get_room_list(center['url'])
        center_list[i]['bus_list'] = get_bus_list(center['url'])

    with open('center_list.json', 'w') as f:
        f.write(json.dumps(center_list))
