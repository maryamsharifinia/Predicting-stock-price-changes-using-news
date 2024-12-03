import dill
from pymongo import MongoClient
from deep_translator import GoogleTranslator
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

# تنظیمات اتصال به پایگاه داده
client = MongoClient('mongodb://localhost:27017/')
db = client['telegram_data']

# مدل FinBERT برای تحلیل احساسات

# چون من مدام نیاز به دیباگ و تست داشتم دانلود مدام باید انجام میشد بنابر این من مدل ها رو با dill ذخیره و استفاده کردم ولی برای جرا شما باید از کد زیر استفاده کنید
# finbert_model = "yiyanghkust/finbert-tone"
# tokenizer_finbert = AutoTokenizer.from_pretrained(finbert_model)
# model_finbert = AutoModelForSequenceClassification.from_pretrained(finbert_model)
# def calculate_finbert_sentiment(text):
#     inputs = tokenizer_finbert(text, return_tensors="pt", truncation=True, padding=True)
#     outputs = model_finbert(**inputs)
#     probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
#     sentiment_score = probs.detach().numpy()[0]
#     return sentiment_score


with open(r"C:\Users\mobin.DESKTOP-KS1RI2E\Downloads\functions.dill", 'rb') as file:
    loaded_function_dict = dill.load(file)

calculate_finbert_sentiment = loaded_function_dict.get('calculate_finbert_sentiment')
finbert_model = loaded_function_dict.get("finbert_model")
tokenizer_finbert = loaded_function_dict.get("tokenizer_finbert")
model_finbert = loaded_function_dict.get("model_finbert")

def translate_to_english(text, index, total):
    try:
        from deep_translator import GoogleTranslator
        translation = GoogleTranslator(source='fa', target='en').translate(text)
        print(f"Translating {index + 1}/{total}...")
        return translation
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


def calculate_finbert_sentiment(text):
    inputs = tokenizer_finbert(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model_finbert(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().numpy()[0]
    return {
        "neutral": float(probs[0]),
        "positive": float(probs[1]),
        "negative": float(probs[2])
    }


collections = db.list_collection_names()

for collection_name in collections:
    print(f"Processing collection: {collection_name}")
    collection = db[collection_name]

    documents = list(collection.find())
    total_docs = len(documents)

    for index, doc in enumerate(documents):
        message = doc.get('Message', '')
        if not message:
            continue


        translated_message = translate_to_english(message, index, total_docs)


        sentiment_scores = calculate_finbert_sentiment(translated_message)


        collection.update_one(
            {'_id': doc['_id']},
            {
                '$set': {
                    'translated_message': translated_message,
                    'sentiment': sentiment_scores
                }
            }
        )
        print(f"Updated document {index + 1}/{total_docs} in collection {collection_name}")

print("Processing complete!")
