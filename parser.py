import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin


class Parser:
    def __init__(self, url=None):
        self.url = url
        self.data = []

    def fetch(self):
        if not self.url:
            raise ValueError("URL не задан")
        response = requests.get(self.url)
        response.raise_for_status()
        return response.text


    def parse(self, html):
        self.data.clear()
        soup = BeautifulSoup(html, 'html.parser')

        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                self.data.append({'type': 'paragraph', 'text': text})

        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            link = urljoin(self.url, a['href'])
            if text or link:
                self.data.append({'type': 'link', 'text': text, 'link': link})


    def get_data(self):
        return self.data


if __name__ == "__main__":
    url = "https://fivethirtyeight.com/features/2024-top-senate-races-chat/"
    parser = Parser(url)
    html = parser.fetch()
    parser.parse(html)
    data = parser.get_data()
    for i, record in enumerate(data, 1):
        print(f"{i}. Автор: {record.get('author_name')}")
        print(f"   Заголовок: {record.get('title')}")
        print(f"   Ссылка: {record.get('link')}")
        print(f"   Дата: {record.get('date')}")
        print(f"   Текст: {record.get('text')[:300]}...")
        print("-----")
