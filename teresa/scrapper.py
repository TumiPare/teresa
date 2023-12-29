import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from urllib.parse import urlparse, parse_qsl, urlencode, urljoin
from oliver_dl import Downloader
import base64
import json


session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = requests.adapters.HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

site = "https://viewasian.co"

search = input("Search Kdrama: ")
search_url = "https://viewasian.co/movie/search/" + search.replace(" ", "-")

r = session.get(search_url)


soup = BeautifulSoup(r.content, "html.parser").select('.movies-list')
a_tags = soup[0].find_all("a", {"class": "ml-mask jt"})
for index, tag in enumerate(a_tags):
    print(f"[{index}] {tag['title']}")

show = input("Choose a show: ")


episode = input("Choose an episode: ")

url = site + a_tags[int(show)].get("href").replace('/drama', '/watch') + "/watching.html?ep=" + episode
page = session.get(url)
soup = BeautifulSoup(page.content, "html.parser").select('#media-player')
iframe =  soup[0].find("iframe")
iframe_url = "https:" + iframe['src']

a = 0
b = "93422192433"
c = "42908585752"
d = "9524897523"
e = b + d + c
f = "9262859"
g = "5825"
h = "23243"
i = f + h + g

response = session.get(iframe_url)
soup = BeautifulSoup(response.content, "html.parser")

crypto = soup.find("script", {"data-name": "crypto"})
crypto_script_value = crypto["data-value"]

key = e.encode('utf-8')
iv = i.encode('utf-8')

def aes_encrypt(data, key, iv):
        pad = lambda s: s + chr(len(s) % 16) * (16 - len(s) % 16)
        return base64.b64encode(
            AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pad(data).encode())
        )

def aes_decrypt(data, key, iv):
        return (
            AES.new(key, AES.MODE_CBC, iv=iv)
            .decrypt(base64.b64decode(data))
            .strip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
        )

decrypted_value = aes_decrypt(crypto_script_value,key,iv)
decrypted_value = dict(parse_qsl(decrypted_value))

id = urlparse(iframe_url).query
id = dict(parse_qsl(id))["id"]
enc_id = aes_encrypt(id, key, iv).decode()
decrypted_value.update(id=enc_id)

url = f" https://draplay2.pro/encrypt-ajax.php?id={urlencode(decrypted_value)}&alias={id}"

final_response = session.get(url).json().get("data")
json_resp = json.loads(
            aes_decrypt(
                final_response, key, iv
            )
        )


m3u8_url = json_resp['source'][0]['file']
print(m3u8_url)
Downloader(m3u8_url).save()





