import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from confluent_kafka import Producer
import spacy
from geopy.geocoders import Nominatim
from atproto import Client  # Bluesky / AT Protocol SDK

# ------------ Config ------------
KAFKA_BOOTSTRAP = "localhost:9092"
ENRICHED_TOPIC = "enriched_events"
POLL_INTERVAL_MINUTES = 5

BLUESKY_HANDLE = "your-handle.bsky.social"
BLUESKY_APP_PASSWORD = "your-app-password"
TARGET_ACTORS = [
    "target1.bsky.social",
    "target2.bsky.social",
]  # actors whose feeds you want to monitor

# ------------ Globals ------------
nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="danger-map-pipeline")
danger_keywords = [
    "explosion", "bomb", "shooting", "gunfire",
    "earthquake", "flood", "landslide", "collapse",
    "fire", "wildfire", "terrorist", "attack",
    "chemical", "toxic", "radiation",
]

producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})
last_fetch_time = datetime.now(timezone.utc)

bsky_client = Client()
bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
# Client manages the session (access/refresh tokens) automatically. [file:1]


# ------------ Utilities ------------
def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# ------------ Step 1: fetch from Bluesky ------------
def fetch_bluesky_posts_since(
    actor: str, since: datetime, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Use atproto.Client to fetch an author's feed and filter by time.
    """
    feed = bsky_client.app.bsky.feed.get_author_feed(
        {"actor": actor, "limit": limit}
    )
    posts = []
    for item in feed.feed:
        record = item.post.record
        # app.bsky.feed.post has createdAt field
        created_at = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
        if created_at <= since:
            continue
        posts.append(
            {
                "id": item.post.uri,
                "source": "bluesky",
                "text": record.text,
                "created_at": created_at,
            }
        )
    return posts


def fetch_social_posts(since: datetime) -> List[Dict[str, Any]]:
    all_posts: List[Dict[str, Any]] = []
    for actor in TARGET_ACTORS:
        all_posts.extend(fetch_bluesky_posts_since(actor, since))
    # sort by created_at just to be deterministic
    all_posts.sort(key=lambda p: p["created_at"])
    return all_posts


# ------------ Step 2: NLP ------------
def extract_locations(text: str) -> List[Dict[str, Any]]:
    doc = nlp(text)
    locs = []
    for ent in doc.ents:
        if ent.label_ in {"GPE", "LOC", "FAC"}:
            locs.append({"name": ent.text})
    # dedupe by name
    names = {}
    for loc in locs:
        if loc["name"]:
            names[loc["name"]] = loc
    results = []
    for loc in names.values():
        try:
            geo = geolocator.geocode(loc["name"], timeout=5)
            if geo:
                results.append(
                    {
                        "name": loc["name"],
                        "lat": geo.latitude,
                        "lon": geo.longitude,
                    }
                )
        except Exception:
            continue
    return results


def compute_danger_score(text: str) -> float:
    lowered = text.lower()
    hits = sum(1 for kw in danger_keywords if kw in lowered)
    return min(hits / 3.0, 1.0)


def derive_event_id(text: str, locations: List[Dict[str, Any]], created_at: datetime) -> str:
    loc_name = locations[0]["name"].lower().replace(" ", "_") if locations else "unknown"
    date_str = created_at.date().isoformat()
    return f"{loc_name}_{date_str}"


def enrich_post(post: Dict[str, Any]) -> Dict[str, Any]:
    created_at = post["created_at"]
    text = post["text"]

    locations = extract_locations(text)
    danger_score = compute_danger_score(text)
    event_id = derive_event_id(text, locations, created_at)

    # treat first observation as start date for now
    event_start_date = created_at

    return {
        "event_id": event_id,
        "post_id": post["id"],
        "source": post["source"],
        "text": text,
        "created_at": to_iso(created_at),
        "event_start_date": to_iso(event_start_date),
        "danger_score": danger_score,
        "locations": locations,
    }


# ------------ Step 3: Kafka write ------------
def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(
            f"Produced {msg.key()} to {msg.topic()} "
            f"[{msg.partition()}] offset {msg.offset()}"
        )


def write_to_kafka(event: Dict[str, Any]):
    key = event["event_id"].encode("utf-8")
    value = json.dumps(event).encode("utf-8")
    producer.produce(
        ENRICHED_TOPIC,
        key=key,
        value=value,
        callback=delivery_report,
    )
    producer.poll(0)


# ------------ Scheduled job ------------
def job():
    global last_fetch_time
    now = datetime.now(timezone.utc)
    print(f"[{to_iso(now)}] Polling Bluesky since {to_iso(last_fetch_time)}")

    posts = fetch_social_posts(last_fetch_time)
    print(f"Fetched {len(posts)} new Bluesky posts")

    for post in posts:
        enriched = enrich_post(post)
        # optional filter
        if enriched["danger_score"] < 0.3:
            continue
        write_to_kafka(enriched)

    producer.flush()
    last_fetch_time = now
    print(f"[{to_iso(now)}] Job finished, updated last_fetch_time")


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", minutes=POLL_INTERVAL_MINUTES)
    scheduler.start()

    print(f"Scheduler started, running every {POLL_INTERVAL_MINUTES} minutes. Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        producer.flush()


if __name__ == "__main__":
    main()
