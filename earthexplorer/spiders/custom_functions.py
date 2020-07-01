CONFIG_FILE_PATH = '/path/to/config_file.txt'
ERROR_LOG = '/path/to/error_log.txt'
RESUME_LOG = '/path/to/resume_log.txt'

from usgs import api, USGSError
from datetime import datetime
import os

def record_error(str_):     # print error and also record it
    print(f'{str(datetime.now())}\n{str_}\n\n')

    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, 'a') as f:
        f.write(f'{str(datetime.now())}\n{str_}\n\n')


def get_updd():     # returns USERNAME, PASSWORD, DOWNLOAD_PATH, DATA_DICT_PATH

    with open(CONFIG_FILE_PATH, 'r') as f:
        # 1
        i = f.readline()
        if 'USERNAME=' not in i:
            record_error('Invalid username format in config_file')
            USERNAME = None
        else:
            USERNAME = i.split('USERNAME=')[1].strip()

        # 2
        i = f.readline()
        if 'PASSWORD=' not in i:
            record_error('Invalid password format in config_file')
            PASSWORD = None
        else:
            PASSWORD = i.split('PASSWORD=')[1].strip()

        # 3
        i = f.readline()
        if 'DOWNLOAD_PATH=' not in i:
            record_error('Invalid download_path format in config_file')
            DOWNLOAD_PATH = None
        else:
            DOWNLOAD_PATH = i.split('DOWNLOAD_PATH=')[1].strip()
            if(DOWNLOAD_PATH[-1] != '/'):
                DOWNLOAD_PATH += '/'

        # 4
        i = f.readline()
        if 'DATA_DICT_PATH=' not in i:
            print('Invalid data_dict_path format in config_file')
            DATA_DICT_PATH = None
        else:
            DATA_DICT_PATH = i.split('DATA_DICT_PATH=')[1].strip()

    return (USERNAME, PASSWORD, DOWNLOAD_PATH, DATA_DICT_PATH)

def get_API_key():
    user, password, _, _ = get_updd()

    try:
        return (api.login(user, password, save=True, catalogId='EE')['data'])
    except USGSError as e:
        record_error(e)
        raise e
        # return None

def get_resume():
    try:
        with open(RESUME_LOG, 'r') as fp:
            path = fp.readline().strip()
            row = fp.readline().strip()

        return (path, row)

    except FileNotFoundError as e:
        return ('', '')


def set_resume(path, row):
    os.makedirs(os.path.dirname(DATA_DICT_PATH), exist_ok=True)
    with open(RESUME_LOG, 'w') as fp:
        fp.write(path + '\n')
        fp.write(row + '\n')

if __name__ == '__main__':
    print(get_updd())
    print(get_API_key())
