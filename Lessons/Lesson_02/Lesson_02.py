import csv
import json
import re
from pprint import pprint

import chardet
import yaml

'''
    1. Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt,
info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого:
        a. Создать функцию get_data(), в которой в цикле осуществляется
    перебор файлов с данными, их открытие и считывание данных. В этой функции
    из считанных данных необходимо с помощью регулярных выражений извлечь
    значения параметров «Изготовитель системы»,  «Название ОС», «Код продукта»,
    «Тип системы».
        Значения каждого параметра поместить в соответствующий список.
    Должно получиться четыре списка — например, os_prod_list, os_name_list,
    os_code_list, os_type_list. В этой же функции создать главный список
    для хранения данных отчета — например, main_data — и поместить в него
    названия столбцов отчета в виде списка: «Изготовитель системы», «Название
    ОС», «Код продукта», «Тип системы». Значения для этих столбцов также
    оформить в виде списка и поместить в файл main_data (также для каждого
    файла);
        b. Создать функцию write_to_csv(), в которую передавать ссылку на
    CSV-файл. В этой функции реализовать получение данных через вызов функции
    get_data(), а также сохранение подготовленных данных в соответствующий
    CSV-файл;
        c. Проверить работу программы через вызов функции write_to_csv().
'''


def get_data():  # извините, я не стала создавать промежуточные списки, а сразу помещаю данные в main_data
    """Retrieves the necessary data from text files"""
    files = ['info_1.txt', 'info_2.txt', 'info_3.txt']
    search_subjects = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    main_data = [[] for _ in range(4)]
    main_data[0] = search_subjects
    counter = 1

    for file in files:
        with open(file, 'rb') as text_file:
            raw_data = text_file.read()
            data_analysis = chardet.detect(raw_data)
            str_text = raw_data.decode(data_analysis['encoding'])

            for subject in search_subjects:
                # перебираем маски для поиска, если нашли - обрабатываем строку,
                # забираем полученный результат и складываем его в соответствующий подсписок
                match = re.findall(fr'{subject}.*[^\\\r\n ]', str_text)
                if match:
                    raw_data = match[0].split(':')
                    main_data[counter].append(raw_data[1].strip())
            counter += 1
    return main_data


def write_to_csv():
    """Writing data received from text files to a csv file"""
    with open("data_report.csv", mode="w", encoding='utf-8') as csv_file:
        file_writer = csv.writer(csv_file, delimiter=",", lineterminator="\r")
        processed_data = get_data()
        for item in processed_data:
            file_writer.writerow(item)


write_to_csv()

'''
    2. Задание на закрепление знаний по модулю json. Есть файл orders в формате
JSON с информацией о заказах. Написать скрипт, автоматизирующий его заполнение
данными. Для этого:
        a. Создать функцию write_order_to_json(), в которую передается 5 
    параметров — товар (item), количество (quantity), цена (price), покупатель 
    (buyer), дата (date). Функция должна предусматривать запись данных в виде 
    словаря в файл orders.json. При записи данных указать величину отступа в 4 
    пробельных символа;
        b. Проверить работу программы через вызов функции write_order_to_json()
    с передачей в нее значений каждого параметра.
'''


def write_order_to_json(item, quantity, price, buyer, date, keys=('item', 'quantity', 'price', 'buyer', 'date')):
    """Fills json with data"""
    with open('orders.json') as json_read:
        file = json.load(json_read)
        orders = file['orders']
        new_order = {x: y for x, y in zip(keys, (item, quantity, price, buyer, date))}
        orders.append(new_order)
    with open('orders.json', 'w') as json_write:
        json.dump(file, json_write, sort_keys=True, indent=2, ensure_ascii=False)

    with open('orders.json') as f_n:
        print(f_n.read())


write_order_to_json('Ноутбук LENOVO', 2, 75000.00, 'Муравьев Антон', '22.02.2022')
write_order_to_json('Ноутбук ACER', 1, 68000.00, 'Ковалев Игорь', '20.02.2022')

'''
    3. Задание на закрепление знаний по модулю yaml. Написать скрипт, 
автоматизирующий сохранение данных в файле YAML-формата. Для этого:
        a. Подготовить данные для записи в виде словаря, в котором первому 
    ключу соответствует список, второму — целое число, третьему — вложенный 
    словарь, где значение каждого ключа — это целое число с юникод-символом, 
    отсутствующим в кодировке ASCII (например, €);
        b. Реализовать сохранение данных в файл формата YAML — например, в 
    файл file.yaml. При этом обеспечить стилизацию файла с помощью параметра 
    default_flow_style, а также установить возможность работы с юникодом: 
    allow_unicode = True;
        c. Реализовать считывание данных из созданного файла и проверить, 
    совпадают ли они с исходными.
'''


def yaml_writing_and_reading(data_dict):
    """Writing yaml with special characters and reading"""
    with open('data_write.yaml', 'w', encoding='utf-8') as file_w:
        yaml.dump(data_dict, file_w, default_flow_style=False, allow_unicode=True, indent=4)
    with open('data_write.yaml', encoding='utf-8') as file_r:
        result = yaml.load(file_r, Loader=yaml.FullLoader)
    pprint(result)


data = {'items': ['computer', 'printer', 'keyboard', 'mouse'],
        'items_quantity': 4,
        'items_price': {'computer': '200€-1000€',
                        'keyboard': '5£-50£',
                        'mouse': '4₽-7₽',
                        'printer': '100₿-300₿'}}

yaml_writing_and_reading(data)
