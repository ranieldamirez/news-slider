# fetch_headlines.py

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.parser import parse
import sqlite3

from app import create_app
from models import db, NewsSource, Headline

load_dotenv() # reads variable from .env
API_KEY = os.environ.get("NEWSAPI_KEY")

# bias values sorted from left to right
# (-10, -6) : Strongly Left
# (-5, -2) : Lean Left
# (-1, +1) : Centrist / Minimal partisan
# (+2, +5) : Lean Right
# (+6, +10) : Strongly Rights
bias_overrides = {
    "MSNBC": -7,
    "The Huffington Post": -6,
    "Al Jazeera English": -5,
    "Buzzfeed": -5,
    "Vice News": -5,
    "CNN": -4,
    "CNN Spanish": -4,
    "MTV News": -4,
    "New York Magazine": -4,
    "The Washington Post": -4,
    "CBS News": -3,
    "Mashable": -3,
    "NBC News": -3,
    "Axios": -2,
    "ABC News": -2,
    "Business Insider": -2,
    "Entertainment Weekly": -2,
    "Newsweek": -2,
    "Politico": -2,
    "TechCrunch": -2,
    "The Verge": -2,
    "Time": -2,
    "Wired": -2,
    "Associated Press": -1,
    "Engadget": -1,
    "Hacker News": -1,
    "IGN": -1,
    "Polygon": -1,
    "Recode": -1,
    "Reddit /r/all": -1,
    "Reuters": -1,
    "The Next Web": -1,
    "Ars Technica": 0,
    "Bleacher Report": 0,
    "Bloomberg": 0,
    "Crypto Coins News": 0,
    "ESPN": 0,
    "ESPN Cric Info": 0,
    "Fox Sports": 0,
    "Google News": 0,
    "Medical News Today": 0,
    "National Geographic": 0,
    "New Scientist": 0,
    "Next Big Future": 0,
    "NFL News": 0,
    "NHL News": 0,
    "TechRadar": 0,
    "The Hill": 0,
    "Fortune": 1,
    "USA Today": 1,
    "The Wall Street Journal": 2,
    "The American Conservative": 5,
    "The Washington Times": 5,
    "Fox News": 6,
    "National Review": 6,
    "Breitbart News": 8
}

def fetch_us_sources_and_store(default_bias=0):
    """
    1) Fetch the list of sources from NewsAPI.
    2) Store each source in our DB with 'default_bias' if it doesn't already exist.
    3) Return the list of source IDs.
    """
    app = create_app()
    with app.app_context():
        # Fetch the source list
        url = f"https://newsapi.org/v2/sources?country=us&apiKey={API_KEY}" # only grabbing US sources
        resp = requests.get(url)
        data = resp.json()

        if data.get("status") != "ok":
            print("Error fetching sources:", data)
            return []

        source_ids = []
        sources_data = data.get("sources", [])

        for item in sources_data:
            # item example: {"id": "cnn", "name": "CNN", ...}
            source_id = item["id"]       # e.g. "cnn"
            source_name = item["name"]   # e.g. "CNN"

            # Check if we already have this in our DB
            existing = NewsSource.query.filter_by(name=source_name).first()

            if not existing:
                # Create a new row for this source
                bias = bias_overrides.get(source_name, 0)
                new_source = NewsSource(name=source_name, bias_score=bias)
                db.session.add(new_source)
                db.session.commit()
                print(f"Added new source '{source_name}' with ID {new_source.id}")
            else:
                print(f"Source '{source_name}' already exists in DB.")
            
            # We'll keep track of the actual source_id (the one NewsAPI uses) so we can fetch headlines next
            source_ids.append((source_name, source_id))

        return source_ids

def fetch_headlines_for_source(source_name, source_api_id):
    """
    1) Fetch top headlines from a specific source (using source_api_id).
    2) Store them in the DB under 'source_name' row.
    """
    app = create_app()
    with app.app_context():
        # Find the DB row for this source
        db_source = NewsSource.query.filter_by(name=source_name).first()
        if not db_source:
            print(f"Error: Source '{source_name}' not found in DB.")
            return

        # Fetch headlines from NewsAPI
        url = f"https://newsapi.org/v2/top-headlines?sources={source_api_id}&apiKey={API_KEY}"
        resp = requests.get(url)
        data = resp.json()

        if data.get("status") != "ok":
            print(f"Error fetching headlines for {source_name}:", data)
            return

        articles = data.get("articles", [])
        new_count = 0

        for article in articles:
            title = article.get("title")
            article_url = article.get("url")
            published_at_raw = article.get("publishedAt")  # e.g. from API, "2025-02-19T18:12:00Z"

            try:
                dt = parse(published_at_raw)  # Automatically handles extra fractional digits.
                published_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error parsing publishedAt for article '{title}': {e}")
                continue

            # Check for duplicates by title + url
            existing = Headline.query.filter_by(title=title, url=article_url).first()
            if existing:
                continue

            # Insert new Headline
            new_headline = Headline(
                source_id=db_source.id,
                title=title or "No Title",
                url=article_url or "No URL",
                published_at=published_at
            )
            db.session.add(new_headline)
            new_count += 1

        db.session.commit()
        print(f"Fetched and stored {new_count} new headlines from {source_name}.")

def cleanup_old_articles(db_path='./instance/news.db'):
    # If the articles are more than 2 days old, delete it from the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Calculatea threshold datetime (two days ago)
    threshold = datetime.now() - timedelta(days=2)
    threshold_str = threshold.strftime("%Y-%m-%d %H:%M:%S")
    # Delete old articles
    cursor.execute("DELETE FROM headlines WHERE published_at < ?", (threshold_str,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Step 1: Fetch the list of all NewsAPI sources and store them in DB
    #         with a default bias score of 0.  (You could also do custom logic 
    #         if you know certain sources are more liberal/conservative.)
    all_sources = fetch_us_sources_and_store(default_bias=0)

    # Delete old headlines (2 days old)
    cleanup_old_articles()

    # Step 2: For each source, fetch the top headlines
    # WARNING: This could be 70+ requests. Might exceed free-tier NewsAPI limit.
    for (source_name, source_api_id) in all_sources:
        fetch_headlines_for_source(source_name, source_api_id)
