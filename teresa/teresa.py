import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from urllib.parse import urlparse, parse_qsl, urlencode, urljoin
from oliver_dl import Downloader
import base64
import json
import subprocess
import argparse

class teresa: 
    site = "https://viewasian.co"
    def __init__(self):       
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def cli(self):
        search_query = input("Search Kdrama: ")
        search_results = self.search(search_query )
 
        for index, tag in enumerate(search_results):
            print(f"[{index}] {tag['title']}")

        show = input("Choose a show: ")
        show_url = self.site + search_results[int(show)]["href"].replace('/drama', '/watch') + "/watching.html"
        ep_range = self.get_ep_range(show_url)
        episode = input(f"Choose an episode[{ep_range}]: ")
    
        m3u8_url = self.get_link(show_url, episode)
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-d","--download", action="store_true", help="download the episode")
        parser.add_argument("-l","--link", action="store_true", help="get the link to the episode")
        args = parser.parse_args()
        if args.download:
            self.download(m3u8_url)
        elif args.link:
            print(m3u8_url)
        else:
            self.stream(m3u8_url)
        
    def get_ep_range(self,show_url):
        page = self.session.get(show_url)
        soup = BeautifulSoup(page.content, "html.parser").find_all('li', class_='ep-item')
        last = soup[0]["id"]
        first = soup[-1]["id"]

        return f"{first}-{last}"

    def search(self, query):
        search_url = "https://viewasian.co/movie/search/" + query.replace(" ", "-")
        r = self.session.get(search_url)
        soup = BeautifulSoup(r.content, "html.parser").select('.movies-list')
        if len(soup) == 0:
            print("No results found")
            exit()
        a_tags = soup[0].find_all("a", {"class": "ml-mask jt"})
        bobby = [];
        for tag in a_tags:
            bobby.append({
                "href": tag.get("href"),
                "title": tag.get("title")
            })
        return bobby

    def aes_encrypt(self, data, key, iv):
                pad = lambda s: s + chr(len(s) % 16) * (16 - len(s) % 16)
                return base64.b64encode(
                    AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pad(data).encode())
                )

    def aes_decrypt(self, data, key, iv):
            return (
                AES.new(key, AES.MODE_CBC, iv=iv)
                .decrypt(base64.b64decode(data))
                .strip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
            )
           
    def get_link(self, url,episode):
        url = url + "?ep=" + episode
        page = self.session.get(url)
        soup = BeautifulSoup(page.content, "html.parser").select('#media-player')
        iframe =  soup[0].find("iframe")
        iframe_url = "https:" + iframe['src']

        response = self.session.get(iframe_url)
        soup = BeautifulSoup(response.content, "html.parser")
        crypto = soup.find("script", {"data-name": "crypto"})
        crypto_script_value = crypto["data-value"]

        key = "93422192433952489752342908585752".encode('utf-8')
        iv = "9262859232435825".encode('utf-8')

        decrypted_value = self.aes_decrypt(crypto_script_value,key,iv)
        decrypted_value = dict(parse_qsl(decrypted_value))

        id = urlparse(iframe_url).query
        id = dict(parse_qsl(id))["id"]
        enc_id = self.aes_encrypt(id, key, iv).decode()
        decrypted_value.update(id=enc_id)

        url = f"https://draplay2.pro/encrypt-ajax.php?id={urlencode(decrypted_value)}&alias={id}"
        print(url)
        
        final_response = self.session.get(url).json().get("data")
        json_resp = json.loads(
                    self.aes_decrypt(
                        final_response, key, iv
                    )
                )

        m3u8_url = json_resp['source'][0]['file']
        return m3u8_url

    def stream(self,link):
        subprocess.run(["mpv", link], check=True)

    def download(self,link):
        Downloader(link).save()





