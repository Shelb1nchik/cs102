import os

from bayes import NaiveBayesClassifier
from bottle import redirect, request, route, run, template
from db import News, session
from scraputils import get_news

current_dir = os.path.dirname(os.path.abspath(__file__))


@route("/news")
def news_list():
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    return template(os.path.join(current_dir, "news_template.tpl"), rows=rows)


@route("/add_label/")
def add_label():
    label = request.query.label
    news_id = request.query.id
    s = session()
    news = s.query(News).filter(News.id == news_id).first()
    if news:
        news.label = label
        s.commit()
    redirect("/news")


@route("/update")
def update_news():
    news_list = get_news("https://news.ycombinator.com/newest", n_pages=1)
    s = session()
    db_news = set([(news.title, news.author) for news in s.query(News).all()])
    for news in news_list:
        if (news["title"], news["author"]) not in db_news:
            n = News(
                title=news["title"],
                author=news["author"],
                url=news["url"],
                comments=news["comments"],
                points=news["points"],
            )
            s.add(n)
    s.commit()
    redirect("/news")


@route("/classify")
def classify_news():
    with session() as s:
        model = NaiveBayesClassifier()
        labeled_news = s.query(News).filter(News.label != None).all()
        X_train = [news.title for news in labeled_news]
        Y_train = [news.label for news in labeled_news]
        model.fit(X_train, Y_train)

        unlabeled_news = s.query(News).filter(News.label == None).all()
        for news in unlabeled_news:
            label = model.predict([news.title])[0]
            news.label = label
            s.add(news)
            s.commit()


@route("/recommendations")
def recommendations():
    good = []
    maybe = []
    never = []
    with session() as s:
        model = NaiveBayesClassifier()
        labeled_news = s.query(News).filter(News.label != None).all()
        X_train = [news.title for news in labeled_news]
        Y_train = [news.label for news in labeled_news]
        model.fit(X_train, Y_train)

        unlabeled_news = s.query(News).filter(News.label == None).all()
        for news in unlabeled_news:
            label = model.predict([news.title])[0]
            news.label = label
            if label == "good":
                good.append(news)
            elif label == "maybe":
                maybe.append(news)
            elif label == "never":
                never.append(news)
            s.add(news)
            s.commit()
        classified_news = (
            s.query(News).filter(News.label == "good").all()
            + s.query(News).filter(News.label == "maybe").all()
            + s.query(News).filter(News.label == "never").all()
        )
    return template("news_recommendations", rows=classified_news)


if __name__ == "__main__":
    run(host="localhost", port=7070)
