import requests  # type: ignore
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker

from db import News, engine

Session = sessionmaker(bind=engine)
session = Session()


def extract_news(parser):
    """Extract news from a given web page"""
    news_list = []

    data = parser.find_all("tr", class_="athing")
    for i in data:
        nazv = i.find("span", class_="titleline")
        link = nazv.a.get("href") if nazv.a else None
        title = nazv.a.text

        infa = i.find_next_sibling("tr")
        points_tag = infa.find("span", class_="score")
        points = int(points_tag.text.strip().split()[0]) if points_tag else 0
        author_tag = infa.find("a", class_="hnuser")
        author = author_tag.text if author_tag else "unknown author"
        comments_tag = infa.find("a", string=lambda s: "comments" in s.lower())
        comments = int(comments_tag.text.strip().split()[0]) if comments_tag else 0

        news_list.append(
            {
                "author": author,
                "comments": comments,
                "points": points,
                "title": title,
                "url": link,
            }
        )

    return news_list


def extract_next_page(parser):
    """Extract next page URL"""
    more_link = parser.find("a", class_="morelink")
    return more_link.get("href")


def get_news(url, n_pages=1):
    """Collect news from a given web page"""
    news = []
    while n_pages:
        print("Collecting data from page: {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = extract_news(soup)
        next_page = extract_next_page(soup)
        url = "https://news.ycombinator.com/" + next_page
        news.extend(news_list)
        n_pages -= 1
    return news


def save_news_to_db(n_pages=1):
    """Collect and save news to the database"""
    news_list = get_news("https://news.ycombinator.com/newest", n_pages=n_pages)
    for news in news_list:
        n = News(
            title=news["title"],
            author=news["author"],
            url=news["url"],
            comments=news["comments"],
            points=news["points"],
        )
        session.add(n)
    session.commit()


if __name__ == "__main__":
    save_news_to_db(n_pages=8)
