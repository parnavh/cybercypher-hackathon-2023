from selenium.webdriver.common.by import By
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote

chrome_options = Options()
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.headless = True
chrome_options.add_argument("--disable-gpu")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

def main(query: str):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.google.com/search?q={quote(query)}+stocks&tbm=nws")

    content = driver.find_elements(
        By.XPATH, '//*[@id="search"]/div/div/div/div/div/div/div/a'
    )

    articles_data = []

    for x in content:
        article = Article(x.get_attribute("href"))
        try:
            article.download()
        except:
            try:
                article.download()
            except:
                continue

        article.parse()
        if not article.meta_description:
            continue
        articles_data.append({ "description": article.meta_description, "title": article.title, "url": article.url })

    return articles_data

if __name__ == "__main__":
    print(main("reliance"))
