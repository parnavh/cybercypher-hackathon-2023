import streamlit as st
from pandas_datareader import data as pdr
import yfinance as yf
import plotly.figure_factory as ff
import plotly.express as px
from utils import get_start_date, get_effect_on_trend, get_search_term, sanitize_text, colorize, is_available
from scrape import main as scraper

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

yf.pdr_override()

st.set_page_config(page_title="Team Deprecated | Stock Sentiment Analysis")

st.title("Stock Sentiment Analysis")
st.text(
    "Predicting stock trend based on recent news and social media posts")

st.text_input(label="Enter Stock Ticker", key="stock", value="AMZN")


df = pdr.get_data_yahoo(st.session_state.stock, start=get_start_date())
df["100 day rolling"] = df["High"].rolling(window=100).mean()
df["200 day rolling"] = df["High"].rolling(window=200).mean()

company_info = yf.Ticker(st.session_state.stock).info

tab1, tab2 = st.tabs(
    ['Company Details', 'News Analysis'])

with tab1:
    info_container = st.container()

    col1, col2, col3 = info_container.columns(3)

    with col1:
        st.metric(
            label=company_info["shortName"],
            value="%.2f" % company_info["currentPrice"],
            delta="%.2f" % (company_info["currentPrice"] -
                            company_info["previousClose"]),
        )
    with col2:
        st.metric(label="Today's High", value="%.2f" % company_info["dayHigh"] if (
            is_available(company_info, "dayHigh")) else "N/A")
    with col3:
        st.metric(label="Today's Low", value="%.2f" % company_info["dayLow"] if (
            is_available(company_info, "dayLow")) else "N/A")

    col4, col5, col6 = info_container.columns(3)

    with col4:
        st.metric(
            label="Revenue Growth (YoY)",
            value=("%.2f" % (company_info["revenueGrowth"]*100)+"%" if (
                is_available(company_info, "revenueGrowth")) else "N/A")
        )
    with col5:
        st.metric(label="PE Ratio", value="%.2f" % company_info["trailingPE"] if (
            is_available(company_info, "trailingPE")) else "N/A")
    with col6:
        st.metric(label="PB Ratio", value="%.2f" % company_info["priceToBook"] if (
            is_available(company_info, "priceToBook")) else "N/A")

    option = info_container.selectbox('Choose Chart Type',
                                      ('Candlestick chart', 'Line chart'))

    if option == "Candlestick chart":
        fig = ff.create_candlestick(
            dates=df.index, open=df['Open'], close=df['Close'], high=df['High'], low=df['Low'])
    else:
        fig = px.line(df, x=df.index, y=[
                      "High", "100 day rolling", "200 day rolling"])

    fig.update_layout(xaxis_title="Time", yaxis_title="Stock Value")

    info_container.plotly_chart(
        fig, use_container_width=True, theme="streamlit")

    info_container.markdown("### Company Info")
    info_container.write(company_info["longBusinessSummary"] if is_available(company_info, "longBusinessSummary") else "N/A")

with tab2:
    news_sentiment = """| News Article | Publisher | Publish Time | Sentiment | Effect on Trend |
| ------------ | --------- | ------------ | --------- | --------------- |
"""

    @st.cache(ttl=3600, show_spinner=False)
    def get_news():
        return scraper(get_search_term(st.session_state.stock.upper()))

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

