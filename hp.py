import requests
import re
import urllib.parse
import threading
from queue import Queue
import csv
import time
BIAOTOU = [['视频名称'],['关注数'],['发布时间'],['id'],['用户名'],['播放量'],['弹幕量'],['点赞量'],['投币量'],['收藏量'],['转发量'],['分区1'],['分区2']]
HEADERS = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Referer":"https://search.bilibili.com/all?keyword=%E7%AE%80%E5%8E%86%E6%A8%A1%E6%9D%BF"
    }
class Producer(threading.Thread):
    def __init__(self, url_queue, data_queue, *args, **kwargs):
        super(Producer, self).__init__(*args, **kwargs)
        self.url_queue = url_queue
        self.data_queue = data_queue
    def run(self):
        while True:
            if self.url_queue.empty():  #判断队列是否为空
                break
            z_url,ff = self.url_queue.get() #将队列中的最后一个url取到
            self.parse_page(z_url,ff)
    def parse_page(self,z_url,ff):
        #动态数据
        response1 = requests.get(z_url, headers=HEADERS)
        z_text= response1.text

        up_id = re.findall(r'"mid":(.*?),', z_text)
        up_username = re.findall(r'"name":(.*?),', z_text)
        video_playback_num = re.findall(r'"view":(.*?),', z_text)
        video_barrage_num = re.findall(r'"danmaku":(.*?),', z_text)
        video_like_num = re.findall(r'"like":(.*?),', z_text)
        video_coin_num = re.findall(r'"coin":(.*?),', z_text)
        video_favorite_num = re.findall(r'"favorite":(.*?),', z_text)
        video_forward_num = re.findall(r'"share":(.*?),', z_text)
        #print(video_coin_num)
        #静态数据
        ff = re.sub("//","https://",ff)
        response2= requests.get(ff,headers=HEADERS)
        text_2 = response2.text
        up_follow_num = re.findall(r'<i\sclass="van-icon-general_addto_s".*?>'
                                   r'.*?<span>(.*?)</span>', text_2, re.DOTALL)
        video_name = re.findall(r'<h1\s.*? class="video-title">.*?'
                                r'<span\sclass=.*?>(.*?)</span>', text_2, re.DOTALL)
        video_published_at = re.findall(r'<div\sclass="video-data">.*?<span>(.*?)</span>', text_2, re.DOTALL)[0]
        categroy_1 = re.findall(r'div\sclass="video-data".*?<a.*?>(.*?)</a>', text_2, re.DOTALL)[0]
        categroy_2 = re.findall(r'i\sclass="van-icon-general_enter_s".*?<a.*?>(.*?)</a>', text_2, re.DOTALL)[0]
        self.data_queue.put((video_name, up_follow_num, video_published_at,up_id,up_username,video_playback_num,video_barrage_num,video_like_num,
                             video_coin_num,video_favorite_num,video_forward_num,categroy_1, categroy_2,))
        time.sleep(1)
class Consumer(threading.Thread):
    def __init__(self, url_queue, data_queue, search_term,*args, **kwargs):
        super(Consumer, self).__init__(*args, **kwargs)
        self.url_queue = url_queue
        self.data_queue = data_queue
        self.search_term = search_term
    def run(self):
        while True:
            if self.url_queue.empty() and self.data_queue.empty():
                break
            qw = []
            qw.append(self.data_queue.get())
            with open("%s信息.csv" % self.search_term,'a',encoding='gbk',newline='')as fp:
                write = csv.writer(fp)
                write.writerows(qw)
                fp.close()

if __name__ == '__main__':
    search_terms = ["简历","简历模板","面试","实习","找工作","笔试","职场"]
    for search_term in search_terms:
        with open("{}信息.csv".format(search_term),'w',encoding='gbk',newline="")as fp:
            write = csv.writer(fp)
            write.writerow(BIAOTOU)
            fp.close()
        s = search_term
        s = urllib.parse.quote(s)
        url = "https://search.bilibili.com/all?keyword={}&page=1".format(s)


        url_queue = Queue(1000000000)
        data_queue = Queue(1000000000)
        #解析数据
        response = requests.get(url,headers=HEADERS)
        print(response.status_code)
        text = response.text

        #获取动态数据
        dds = re.findall(r'<li class="video-item matrix">.*?<a href=".*?/video/(.*?)\?from.*?>',text,re.DOTALL)
        z_urls = []
        for dd in dds:
            z_url = "https://api.bilibili.com/x/web-interface/view?cid=82176178&bvid={}".format(dd)
            z_urls.append(z_url)
        #静态数据
        ffs = re.findall(r'<li\sclass="video-item matrix">.*?<a\shref="(.*?)".*?>',text,re.DOTALL)
        for i in range(len(z_urls)):
            url_queue.put((z_urls[i],ffs[i]))

        for x in range(5):
            t1 = Producer(url_queue, data_queue)
            t1.start()

            t2 = Consumer(url_queue,data_queue,search_term)
            t2.start()
        time.sleep(1)
