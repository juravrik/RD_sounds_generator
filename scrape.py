import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from time import sleep


with open('headers.json') as f:
  headers = json.load(f)

save_path = './lyrics/'
index_url = "https://www31.atwiki.jp/touhoukashi/pages/527.html"


def get_content(url):
  resp = requests.get(url, timeout=1, headers=headers)

  try:
    soup = BeautifulSoup(resp.text, "lxml")
  except:
    soup = BeautifulSoup(resp.text, "html5lib")

  meta = soup.find_all('meta',
                     attrs={"name":"robots"},
                     content=lambda x: "nofollow" in str(x).lower() or "noarchive" in str(x).lower())

  s = str(resp.headers.get("X-Robots-Tag"))
  if meta != [] and ("nofollow" in s) and ("noarchive" in s):
    raise Exception

  for comment in soup(text=lambda x: isinstance(x, Comment)):
    comment.extract()

  if soup.blockquote is not None:
    soup.blockquote.decompose()

  return soup


def write_lyrics(url, album, title):
  soup = get_content(url)
  lyrics = " ".join(soup.find(id="lyrics").stripped_strings).replace("\u3000", " ")

  Path(save_path+album+(title.replace('/', ''))+'.txt').write_text(lyrics)

def access_lyrics(url, album):
  soup = get_content(url)

  for s in soup.find(id="wikibody").find_all("h3"):
    sleep(1)
    content = s.find("a")

    if content is not None:
      write_lyrics("https:"+content.get("href"), album, content.string[3:])

def access_album():
  soup = get_content(index_url)

  for s in soup.table.find_all("a"):
    sleep(1)
    album = s.get("title")[0]
    print(album)
    try:
      Path(save_path+album).mkdir()
    except:
      pass
    access_lyrics("https:"+s.get("href"), album+"/")


if __name__ == '__main__':
  access_album()

:q
:q
:q!



