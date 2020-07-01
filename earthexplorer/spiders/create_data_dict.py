import atexit
import pickle
from usgs import api, USGSError
import os

no_data = {}

def main():
    API_KEY = custom_functions.get_API_key()
    global no_data
    _, _, _, DATA_DICT_PATH = custom_functions.get_updd()

    Path_i = 1
    Row_i = 1

    os.makedirs(os.path.dirname(DATA_DICT_PATH), exist_ok=True)
    try:
        with open(DATA_DICT_PATH, 'rb') as fp:
            no_data = pickle.load(fp)

        try:
            Path_i = sorted(no_data.keys())[-1]
            Row_i = no_data[Path_i][-1]

        except Exception as e:
            no_data = {}
            Path_i = 1
            Row_i = 1

    except FileNotFoundError as e:
        no_data = {}

    # incase path_i and row_i are taken from data_dict, they would be strings
    Path_i = int(Path_i)
    Row_i = int(Row_i)

    if Path_i > 1 or Row_i > 1:
        print(f'DATA_DICT already has data till Path {Path_i} and Row {Row_i}')

    dataset = 'LANDSAT_8_C1'

    for Path in range(Path_i, 234):

        for Row in range(1, 249):

            if (Path == Path_i) and (Row in range(1, Row_i + 1)):
                continue

            Path = str(Path)
            if len(Path) == 1:
                Path = '00' + Path
            elif len(Path) == 2:
                Path = '0' + Path

            Row = str(Row)
            if len(Row) == 1:
                Row = '00' + Row
            elif len(Row) == 2:
                Row = '0' + Row

            where = {20514 : Path, 20516 : Row}

            try:
                response = (api.search(dataset=dataset, node='EE', where=where, api_key=API_KEY))
            except USGSError as e:
                if 'AUTH_UNAUTHORIZED' in e:
                    API_KEY = custom_functions.get_API_key()
                    response = (api.search(dataset=dataset, node='EE', where=where, api_key=API_KEY))
                else:
                    custom_functions.record_error(e + f'\nERROR in create_dict.py\nAPI search error at Path {Path} and Row {Row}\n')
                    continue


            if(response['errorCode'] is not None):
                custom_functions.record_error(e + f'\nERROR in create_dict.py\nerrorCode {response["errorCode"]} received during query at Path {Path} and Row {Row}\n')

            if(response['data']['numberReturned'] == 0):
                continue

            no_data.setdefault(Path, [])
            no_data[Path].append(Row)

            print(f'Path {Path} and Row {Row} has some data')

    with open(DATA_DICT_PATH, 'wb') as fp:
        pickle.dump(no_data, fp)

if __name__ == '__main__':
    import custom_functions

    @atexit.register
    def save_data():
        global no_data
        _, _, _, DATA_DICT_PATH = custom_functions.get_updd()

        with open(DATA_DICT_PATH, 'wb') as fp:
            pickle.dump(no_data, fp)

        print('EARLY EXIT at create_data_dict.py')

    main()

else:
    import earthexplorer.spiders.custom_functions as custom_functions
