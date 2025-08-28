import requests
from bs4 import BeautifulSoup

url = "https://pypi.org/simple/"

payload = ""
headers = {"User-Agent": "insomnia/11.4.0"}

response = requests.request("GET", url, data=payload, headers=headers)
html_data = response.text
soup = BeautifulSoup(html_data, 'html.parser')
library_list = [tag.get_text() for tag in soup.find_all('a')]
