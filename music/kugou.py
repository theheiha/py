import requests
import re
import json
import os
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue


class Kugou(object):
    def __init__(self):
        self.rank_url = 'https://www.kugou.com/yy/html/rank.html'
        self.download_url = 'https://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash={}'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }
        self.queue = Queue()
        self.filepath_name = '酷狗音乐'

        if not os.path.exists(self.filepath_name):
            os.mkdir(self.filepath_name)

    def get_rank(self):
        """
        获取酷狗音乐排行榜
        """
        res = requests.get(url=self.rank_url, headers=self.headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        rank_html_list = soup.select('div.pc_rank_sidebar > ul > li > a')
        rank_list = [{'title': i.get('title'), 'url': i.get('href')} for i in rank_html_list]

        for rank in rank_list:
            self.get_song(rank['url'])
            break

    def get_song(self, url):
        res = requests.get(url=url, headers=self.headers)
        song_list = self.get_song_list(res.content.decode('utf-8'))
        for song in song_list:
            print(f'找到歌曲：{song["FileName"]}')
            self.queue.put(song)

    def get_song_list(self, content):
        """
        通过正则获取到歌曲列表数据
        """
        pattern = r'global.features = \[({.*?})\]'
        match = re.search(pattern, content, re.S)
        song_list = []
        if match:
            list_str = f"[{match.group(1)}]"
            try:
                song_list = json.loads(list_str)
                return song_list
            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}")
                return song_list
        else:
            print("未找到匹配的内容")
            return song_list

    def get_download_url(self):
        """
        获取歌曲下载地址
        """
        while True:
            song = self.queue.get()
            name = song['FileName']
            hash_val = song['Hash']
            res = requests.get(url=self.download_url.format(hash_val), headers=self.headers)
            if res.status_code == 200:
                data = res.json()
                url = data.get('url')
                error = data.get('error')
                if url:
                    self.download(name, url)
                else:
                    print(f'链接获取失败--{error}')
            else:
                print(f'链接获取失败--接口失败--{name}')
            self.queue.task_done()

    def download(self, name, url):
        """
        下载歌曲
        """
        try:
            res = requests.get(url=url, headers=self.headers)
            if res.status_code == 200:
                with open(f'{self.filepath_name}/{name}.mp3', 'wb') as f:
                    f.write(res.content)
                    print(f'下载成功--{name}')
            else:
                print(f'下载失败--{name}')
        except Exception as e:
            print(f'下载出错--{name}: {e}')

    def run(self):
        t1 = Thread(target=self.get_rank)
        t2 = Thread(target=self.get_download_url)
        t1.start()
        t2.daemon = True
        t2.start()
        t1.join()
        # 等待所有任务完成
        self.queue.join()

if __name__ == '__main__':
    k = Kugou()
    k.run()