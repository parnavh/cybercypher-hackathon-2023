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
    articles_data = []

    for x in range(0, 2):
        driver.get(
            f"https://www.google.com/search?q={quote(query)}+stocks&tbm=nws&start={x*10}")

        content = driver.find_elements(
            By.XPATH, '//*[@id="search"]/div/div/div/div/div/div/div/a'
        )

        for x in content:
            author = x.find_element(By.XPATH, ".//descendant::span[1]")
            time = x.find_element(By.XPATH, ".//descendant::span[3]")
            article = Article(x.get_attribute("href"))
            try:
                article.download()
                article.parse()
            except:
                try:
                    article.download()
                    article.parse()
                except:
                    continue

            if not article.meta_description:
                continue
            articles_data.append({"author": author.text, "description": article.meta_description,
                                  "title": article.title, "url": article.url, "text": article.text, "time": time.text})

    return articles_data


if __name__ == "__main__":
    print(main("reliance"))
