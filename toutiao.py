import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
from bs4 import BeautifulSoup
import re
import pymongo
import os
from multiprocessing import Pool
from hashlib import md5
from com.it.ttconfig import *
client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]
def getHtml(Url):
    try:
        Myhtml = requests.get(Url,headers=Myheader)
        if Myhtml.status_code == 200:
            return Myhtml.text
        return "getHtmlerror"
    except RequestException:
        return "getHtmlerror"

def getStr(Myhtml):
    Data = json.loads(Myhtml)
    if Data and "data" in Data.keys():
        for url1 in Data.get("data"):
            yield url1.get("share_url")

def getDetail(Url1):
    try:
        Myhtml = requests.get(Url1,headers=Myheader)
        if Myhtml.status_code == 200:
            return Myhtml.text
        return "getDetailHtmlerror"
    except RequestException:
        print("Url1 error")
        return "getDetailHtmlerror"

def getStr2(Myhtml2,Url1):
    Bs4html = BeautifulSoup(Myhtml2,"lxml")
    Mytitle = Bs4html.select("title")[0].get_text()
    Myrule = re.compile("BASE_DATA.galleryInfo.*?gallery:(.*?),\n\s*?siblingList",re.S)
    Mystr2 = re.search(Myrule,Myhtml2)
    if Mystr2:
        json_str2 = json.loads(Mystr2.group(1))
        if json_str2 and "sub_images" in json_str2.keys():
            sub_image = json_str2.get("sub_images")
            image = [x.get("url") for x in sub_image]
            for imageurlone in image:downLoad(imageurlone)
            return {"title":Mytitle,"imageurl":image,"Url":Url1}
        return "url2error"
    return "url2error"

def saveMongo(imageurl):
    if db[MONGO_TABLE].insert(imageurl):
        print("url save to mongodb ok")
        return True
    return False

def downLoad(imageurlone):
    try:
        Myhtml = requests.get(imageurlone,headers=Myheader)
        if Myhtml.status_code == 200:
            saveImage(Myhtml.content)
        return "getHtmlerror"
    except RequestException:
        print("downloadImagError")
        return "getHtmlerror"

def saveImage(content):
    path = "{0}/{1}.{2}".format(os.getcwd()+"/image",md5(content).hexdigest(),"jpg")
    if not os.path.exists(path):
        with open(path,"wb") as f:
            f.write(content)
            f.close()
        print("downimage successful:"+ path)

def main(Offset):
    Data = {'offset': Offset, 'format': 'json', 'keyword': Find, 'autoload': 'true', 'count': '20', 'cur_tab': '1'}
    Url = "http://www.toutiao.com/search_content/?" + urlencode(Data)
    Myhtml = getHtml(Url)
    for Url1 in getStr(Myhtml):
        Myhtml2 = getDetail(Url1)
        imageurl = getStr2(Myhtml2,Url1)
        if imageurl != "url2error":
            saveMongo(imageurl)

if __name__ == "__main__":
    page = [i*20 for i in range(0,6)]
    pool = Pool()
    pool.map(main,page)
