import os
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from normalization.normalization import Normalizer

directory = "./news"
chanels = os.listdir(directory)

client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_data']


def parse_date(date_str):
    date_format = '%d.%m.%Y %H:%M:%S %Z%z'
    return datetime.strptime(date_str, date_format)


def clean_text(text):
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[\U0001F600-\U0001F64F'  # Emoticons
                  r'\U0001F300-\U0001F5FF'  # Symbols & Pictographs
                  r'\U0001F680-\U0001F6FF'  # Transport & Map Symbols
                  r'\U0001F700-\U0001F77F'  # Alchemical Symbols
                  r'\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
                  r'\U0001F800-\U0001F8FF'  # Supplemental Arrows Extended-A
                  r'\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
                  r'\U0001FA00-\U0001FA6F'  # Chess Symbols
                  r'\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
                  r'\U00002702-\U000027B0'  # Dingbats
                  r'\U000024C2-\U0001F251'  # Enclosed Alphanumeric Supplement
                  r']+', '', text)

    text = text.strip()
    text = normalize_persian(text)
    return text


def normalize_persian(text):
    normalizer = Normalizer()
    return normalizer.normalize_str(text)


def process_directory(directory, db, collection):
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            file_path = os.path.join(directory, filename)
            print(f"Processing file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                    messages = soup.find_all('div', class_='message default clearfix')
                    for message in messages:
                        date_tag = message.find('div', class_='pull_right date details')
                        if date_tag:
                            date_str = date_tag['title']
                            try:
                                date = parse_date(date_str)
                            except ValueError as e:
                                print(f"Error parsing date: {date_str} - {e}")
                                date = None
                        else:
                            date = None
                        text_tag = message.find('div', class_='text')
                        if text_tag:
                            text = text_tag.get_text(separator=' ', strip=True)
                            text = clean_text(text)
                        else:
                            text = None
                        if date and text:
                            document = {
                                'date': date,
                                'Message': text
                            }
                            collection.insert_one(document)
            except:
                continue


x = directory + "\\" + chanels[-2]
collection = db[chanels[-2]]
process_directory(x, db, collection)
