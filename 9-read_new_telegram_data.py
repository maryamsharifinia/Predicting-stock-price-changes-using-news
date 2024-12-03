import re
import time
from datetime import datetime
import random

import dill
from deep_translator import GoogleTranslator
from pymongo import MongoClient
import torch
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest, SendMessageRequest, UpdatePinnedMessageRequest
from telethon.tl.types import PeerChannel

from normalization.normalization import Normalizer

number = "@badbakht_lit"


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


with open(r"C:\Users\mobin.DESKTOP-KS1RI2E\Downloads\functions.dill", 'rb') as file:
    loaded_function_dict = dill.load(file)

calculate_finbert_sentiment = loaded_function_dict.get('calculate_finbert_sentiment')
finbert_model = loaded_function_dict.get("finbert_model")
tokenizer_finbert = loaded_function_dict.get("tokenizer_finbert")
model_finbert = loaded_function_dict.get("model_finbert")


# تابع ترجمه
def translate_to_english(text, index, total):
    try:
        translation = GoogleTranslator(source='fa', target='en').translate(text)
        print(f"Translating {index + 1}/{total}...")
        return translation
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


async def forward_message_to_user(user_id, message_id, from_channel, message=None):
    try:
        # تبدیل ID به موجودیت تلگرام
        user = await client.get_input_entity(user_id)

        # فوروارد پیام
        await client.forward_messages(entity=user, messages=message_id, from_peer=from_channel)
        if message is not None:
            random_id = random.randint(1, 2 ** 63 - 1)
            sent_message = await client(SendMessageRequest(peer=user, message=message, random_id=random_id))
            await client(UpdatePinnedMessageRequest(peer=user, id=sent_message.id))
        print(f"Message ID {message_id} forwarded to User ID {user_id}")
    except Exception as e:
        print(f"Error forwarding message to User ID {user_id}: {e}")


# تابع محاسبه احساسات
def calculate_finbert_sentiment(text):
    inputs = tokenizer_finbert(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model_finbert(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().numpy()[0]
    return {
        "neutral": float(probs[0]),
        "positive": float(probs[1]),
        "negative": float(probs[2])
    }


# اطلاعات API خود را اینجا وارد کنید
api_id = ''
api_hash = ''
phone = ''  # شماره تلفن ثبت‌شده در تلگرام

# اتصال به تلگرام
client = TelegramClient('session_name', api_id, api_hash)

# تنظیمات MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['telegram_data']
collection = db['messages']

# کانال‌ها و مقادیر مرتبط
channel_mapping = {'IranintlTV': 0, 'Saberin_ir': 1, 'Tasnimnews': 2, 'akharinkhabar': 3, 'akhbarefori': 4,
                   'bbcpersian': 5, 'farsna': 6, 'irZagrosNews': 7, 'khabarfarda_ir': 8, 'tweet_Khabari': 9}

# اتصال به تلگرام
client = TelegramClient('session_name', api_id, api_hash)


async def fetch_channel_messages():
    await client.start()
    print("Connected to Telegram!")
    for channel_username, channel_id in channel_mapping.items():
        try:
            channel = await client.get_entity(channel_username)
            messages = await client(GetHistoryRequest(
                peer=channel,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=100,  # تعداد پیام‌های قابل دریافت
                max_id=0,
                min_id=0,
                hash=0
            ))

            for message in messages.messages:
                try:
                    if message.message:  # فقط پیام‌های متنی
                        message_text = clean_text(message.message)
                        message_date = message.date

                        # بررسی عدم ذخیره پیام تکراری
                        if collection.count_documents({'Message': message_text, 'channel': channel_username}) == 0:
                            # ترجمه پیام
                            translated_message = translate_to_english(message_text, 0, 1)

                            # محاسبه احساسات
                            sentiment = calculate_finbert_sentiment(translated_message)

                            # ذخیره در MongoDB
                            document = {
                                "Message": message_text,
                                "translated_message": translated_message,
                                "neutral": sentiment['neutral'],
                                "positive": sentiment['positive'],
                                "negative": sentiment['negative'],
                                "date": message_date,
                                "channel": channel_username
                            }

                            if sentiment['positive'] > 0.1 or sentiment['negative'] > 0.1:
                                if sentiment['positive'] > 0.8 or sentiment['negative'] > 0.8:
                                    alert_message = f"📢 پیام مهم از {channel_username}:\n\n" \
                                                    f"{message_text}\n\n" \
                                                    f"🟢 مثبت: {sentiment['positive']:.2f}\n" \
                                                    f"🔴 منفی: {sentiment['negative']:.2f}\n" \
                                                    f"⚪ خنثی: {sentiment['neutral']:.2f}"
                                else:
                                    alert_message = None
                                await forward_message_to_user(
                                    user_id=number,  # جایگزین با آیدی یا نام کاربری مقصد
                                    message_id=message.id,  # شناسه پیام
                                    from_channel=channel,  # کانال مبدا
                                    message=alert_message
                                )

                            collection.insert_one(document)
                            print(f"Saved message from {channel_username}: {message_text[:50]}...")
                except:
                    continue
        except Exception as e:
            print(f"Error fetching messages from {channel_username}: {e}")


# اجرای برنامه هر 10 دقیقه
async def run_periodically():
    while True:
        await fetch_channel_messages()
        print("Waiting for 10 minutes...")
        time.sleep(600)


with client:
    client.loop.run_until_complete(run_periodically())
