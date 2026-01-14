import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

import demjson3
from SegmentsDownload import Downloader


class Missav:
    def __init__(self):
        self.session = requests.Session()
        self.downloader = Downloader()

    def get_html(self, url):
        '''
        Get html of the url that you want to download
        '''
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        html = driver.page_source
        driver.quit()
        return html
    
    def get_playlist_url(self, html):
        '''
        From html, get a url that is to get playlist urls
        '''
        pattern = re.compile(r"let playerSettings(_\w+)?\s*=")  # flashvarsまたはflashvars_〇〇にマッチ
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script"):
            if script.string and pattern.search(script.string):
                match = re.search(r'let\s+playerSettings\s*=\s*({[\s\S]*?});', script.string)

                if match:
                    js_object_str = match.group(1)
                try:
                    data = demjson3.decode(js_object_str)
                    # Get id from: https:\/\/nineyu.com\/6d41075c-7ded-4650-bfa7-b8b3af8c2d38\/seek\/_0.jpg
                    return f'https://surrit.com/{data['thumbnail']['urls'][0].split('/')[3]}/playlist.m3u8'
                except demjson3.JSONDecodeError as e:
                    print("Decode error:", e)

    def get_master_urls(self, playlist_url):
        '''
        Get master urls
        '''
        res = self.session.get(playlist_url)
        if res.status_code == 200:
            video_paths = re.findall(r'^(?!#).+', res.text, re.MULTILINE)
            base_url = playlist_url.rsplit('/', 1)[0]
            master_urls = [f'{base_url}/{video_path}' for video_path in video_paths]
            return master_urls
        return None

    def get_segment_urls(self, master_url) -> list:
        '''
        Get urls that are video segments
        '''
        res = self.session.get(master_url)
        if res.status_code == 200:
            video_paths = re.findall(r'^(?!#).+', res.text, re.MULTILINE)
            base_url = master_url.rsplit('/', 1)[0]
            segment_urls = [f'{base_url}/{video_path}' for video_path in video_paths]
            return segment_urls
        return None

    def get_safe_title(self, html, max_length=150):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1")
        if max_length:
            return re.sub(r'[\\/*?:"<>|\'() ]', '_', title.text)[:max_length]
        return re.sub(r'[\\/*?:"<>|\'() ]', '_', title.text)
    
    def run(self, url, path):
        html = self.get_html(url)
        title = self.get_safe_title(html, max_length=150)
        playlist_url = self.get_playlist_url(html)
        master_urls = self.get_master_urls(playlist_url)
        # The last one is highest resolution
        master_url = master_urls[-1]
        segment_urls = self.get_segment_urls(master_url)
        self.downloader.get_video(segment_urls, path, title)


if __name__ == '__main__':
    app = Missav()
    app.run()
    