import feedparser
from flask import Flask, render_template, request
import sys
import json
import urllib

app = Flask(__name__)

RSS_FEEDS = {
    'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
    'cnn': 'http://rss.cnn.com/rss/edition.rss',
    'fox': 'http://feeds.foxnews.com/foxnews/latest',
    'iol': 'http://www.iol.co.za/cmlink/1.640'
}
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=fea0835dbeecc42142934ae319c8ad61"
CURRENCY_URL = "https://openexchangerates.org/api/latest.json?app_id=8054ccbe02994e3c93c4c1ea6eb47bc8"
# FOX_FEED = "http://feeds.foxnews.com/foxnews/latest"
DEFAULTS = {
    'publication': 'bbc',
    'city' : 'Taneytown',
    'currency_from' : 'GBP',
    'currency_to' : 'USD'
}

@app.route("/")
# @app.route("/<publication>")
def home():
    publication = request.args.get('publication')
    if not publication:
        publication = DEFAULTS['publication']
    articles = get_news(publication)
    #get custom weather based on user input or default
    city = request.args.get('city')
    if not city:
        city = DEFAULTS['city']
    weather = get_weather(city)
    # get custom currency based on user input or default
    currency_from = request.args.get("currency_from")
    if not currency_from:
        currency_from = DEFAULTS['currency_from']
    currency_to = request.args.get("currency_to")
    if not currency_to:
        currency_to = DEFAULTS['currency_to']
    rate, currencies = get_rate(currency_from, currency_to)
    return render_template("home.html", articles=articles, weather=weather,
                            currency_from=currency_from, currency_to=currency_to, rate=rate, currencies=sorted(currencies))

def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS['publication']
    else:
        publication=query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    # first_article = feed['entries'][0]
    
    return feed['entries']
    
    # """<html>
    #     <body>
    #         <h1> Headlines </h1>
    #         <b>{0}</b> <br/>
    #         <i>{1}</i> <br/>
    #         <p>{2}</p> <br/>
    #     </body>
    # </html>
    # """.format(first_article.get("title"), first_article.get("published"), first_article.get("summary"))
def get_weather(query):
    api_url = WEATHER_URL
    query = urllib.parse.quote(query)
    url = api_url.format(query)
    data = urllib.request.urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get("weather"):
        weather = {"description":parsed["weather"][0]["description"], 
        "temperature":parsed["main"]["temp"], "city":parsed["name"],
        'country': parsed['sys']['country']}
    return weather

def get_rate(frm, to):
    all_currency = urllib.request.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate / frm_rate, parsed.keys())

if __name__ == "__main__":
    # if sys.platform == 'darwin':

    app.run(host='0.0.0.0')