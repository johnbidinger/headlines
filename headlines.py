from pathlib import Path
import sys
import os
import datetime

from dotenv import load_dotenv
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

import feedparser
from flask import Flask, render_template, request, make_response

import json
import urllib

app = Flask(__name__)

RSS_FEEDS = {
    'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
    'cnn': 'http://rss.cnn.com/rss/edition.rss',
    'fox': 'http://feeds.foxnews.com/foxnews/latest',
    'iol': 'http://www.iol.co.za/cmlink/1.640'
}
DOTENV_WEATHER_APP_ID = os.environ.get('WEATHER_API_APP_ID')
DOTENV_CURRENCY_APP_ID = os.environ.get('CURRENCY_API_APP_ID')
COUNTRIES_AND_CODES_URL = os.environ.get('CURRENCY_API_COUNTRIES')

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=" #.format(os.environ.get('WEATHER_API_APP_ID')
WEATHER_URL += DOTENV_WEATHER_APP_ID

CURRENCY_URL = "https://openexchangerates.org/api/latest.json?app_id=" #.format(os.environ.get('CURRENCY_API_APP_ID'))
CURRENCY_URL += DOTENV_CURRENCY_APP_ID

# FOX_FEED = "http://feeds.foxnews.com/foxnews/latest"
DEFAULTS = {
    'publication': 'bbc',
    'city' : 'Baltimore',
    'currency_from' : 'GBP',
    'currency_to' : 'USD'
}

def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]

@app.route("/")
# @app.route("/<publication>")
def home():
    # get custom headlines
    publication = get_value_with_fallback('publication')
    articles = get_news(publication)

    #get custom weather based on user input or default
    city = get_value_with_fallback('city')
    weather = get_weather(city)

    # get custom currency based on user input or default
    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies, countries = get_rate(currency_from, currency_to)

    response = make_response(render_template("home.html", 
        articles=articles,
        weather=weather,
        currency_from=currency_from,
        currency_to=currency_to,
        rate=rate,
        currencies=sorted(currencies),
        countries_and_codes=countries))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    
    response.set_cookie("publication", publication, expires=expires)

    response.set_cookie("city", city, expires=expires)
    response.set_cookie("currency_from", currency_from, expires=expires)
    response.set_cookie("currency_to", currency_to, expires=expires)

    return response
    # render_template("home.html", articles=articles, weather=weather,
                            # currency_from=currency_from, currency_to=currency_to, rate=rate, currencies=sorted(currencies), countries_and_codes=countries)



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
    countries_and_codes = urllib.request.urlopen(COUNTRIES_AND_CODES_URL).read()
    countries_and_codes = json.loads(countries_and_codes)
    all_currency = urllib.request.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate / frm_rate, parsed.keys(), countries_and_codes)

if __name__ == "__main__":
    # if sys.platform == 'darwin':

    app.run(host='0.0.0.0')
