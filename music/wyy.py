import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from threading import Thread
from queue import Queue

class WYY(object):
    def __init__(self):
        # 榜单id
        # 飙升榜：19723756
        # 新歌榜：3779629
        # 原创榜：19723760
        # 热歌榜：3778678
        self.url = 'https://music.163.com/#/playlist?id=19723756'
        self.download_url = 'https://music.163.com/song/media/outer/url?id={}.mp3'
        self.headers = {
            'Cookie': 'NMTID=00OxfwD_E_FsNExgU6nm2eIXWb-9zUAAAGVrt3Yaw; JSESSIONID-WYYY=a7HDO7Bu%2BYIfQYk%5CbGRVPncbUqJ17GD68oNx%5CyjSY06Fl%2FK6B0D9PT%2FHPjBZa1V%5CxzCcQgMu07x20J0%5C3J%2Bd0njZ%2FlDxwKsb6%2BGFC8d4RRFw0QU%2B%2F3MYZ3bwdio3pjSZH4%5C3jqKe%5CcnPnyEnsP6BjnKxY9cCyWPxOgxh1esHOGr%2FkXCc%3A1742397329527; _iuqxldmzr_=32; _ntes_nnid=2fb5bec4131e6c7718a8fa6a63484ce3,1742395529568; _ntes_nuid=2fb5bec4131e6c7718a8fa6a63484ce3; WEVNSM=1.0.0; WNMCID=hvsmwn.1742395531950.01.0; WM_NI=KcOsMYdRjEtx%2BCtABRdJkjEWqMPrhzLlsWIivKTpha96VqhjU8pFBb0uLLhOoeAV8JG8uthR8o%2FyOKw%2FuhcikfHDbI%2FXbyTlIf%2FcQtFNnPYaV8mNllT57JXNwKFGGU%2F4WVc%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6ee8cf53fb4a9fcb6db53afb48ba6d15b879a9ab1d253b8b7f8dab66ab4b88997bb2af0fea7c3b92a89bd8194d053a88ea6a6f774e99dbca2c15aa896a58bc85db393a093eb7290b4bdb8cc63b6959c91eb6bfbea9a92eb6297e8c0a7c16af4ab84adeb45adbb8fb7bb4285e8bb95eb5afcb1e19ace41b5f1bb89e263a9ba88a5e143ed88ae9ad7688bbae184d4808692a2b1dc6b96e8a3afef6898ebf9abdb46b5958aa8c65fedec99b7e237e2a3; WM_TID=mRDsbuk05BZEQVVBAAfHY5z5p%2FKpxS6s; sDeviceId=YD-5cWj68tlwmdBRxQBAEKAwzkMZuzX1Ojc; ntes_utid=tid._.EoVCTRgd2JxFQhUUBRaXNp3p4rPpyLIK._.0',
            'Referer': 'https://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }
        self.filepath_name = '网易云音乐'
        self.queue = Queue()
        
        if not os.path.exists(self.filepath_name):
            os.mkdir(self.filepath_name)
    
    def get_song_info(self):
        """
        获取歌曲信息
        """
        driver = None
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get(self.url)
    
            # 等待iframe加载完成
            iframe = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "g_iframe"))
            )
            # 切换到iframe
            driver.switch_to.frame(iframe)
            print('切换成功--iframe')
    
            table = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.m-table"))
            )
            print('加载成功--音乐表格')
    
            trs = WebDriverWait(table, 3).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr"))
            )
            print('加载成功--音乐列表')
            time.sleep(2)
            print('开始获取歌曲信息\n')
    
            for tr in trs:
                try:
                    song_name_el = WebDriverWait(tr, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(2) span.txt b"))
                    )
                    song_name = song_name_el.get_attribute('title')
                    song_id = tr.find_element(By.CSS_SELECTOR, "td:nth-child(2) span.txt a").get_attribute('href').split('=')[-1]
                    singer = tr.find_element(By.CSS_SELECTOR, "td:nth-child(4) div.txt").get_attribute('title')
    
                    print(f'找到歌曲：{song_name}\n歌手：{singer}\n歌曲id：{song_id}\n\n')
                    self.queue.put({'song_id': song_id, 'song_name': song_name, 'singer': singer})
                except Exception as e:
                    print(f'获取歌曲信息失败：{e}')
        except Exception as e:
            print(f'获取歌曲信息时出现异常：{e}')
        finally:
            if driver:
                driver.quit()
            self.queue.put(None)

    def download(self):
        while True:
            song = self.queue.get()
            if song is None:
                self.queue.task_done()
                break
            song_id = song['song_id']
            song_name = song['song_name']
            singer = song['singer']
            try:
                resp = requests.get(url=self.download_url.format(song_id), headers=self.headers)
                if resp.status_code == 200:
                    valid_filename = re.sub(r'[\\/:*?"<>|]', '.', f'{song_name}__{singer}.mp3')
                    with open(f'{self.filepath_name}/{valid_filename}', 'wb') as f:
                        f.write(resp.content)
                    print(f'下载成功：{song_name}')
                else:
                    print(f'下载失败：{song_name}，状态码：{resp.status_code}')
            except requests.RequestException as e:
                print(f'下载失败：{song_name}，错误信息：{e}')
            self.queue.task_done()

    def run(self):
        t1 = Thread(target=self.get_song_info)
        t2 = Thread(target=self.download)
        t1.start()
        t2.daemon = True
        t2.start()
        t1.join()
        self.queue.join()

if __name__ == '__main__':
    WYY().run()