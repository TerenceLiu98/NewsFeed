from flask import Flask, render_template, request
from news.news import *

app = Flask(__name__)


def GetArticles(date:str=None):
    newssource = NewsSource(date=date)
    articles = newssource.Articles()
    return articles


def GetEvents(date: str = None):
    newssource = NewsSource(date=date, event=True)
    events_down, events_up = newssource.Events()
    return events_down, events_up


@app.route("/article")
def articles():
    date = request.args.get('date')
    if date != None:
        articles = GetArticles(date=date)
    else:
        articles = GetArticles()

    title = articles.article_info.apply(pd.Series)["title"]
    articles_list = []
    for i in range(0, len(articles)):
        articles_list.append({
            "title": list(title)[i],
            "country": list(articles.country_info)[i],
            "summary": list(articles.summary)[i],
            "source": list(articles.source)[i],
            "url": list(articles.url)[i],
        })

    return render_template("articles.html", date=date, articles=articles_list)


@app.route("/event")
def events():
    date = request.args.get('date')
    if date != None:
        events_down, events_up = GetEvents(date=date)
    else:
        events_down, events_up = GetEvents()
    events_up.sort_values("GoldsteinScale", ascending=False)
    articles_list_down = []
    for i in range(0, len(events_down)):
        articles_list_down.append({
            "title":
            list(events_down.title)[i],
            "summary":
            list(events_down.summary)[i],
            "url":
            list(events_down.SOURCEURL)[i],
            "AvgTone":
            round(list(events_down.AvgTone)[i], 3),
            "Goldstein":
            list(events_down.GoldsteinScale)[i],
            "NumArticles":
            list(events_down.NumArticles)[i],
        })

    articles_list_up = []
    for i in range(0, len(events_down)):
        articles_list_up.append({
            "title": list(events_up.title)[i],
            "summary": list(events_up.summary)[i],
            "url": list(events_up.SOURCEURL)[i],
            "AvgTone": round(list(events_up.AvgTone)[i], 3),
            "Goldstein": list(events_up.GoldsteinScale)[i],
            "NumArticles": list(events_up.NumArticles)[i],
        })

    return render_template("events.html",
                           date=date,
                           events_down=articles_list_down,
                           events_up=articles_list_up)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

