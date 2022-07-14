import requests 
import json
import os 
from clint.textui import progress
from bs4 import BeautifulSoup
import datetime
import argparse
import sys

def _iterate_months(start_date, end_date):
    assert isinstance(start_date, datetime.date)
    assert isinstance(end_date, datetime.date)
    assert start_date < end_date

    year = start_date.year
    month = start_date.month
    while True:
        current = datetime.date(year, month, 1)
        yield current
        if current.month == end_date.month and current.year == end_date.year:
            break
        else:
            month = ((month + 1) % 12) or 12
            if month == 1:
                year += 1

def _datify(date):
    if isinstance(date, datetime.date):
        return date
    elif isinstance(date, datetime.datetime):
        return date.date()
    else:
        # taken from simleo's answer
        return datetime.datetime.strptime(date, "%Y-%m-%d")

def _format_month(date):
    return date.strftime(r"%m-%y")

def getAllDownloadUrls(startmonth="01",startyear="2017",endmonth="12",endyear="2022"):
    startDate = _datify(startyear+"-"+startmonth+"-"+"01")
    endDate = _datify(endyear+"-"+endmonth+"-"+"01")
    
    result = []

    #Get all dates between two months
    l = list(_iterate_months(startDate,endDate)) 
    dates = list(_format_month(entry) for entry in l)

    baselineUrl= 'https://eogdata.mines.edu/nighttime_light/monthly/v10/'
    print("You will have to download " +str(len(dates))+ " Products")
    for date in dates:
        [month,year]=date.split("-")
        year = "20"+year
        url = baselineUrl+year+"/"+year+month+"/vcmcfg/"
        # Request url 
        response = requests.get(url)
        # Find the file we are interested in
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if "75N060W" in link.get('href'):
                downloadUrl = url+link.get('href')                
        result.append(downloadUrl)
    return result 

def download(url,storage_dir="./"):

    # Create storage directory
    if not os.path.isdir(storage_dir):
        os.mkdir(storage_dir)



    params = {
        'client_id':'eogdata_oidc',
        'client_secret' : '2677ad81-521b-4869-8480-6d05b9e57d48',
        'username':'kostantinosst23@gmail.com',
        'password':'.dinos123a',
        'grant_type': 'password'
    }
    token_url = 'https://eogauth.mines.edu/auth/realms/master/protocol/openid-connect/token'
    response = requests.post(token_url, data = params)
    access_token_dict = json.loads(response.text)
    
    access_token = access_token_dict.get('access_token')
    auth = 'Bearer ' + access_token
    headers = {'Authorization' : auth} 
    print("Download will begin shortly")
    response = requests.get(url, headers = headers,stream=True)
    total_length = int(response.headers.get('content-length'))
    output_file = os.path.join(storage_dir,os.path.basename(url)) 
    #os.path.basename(storage_dir+""+url)
    print(output_file)
    with open(output_file,'wb') as f:
        for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
                if chunk:
                    f.write(chunk)
                    f.flush()

    return url 

def getAllDownloadSubUrls(f):
    result=[]
    try:
        with open(f,'r') as f:
            textFiles = f.readlines()
            for url in textFiles:
                url=url.replace(".tif",".tgz")
                url=url.replace("_cropped","")
                #url.split("_")
                year = url [10:14]
                month = url[14:16]
                baseUrl = "https://eogdata.mines.edu/nighttime_light/monthly/v10/"+year+"/"+year+month+"/vcmslcfg/"
                l = url.split("_")
                l[4] = "vcmslcfg"
                newLink = "_".join(l).replace("\n","")
                finalUrl = baseUrl+newLink
                result.append(finalUrl)
        return result 
    except:
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download data regarding Nightlights VIIRS')
    parser.add_argument('--startdate', metavar='startdate', type=str,
                        help='Starting date with the format dayyear, i.e. 062021')

    parser.add_argument('--enddate', metavar='enddate', type=str, 
                        help='Ending date with the format dayyear, i.e. 062021')
    

    parser.add_argument('--saveDir',metavar='savedir',type=str,
                    help='Directory to save the downloaded images, i.e. --saveDir storage will create a storage folder in the current directory')
    
    parser.add_argument('--resume',metavar='resume',choices=["False","True"],
                        help='Skip some files if they have been already downloaded successfully (already downloaded files are in savedproducts.txt')

    parser.add_argument('--corrupted',metavar='corrupted',choices=["True","False"],
                        help= "Set to True if you have a corruptedtifs.txt with the files you need to download stray light images for")
    

    #parser.add_argument('--')

    args = parser.parse_args()
    
    # Run for corrupted files only
    if args.corrupted=="True":
        straylightUrls = getAllDownloadSubUrls("corruptedtifs.txt")

        try:
            avoidParsing=[]
            with  open("savedproducts.txt",'r') as f:
                alreadyParsed = f.readlines()
                for url in alreadyParsed:
                    url=url.replace("\n","")
                    avoidParsing.append(url)
                avoidParsing = set(avoidParsing)
        except:
                avoidParsing=set()
        if straylightUrls==None:
            print("Check if there is a corruptedfiles.txt")
            sys.exit(0)
        
        print("Downloading "+ str(len(straylightUrls))+ " stray light files")
        for url in straylightUrls:
            
            # Used to avoid if files have been downloaded already
            if url in avoidParsing:
                continue
            if args.saveDir != None:
                print(url)
                download(url,args.saveDir)
            else:
                print(url)
                download(url,"straylights")
            with open("savedproducts.txt",'a+') as f:
                f.write(url)
                f.write("\n")

    # Run for non-corrupted files
    else:
        if args.startdate:
            startyear = args.startdate[2:6]
            startmonth = args.startdate[0:2]
        else:
            sys.exit("You need to define starting month and year")
        
        if args.enddate:
            endyear = args.enddate[2:6]
            endmonth = args.enddate[0:2]
        else:
            sys.exit("You need to define ending month and year")
        
        # Check if we have already downloaded some files
        if args.resume=="True":
            avoidParsing = []
            try:
                with  open("savedproducts.txt",'r') as f:
                    alreadyParsed = f.readlines()
                    for url in alreadyParsed:
                        url=url.replace("\n","")
                        avoidParsing.append(url)
                avoidParsing = set(avoidParsing)
            except:
                avoidParsing=set()
        
        # Get all urls that need to be downloaded
        urls = getAllDownloadUrls(startmonth=startmonth,startyear=startyear,endmonth=endmonth,endyear=endyear)
        print("Downloading will begin shortly")
        for i,url in enumerate(urls):
            #download(url,args.saveDir)
            if args.resume=="True":
                if url in avoidParsing:
                    continue
            download(url,args.saveDir)
            print("url download was completed")
            with open("savedproducts.txt",'a+') as f:
                f.write(url)
                f.write("\n")
    
    

