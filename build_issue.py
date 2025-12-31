import feedparser
import json
import random
import datetime
import requests
from bs4 import BeautifulSoup

# --- YOUR SOURCE LIST ---
SOURCES = {
    "cover_story": "https://taylorlorenz.substack.com/feed",
    "secondary_features": [
        "https://mtdeco.substack.com/feed",
        "https://1234kyle5678.substack.com/feed",
        "https://embedded.substack.com/feed",
        "https://zine.kleinkleinklein.com/feed",
        "https://newsletter.danhon.com/rss",
        "https://afterschool.substack.com/feed",
        "https://louderback.com/blog/feed",
        "https://coolshinyculture.substack.com/feed",
        "https://melzog.substack.com/feed",
        "https://www.readtpa.com/feed",
        "https://www.phonetime.news/rss",
        "https://www.hardresetmedia.com/rss"
    ],
    "daily_briefing": [
        "https://www.wired.com/feed/rss",
        "http://www.theverge.com/rss/index.xml",
        "https://feeds.kottke.org/main"
    ],
    "art_feeds": [
        "https://openrss.org/bsky.app/profile/ranaroth.bsky.social",
        "https://openrss.org/bsky.app/profile/scifiart.bsky.social",
        "https://mastodon.world/@librarianRA.rss",
        "https://openrss.org/bsky.app/profile/thatsgoodweb.bsky.social",
        "https://obsoletesony.com/feed",
        "https://openrss.org/bsky.app/profile/tommysiegel.bsky.social",
        "https://openrss.org/bsky.app/profile/ellisjrosen.bsky.social",
        "https://mastodon.world/@exocomics.rss",
        "https://mastodon.social/@warandpeas.rss"
    ]
}

# --- HELPER FUNCTIONS ---

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove "Subscribe" buttons or tracking pixels often found in footers
    for div in soup.find_all('div', class_='subscription-widget'):
        div.decompose()
    
    for img in soup.find_all('img'):
        img['style'] = ''
        img['class'] = 'article-image'
        if img.get('src') and img['src'].startswith('/'):
            img['src'] = "https:" + img['src']
            
    return str(soup)

def get_image(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    if 'content' in entry:
        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
        img = soup.find('img')
        if img: return img['src']
    return "https://placehold.co/800x600/111/333?text=No+Image"

def fetch_longest_item(url):
    """
    Scans the first 3 entries of a feed. 
    Returns the one with the longest text content (avoiding paywall teasers).
    """
    try:
        d = feedparser.parse(url)
        if not d.entries: return None
        
        candidates = []
        
        # Look at the top 3 posts (Updated from 5)
        for entry in d.entries[:3]:
            # Determine content (some use 'content', some 'summary')
            raw_body = ""
            if 'content' in entry:
                raw_body = entry.content[0].value
            elif 'summary' in entry:
                raw_body = entry.summary
            
            # Score it by length
            score = len(raw_body)
            candidates.append((score, entry, raw_body))
        
        # Sort by length (descending) -> Get the longest one
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if not candidates: return None
        
        # The winner is the longest article
        best_entry = candidates[0][1]
        best_body = candidates[0][2]
        
        return {
            "source": d.feed.title if 'title' in d.feed else "Source",
            "title": best_entry.title,
            "author": best_entry.author if 'author' in best_entry else "Unknown",
            "bodyText": clean_html(best_body),
            "image": get_image(best_entry)
        }
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

# --- BUILDER ---

if __name__ == "__main__":
    print("🗞️  Starting the Presses (Smart Mode)...")
    issue = {
        "meta": {
            "issueNo": f"Vol. {datetime.date.today().year}.{datetime.date.today().isocalendar()[1]}",
            "date": datetime.date.today().strftime("%A, %B %d"),
            "location": "West Hollywood"
        },
        "coverStory": {},
        "secondaryFeatures": [],
        "dailyBriefing": [],
        "artInterstitials": []
    }

    # 1. Cover Story
    print(f"Fetching Deepest Story from User Mag...")
    issue["coverStory"] = fetch_longest_item(SOURCES["cover_story"])

    # 2. Features (Pick 5)
    print(f"Selecting 5 Deep Reads from features list...")
    random.shuffle(SOURCES["secondary_features"])
    for url in SOURCES["secondary_features"][:5]:
        item = fetch_longest_item(url)
        if item: issue["secondaryFeatures"].append(item)

    # 3. Briefing
    print("Compiling Daily Briefing...")
    pool = []
    for url in SOURCES["daily_briefing"]:
        d = feedparser.parse(url)
        for entry in d.entries[:5]:
            pool.append({"headline": entry.title, "source": d.feed.title, "link": entry.link})
    random.shuffle(pool)
    issue["dailyBriefing"] = pool[:10]

    # 4. Art
    print("Curating Art Gallery...")
    art_pool = []
    for url in SOURCES["art_feeds"]:
        d = feedparser.parse(url)
        # Be more aggressive finding images
        for entry in d.entries[:3]:
            img = get_image(entry)
            if "placehold" not in img: art_pool.append(img)
    random.shuffle(art_pool)
    issue["artInterstitials"] = art_pool[:5]

    # Save
    with open('weeklyIssue.json', 'w') as f:
        json.dump(issue, f, indent=2)

    print("\n✅ DONE! 'weeklyIssue.json' has been generated.")