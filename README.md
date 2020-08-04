# EarthExplorer-Downloader
This project is a downloader, which automatically downloads latest Landsat 8 image data from EarthExplorer website and stores it in the local file system. Additionally, it also unzips the data downloaded, and erases any older versions of the data. This project has been made compatible with automatic schedulers.

### Steps to execute this project
1. Install Python packages from the requirements.txt file
2. Setup variable values
   There are 7 variable values which need to be set before execution of the project as follows :-
   
####   In config_file.txt :-
      a) USERNAME - username of account on EarthExplorer website
      b) PASSWORD - password of the account on EarthExplorer website
      c) DOWNLOAD_PATH - full directory path where the downloaded data has to be stored
      d) DATA_DICT_PATH - directory path where dictionary of satellite data will be stored
   
####   In custom_functions.py :-
      a) CONFIG_FILE_PATH - full path of the config_file.txt above
      b) ERROR_LOG - path of file which will be used as error log by the project
      c) RESUME_LOG - path of file where the path and row info of currently downloaded file will be stored
   
      Files included in this repo contain example of the format in which you have to enter data into these files. Make sure to enter data in the same format as given in the example
   
3. Execute the create_data_dict.py file.
4. Open earthexplorer/spiders directory and run scrapy crawl revised_data_downloader

### Note:- 
    1. This project supports only Python 3.6 or higher versions
    2. If this project is executed using crontab or other automated schedulers, it is advised to use output redirection in order to preserve the output of the project, to check for error in case the program terminates because of some error
    3. The error file in this project is purposefully not cleared before execution, so that in case automatic scheduling is used to execute the project, then we should be able to check the errors made later on.
    4. **IMPORTANT - There was an update in the website layout of the EarthExplorer website, and therefore for those people who are executing "scrapy crawl data_downloader", this command will not work anymore. Download the revised-downloader.py file from earthexplorer/spiders directory and place it in the same directory in your local project. Now execute "scrapy crawl revised_data_downloader"**
