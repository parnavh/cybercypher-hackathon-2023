import streamlit as st
from pandas_datareader import data as pdr
import yfinance as yf
import plotly.figure_factory as ff
import plotly.graph_objects as go
from utils import get_start_date, get_effect_on_trend, get_search_term, sanitize_text, colorize
from scrape import main as scraper

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

yf.pdr_override()

st.title("Stock Sentiment Analysis")
st.text(
    "Predicting stock trend based on recent news and social media posts")

col1, col2 = st.columns(2)

def on_change():
    st.session_state.stock = st.session_state.stock.upper()

with col1:
    st.text_input(label="Enter Stock Ticker", key="stock", value="AMZN", on_change=on_change)

with col2:
    option = st.selectbox('Choose Chart Type',
                          ('Candlestick chart', 'Line chart'))

df = pdr.get_data_yahoo(st.session_state.stock, start=get_start_date())

if option == "Candlestick chart":
    fig = ff.create_candlestick(
        dates=df.index, open=df['Open'], close=df['Close'], high=df['High'], low=df['Low'])
else:
    fig = go.Figure([go.Line(y=df['High'], x=df.index)])

fig.update_layout(title="Interactive Chart", xaxis_title="Time", yaxis_title="Share Price",
                  xaxis_rangeslider_visible=True)

st.plotly_chart(fig, use_container_width=True, theme="streamlit")

st.subheader("News Sentiment Analysis")

news_sentiment = """
| News Article | Publisher | Publish Time | Sentiment | Effect on Trend |
| ------------ | --------- | ------------ | --------- | --------------- |
"""

@st.cache(ttl=3600, show_spinner=False)
def get_news():
    return scraper(get_search_term(st.session_state.stock))

with st.spinner(text="Analyzing news articles..."):
    search_res = get_news()

stock_score = 0
neutral_count = 0

classifications = []

for x in search_res:
    res = classifier(f"{sanitize_text(x['title'])}. {sanitize_text(x['description'][:600])}")[0]
    classifications.append(res)

    if res['label'] == "negative":
        stock_score -= res['score']
    elif res['label'] == "positive":
        stock_score += res['score']
    else:
        neutral_count += 1

    news_sentiment += f'| [{sanitize_text(x["title"])}]({x["url"]}) | *{x["author"]}* | {x["time"]} | **{colorize(res["label"], res["score"])}** | {get_effect_on_trend(res["label"])} |\n'

if neutral_count/len(classifications) > 0.5:
    st.warning("Recent news articles indicate that the stock trend is likely to remain stable.")
else:
    if stock_score > 0.5:
        st.success("Recent news articles indicate that the stock is likely to go up.")
    elif stock_score < -0.5:
        st.error("Recent news articles indicate that the stock is likely to go down.")
    else:
        st.warning("Recent news articles indicate that the stock trend is likely to remain stable.")

st.markdown(news_sentiment)

