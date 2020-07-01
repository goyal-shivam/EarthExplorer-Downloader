import scrapy
from scrapy.http import FormRequest
import earthexplorer.spiders.custom_functions as custom_functions
import pickle
from datetime import datetime
from usgs import api, USGSError
import os
import zipfile
import tarfile


USERNAME, PASSWORD, DOWNLOAD_PATH, DATA_DICT_PATH = custom_functions.get_updd()
PATH_S, ROW_S = custom_functions.get_resume()        # path_start, row_start
LAST_PATH = ''
LAST_ROW = ''
downloaded = {}

def geturls():
    dataset = 'LANDSAT_8_C1'

    global DATA_DICT_PATH
    global DOWNLOAD_PATH
    global PATH_S
    global ROW_S
    global LAST_PATH
    global LAST_ROW

    with open(DATA_DICT_PATH, 'rb') as fp:
        data_dict = pickle.load(fp)

    API_KEY = custom_functions.get_API_key()

    LAST_PATH = list(data_dict.keys())[-1]
    LAST_ROW = data_dict[LAST_PATH][-1]

    for Path in data_dict:

        # RESUME DOWNLOADING CODE
        if (PATH_S != ''):
            if int(Path) < int(PATH_S):
                continue

        for Row in data_dict[Path]:

            # RESUME DOWNLOADING CODE
            if (ROW_S != ''):
                if int(Row) < int(ROW_S):
                    continue

            where = {20514 : Path, 20516 : Row}

            # MAKING QUERY REQUEST TO USGS API
            try:
                response = (api.search(dataset=dataset, node='EE', where=where, api_key=API_KEY))
            except USGSError as e:
                if 'AUTH_UNAUTHORIZED' in e:
                    API_KEY = custom_functions.get_API_key()
                    response = (api.search(dataset=dataset, node='EE', where=where, api_key=API_KEY))
                else:
                    custom_functions.record_error(e + f'Error in downloader.py\nAPI search error at Path {Path} Row {Row}')


            if (response['data']['numberReturned'] == 0):
                continue

            # FINDING OUT THE LATEST DATASET AVAILABLE FOR THE PATH-ROW COMBINATION
            date = datetime.strptime('1957-10-03', '%Y-%m-%d')

            for i in response['data']['results']:
                currdate = datetime.strptime(i['acquisitionDate'], '%Y-%m-%d')
                if(currdate > date):
                    date = currdate
                    displayId = i['displayId']
                    downloadUrl = i['downloadUrl']

            yield (displayId, Path, Row, downloadUrl)


