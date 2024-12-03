# README for GitHub Repository: *Iranian Stock Market Fluctuations Analysis*

## 📊 **Iranian Stock Market Fluctuations: From Social News to Forecasting Models**

This repository contains the code and methodology used in the research paper titled *"Iranian Stock Market Fluctuations: From Social News to Forecasting Models."* The project explores the impact of news sentiment and market data on stock price fluctuations in the Tehran Stock Exchange.

---

### 📖 **Overview**

This research investigates the relationship between social news and stock market dynamics, focusing on sentiment analysis and technical data to predict stock price movements. The analysis combines:

1. **News Sentiment**: Extracted from prominent Persian Telegram news channels, translated to English, and analyzed using FinBERT.
2. **Market Data**: Price adjustments, trading volume, and index changes sourced from TSETMC.
3. **Machine Learning Models**: Implemented to classify price changes and predict future trends.

---

### 🚀 **Key Features**

- **Sentiment Analysis**: Translate Persian news into English and analyze sentiments (positive, negative, neutral) using FinBERT.
- **Market Modeling**: Combine sentiment scores with financial indicators (e.g., trading volume, index changes) for robust prediction.
- **Classification Models**: Predict stock price movement categories:
  - Significant Increase
  - Slight Increase
  - No Change
  - Slight Decrease
  - Significant Decrease
- **Telegram Bot Integration**: Real-time interaction for investors to assess the impact of news on specific stocks.

---

### 📈 **Results and Performance**

#### Evaluation Metrics
- **News-only Analysis**: ~38% accuracy across models.
- **Market Data-only Analysis**: ~44% accuracy with added financial parameters.
- **Combined Analysis**: ~62% accuracy (Gradient Boosting performs best).

#### Key Findings
- Sentiment analysis alone has limited predictive power.
- Combining sentiment with market data significantly improves model accuracy.
- Gradient Boosting and MLPClassifier provide the best results for price prediction.

---

### 📬 **Usage**

#### Predict Stock Movement
1. you can run  `9-read_new_telegram_data.py` `10-collect_live_market_data.py` for collecting live data and the models with live data:

2. run `11-telegram_bot.py` for use models whitch is crated and use it to test.

---

### 🛠 **Future Improvements**

- Train a dedicated Persian sentiment model to reduce translation errors.
- Incorporate additional financial indicators for better accuracy.
- Enhance the Telegram bot with personalized portfolio features.

---

### 🙌 **Contributors**

- **Maryam Sharifina** (mrymsharifinia@gmail.com)  
- **Farzaneh Ghayour Baghbani** (ghayour@iust.ac.ir)
