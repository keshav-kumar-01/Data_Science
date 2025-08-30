# Web scrapping via multi threading
# https://python.langchain.com/docs/tutorials/rag/
# https://python.langchain.com/docs/introduction/
# https://python.langchain.com/docs/tutorials/
import threading 
import requests
from bs4 import BeautifulSoup

urls = [
    'https://python.langchain.com/docs/tutorials/rag/',
    'https://python.langchain.com/docs/introduction/',
    'https://python.langchain.com/docs/tutorials/'
]

def fetch_contents(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    print(f'Fetched {len(soup.text)} characters from {url}')

threads = []
for url in urls:
    thread = threading.Thread(target=fetch_contents, args=(url,))  # <-- add comma
    threads.append(thread)  # <-- fixed
    thread.start()

for thread in threads:
    thread.join()

print("All webpages are fetched ✅")
