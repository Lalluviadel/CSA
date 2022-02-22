import subprocess

import chardet

'''
    1. Каждое из слов «разработка», «сокет», «декоратор» представить в
строковом формате и проверить тип и содержание соответствующих переменных.
    Затем с помощью онлайн-конвертера преобразовать строковые представление
в формат Unicode и также проверить тип и содержимое переменных.
'''


def letters_to_unicode(words: list):
    """Converts string representation to Unicode format"""
    unicode_objects_collector = list()

    for word in words:
        print(f'Тип переменной: {type(word)}, содержимое: {word}')
        code_points_collector = list()

        for letter in word:
            code_point = '\\u' + str(hex(ord(letter))).replace('x', '')
            code_points_collector.append(code_point)

        unicode_object = ''.join([i for i in code_points_collector])
        print(f'Тип переменной: {type(unicode_object)}, содержимое: {unicode_object}')
        unicode_objects_collector.append(unicode_object)

    return unicode_objects_collector


words = ['разработка', 'сокет', 'декоратор']
print('Задание 1.')
result_01 = letters_to_unicode(words)

'''
    2. Каждое из слов «class», «function», «method» записать в байтовом типе 
без преобразования в последовательность кодов (не используя методы encode и 
decode) и определить тип, содержимое и длину соответствующих переменных.
'''


def str_in_bytes(word: str):
    """Converts string representation to byte representation"""
    byte_type = bytes(word, 'ascii')
    print(f'Тип данных: {type(byte_type)}, содержимое: {byte_type}, длина переменной: {len(byte_type)}')
    return byte_type


words = ['class', 'function', 'method']
print('\nЗадание 2.')
result_2 = list(map(str_in_bytes, words))

'''
    3. Определить, какие из слов «attribute», «класс», «функция», «type» 
невозможно записать в байтовом типе.
'''


def str_in_bytes_upd(word: str):
    """Converts string representation to byte representation with exception catching"""
    try:
        return bytes(word, 'ascii')
    except UnicodeEncodeError as e:
        print(f'Строковый объект "{e.object}" невозможно записать в байтовом типе '
              f'в кодировке ascii по причине: {e.reason}')


words = ['attribute', 'класс', 'функция', 'type']
print('\nЗадание 3.')
result_3 = list(map(str_in_bytes_upd, words))

"""
    4. Преобразовать слова «разработка», «администрирование», «protocol», 
«standard» из строкового представления в байтовое и выполнить обратное 
преобразование (используя методы encode и decode).
"""


def encode_words(words: list):
    """Converts string representation to byte representation"""
    encoded_words = [word.encode('utf-8') for word in words]
    print('Байтовое представление: ', *encoded_words)
    return encoded_words


def decode_words(words: list):
    """Converts byte representation to string representation"""
    decoded_words = [word.decode('utf-8') for word in words]
    print('Строковое представление: ', *decoded_words)
    return decoded_words


words = ['разработка', 'администрирование', 'protocol', 'standard']
print('\nЗадание 4.')
result_4 = decode_words(encode_words(words))

"""
    5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать 
результаты из байтовового в строковый тип на кириллице.
"""


def ping_to_str(list_of_sites: list):
    """Performs a ping of the site and converts byte representation to a string"""
    for site in list_of_sites:
        args = ['ping', site]
        ping_result = subprocess.Popen(args, stdout=subprocess.PIPE).stdout
        for row in ping_result:
            data_analysis = chardet.detect(row)
            result = row.decode(data_analysis['encoding'])
            print(result)


sites = ['yandex.ru', 'youtube.com']
print('\nЗадание 5.')
ping_to_str(sites)

"""
    6. Создать текстовый файл test_file.txt, заполнить его тремя строками: 
«сетевое программирование», «сокет», «декоратор».
    Проверить кодировку файла по умолчанию. 
    Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""


# сетевое программирование
# сокет
# декоратор

def transcoding_and_recording():
    """Overwrites the file with UTF-8 encoding"""
    with open('test_file.txt', 'rb') as text_file:
        data = text_file.read()
        data_analysis = chardet.detect(data)
        print(f'Исходная кодировка: {data_analysis["encoding"]}')
        str_text = data.decode(data_analysis['encoding'])
    with open('test_file.txt', 'wb') as rewritable_file:
        rewritable_file.write(str_text.encode('utf-8'))


def read_file():
    """Opens a file with any encoding as UTF-8"""
    try:
        with open('test_file.txt', 'r', encoding='utf-8') as txt_file:
            data = txt_file.read()
            print(data)
    except UnicodeDecodeError:
        transcoding_and_recording()
        read_file()
    return


print('\nЗадание 6.')
read_file()