class SatelliteDataDownloader(scrapy.Spider):

    name = 'data_downloader'
    start_urls = ['https://ers.cr.usgs.gov/login/']
    download_urls = geturls()

    def parse(self, response):
        global USERNAME
        global PASSWORD
        global DOWNLOAD_PATH

        csrf_token = response.xpath('//form[@id="loginForm"]/dd[@id="csrf_token-element"]/input[@name="csrf_token"]/@value').get()

        yield FormRequest.from_response(response, formdata={"csrf_token": csrf_token, "username":USERNAME, "password":PASSWORD}, callback=self.parse_after_login)


    def parse_after_login(self, response):
        for i in self.download_urls:
            yield scrapy.Request(i[-1], callback=self.get_download_links, meta={'displayId':i[0], 'Path':i[1], 'Row':i[2]})


    def get_download_links(self, response):
        global downloaded

        Path = response.meta['Path']
        Row = response.meta['Row']

        count = len(response.xpath('//input[@class="button inlineButton"]/@onclick').getall())
        downloaded.setdefault(Path, {})
        downloaded[Path].setdefault(Row, {})
        downloaded[Path][Row] = count

        for i in response.xpath('//input[@class="button inlineButton"]/@onclick').getall():
            # response.meta['count'] = count
            yield scrapy.Request(i.split("'")[1], callback=self.download_data, meta=response.meta)


    def login_again(self, response):
        global USERNAME
        global PASSWORD
        global DOWNLOAD_PATH

        csrf_token = response.xpath('//form[@id="loginForm"]/dd[@id="csrf_token-element"]/input[@name="csrf_token"]/@value').get()

        yield FormRequest.from_response(response, formdata={"csrf_token": csrf_token, "username":USERNAME, "password":PASSWORD}, callback=self.download_data, meta=response.meta, dont_filter=True)


    def download_data(self, response):

        global DOWNLOAD_PATH
        global downloaded
        global LAST_PATH
        global LAST_ROW

        if "ers.cr.usgs.gov/login" in response.url:
            yield scrapy.Request(response.url, callback=self.login_again, meta=response.meta, dont_filter=True)
            return      # return so that the function doesn't try to save the response sent to it

        Path = response.meta['Path']
        Row = response.meta['Row']
        displayId = response.meta['displayId']

        filename = (dict(response.headers)[b'Content-Disposition'][0].decode('ascii').split('filename=')[1])
        filename = DOWNLOAD_PATH + Path + '/' + Row + '/' + filename

        # SAVING DOWNLOADED FILES ONTO THE LOCAL SYSTEM
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as fp:
            fp.write(response.body)

        # print(f'\n\nPATH >>> {Path} ROW >>> {Row} COUNT >>> {response.meta["count"]}\n\n')


        downloaded[Path][Row] -= 1

        if downloaded[Path][Row] <= 0:

            # clearing downloaded dict
            del downloaded[Path][Row]
            if len(downloaded[Path]) == 0:
                del downloaded[Path]

            self.delete_old_data(response.meta['displayId'], response.meta['Path'], response.meta['Row'])

            if Path == LAST_PATH and Row == LAST_ROW:
                custom_functions.set_resume('', '')
            else:
                custom_functions.set_resume(response.meta['Path'], response.meta['Row'])

            # print('\n','*'*20, '\n\n', f'Path {response.meta["Path"]} and Row {response.meta["Row"]} Download completed','*'*20, '\n')


    # also unzips files after download has completed
    def delete_old_data(self, id_, path, row):

        global DOWNLOAD_PATH
        for i in os.listdir(DOWNLOAD_PATH + path + '/' + row + '/'):
            if id_ not in i:
                os.remove(DOWNLOAD_PATH + path + '/' + row + '/' + i)

        # UNZIPPING FILES
        for i in os.listdir(DOWNLOAD_PATH + path + '/' + row + '/'):
            if '.zip' in i:
                with zipfile.ZipFile((DOWNLOAD_PATH + path + '/' + row + '/' + i), 'r') as zip_ref:
                    zip_ref.extractall(DOWNLOAD_PATH + path + '/' + row + '/')

                os.remove((DOWNLOAD_PATH + path + '/' + row + '/' + i))

            elif i.endswith("tar.gz"):
                tar = tarfile.open(i, "r:gz")
                tar.extractall(DOWNLOAD_PATH + path + '/' + row + '/')
                tar.close()
                os.remove((DOWNLOAD_PATH + path + '/' + row + '/' + i))

            elif i.endswith("tar"):
                tar = tarfile.open(i, "r:")
                tar.extractall(DOWNLOAD_PATH + path + '/' + row + '/')
                tar.close()
                os.remove((DOWNLOAD_PATH + path + '/' + row + '/' + i))

            elif i.endswith("tar.bz2"):
                tar = tarfile.open(i, "r:bz2")
                tar.extractall(DOWNLOAD_PATH + path + '/' + row + '/')
                tar.close()
                os.remove((DOWNLOAD_PATH + path + '/' + row + '/' + i))

            elif i.endswith("tar.xz"):
                tar = tarfile.open(i, "r:xz")
                tar.extractall(DOWNLOAD_PATH + path + '/' + row + '/')
                tar.close()
                os.remove((DOWNLOAD_PATH + path + '/' + row + '/' + i))


