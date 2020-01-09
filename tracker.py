import configparser
import datetime
import json
import requests
import sched
import time

s = sched.scheduler(time.time, time.sleep)
api_key = ''
debug = ''
sample_file = ''
data_folder = ''
MAX_INT = 99999999999
item_dict = {}
frequency = 5
export_backup_folder = ''


def get_file():
    if debug == 0:
        if not sample_file:
            return ''
        with open(sample_file) as market_file:
            data = json.load(market_file)
            return data
    else:
        try:
            response = requests.get('https://api.originsro.org/api/v1/market/list?api_key=' + api_key)
            now = datetime.datetime.utcnow().strftime('%Y-%m-%d, %H:%M:%S')
            with open(export_backup_folder + now + '.json', 'wb') as f:
                f.write(response.content)
            return response.json()
        except Exception:
            return ''


def sort_and_store(price_list, ranked_list):
    if not price_list:
        return
    shops = price_list['shops']
    global item_dict
    item_dict = {}
    for shop in shops:
        if shop['type'] == 'B':
            continue
        items = shop['items']
        for item in items:
            try:
                item_cards = item['cards']
                if (len(item_cards)) > 0:
                    continue
            except Exception:
                pass

            item_id = item['item_id']
            item_price = item['price']

            # get refine
            try:
                item_refine = item['refine']
            except Exception:
                item_refine = 0
            if item_refine > 0:
                item_id = str(item_id) + '_refine_' + str(item_refine)

            # get ranking
            try:
                item_creator = item['creator']
            except Exception:
                item_creator = None
            if item_creator in ranked_list:
                item_id = str(item_id) + '_ranked_' + str(1)

            # store value
            try:
                current_price = item_dict[item_id]
                if item_price < current_price:
                    item_dict[item_id] = item_price
            except Exception:
                item_dict[item_id] = item_price


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global api_key
    global debug
    global sample_file
    global data_folder
    global frequency
    global export_backup_folder

    try:
        api_key = config['DEFAULT']['API_KEY']
    except Exception:
        pass

    try:
        debug = config['DEFAULT']['DEBUG_MODE']
    except Exception:
        pass

    try:
        sample_file = config['DEFAULT']['DEBUG_MARKET_FILE']
    except Exception:
        pass

    try:
        data_folder = config['DEFAULT']['DATA_FOLDER']
    except Exception:
        pass

    try:
        frequency = config['DEFAULT']['FREQUENCY']
        if frequency < 5:
            frequency = 5
    except Exception:
        pass

    try:
        export_backup_folder = config['DEFAULT']['FULL_MARKET_EXPORT_FOLDER']
    except Exception:
        pass


def get_ranked_list():
    return []


def get_filename(item):
    return data_folder + str(item) + '.json'


def generate_files():
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d, %H:%M:%S')
    if not item_dict:
        return
    for item in item_dict:
        try:  # handles case where a file with that item already exists
            with open(get_filename(item)) as item_json_file:
                existing_data = json.load(item_json_file)
            existing_data[now] = item_dict[item]
            with open(get_filename(item), 'w') as write_file:
                json.dump(existing_data, write_file)
        except Exception:
            try:  # handles case where a file with that item does not exist
                new_data = {now: item_dict[item]}
                with open(get_filename(item), 'w') as write_file:
                    json.dump(new_data, write_file)
            except Exception:
                pass


def log_event():
    pass


if __name__ == "__main__":
    # happens once upon intialization
    read_config()

    # events that happen once every day
    ranked_list = get_ranked_list()
    log_event()

    # events that happen once every <frequency> minutes
    price_list = get_file()
    sort_and_store(price_list, ranked_list)
    generate_files()
    log_event()
