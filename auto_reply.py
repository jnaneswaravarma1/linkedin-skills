from google import genai
from dotenv import load_dotenv
import os
import requests
import time
import json
from datetime import datetime

# Load API keys
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
linkedin_id = os.getenv("LINKEDIN_PLATFORM_ID")
apify_token = os.getenv("APIFY_TOKEN")

# Setup Gemini
client = genai.Client(api_key=gemini_key)

LOG_FILE = "logs.json"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return {"keys": {}, "runs": []}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def log_keys(logs):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keys_to_check = {
        "GEMINI_API_KEY": gemini_key,
        "PUBLORA_API_KEY": publora_key,
        "LINKEDIN_PLATFORM_ID": linkedin_id,
        "APIFY_TOKEN": apify_token
    }
    for key_name, key_value in keys_to_check.items():
        existing = logs["keys"].get(key_name, {})
        old_value = existing.get("value", "")
        connected = bool(key_value)
        note = ""
        if old_value and old_value != key_value:
            note = f"Updated at {now}"
        logs["keys"][key_name] = {
            "connected": connected,
            "value": key_value[:10] + "..." if key_value else "Not set",
            "last_updated": now,
            "note": note if note else existing.get("note", "")
        }
    return logs

def log_run(logs, post_urn, comments_found, replies_posted):
    now = datetime.now()
    run = {
        "type": "COMMENT REPLY",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "topic": post_urn,
        "post_urn": post_urn,
        "comments_found": comments_found,
        "replies_posted": replies_posted,
        "success": replies_posted > 0 or comments_found == 0,
        "published_at": now.strftime("%H:%M:%S")
    }
    logs["runs"].append(run)
    return logs

def read_skill(skill_name):
    path = f"skills/{skill_name}/SKILL.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_published_posts():
    print("Fetching published posts from Publora...")
    url = "https://api.publora.com/api/v1/list-posts"
    headers = {"x-publora-key": publora_key}
    params = {"platformId": linkedin_id}
    response = requests.get(url, headers=headers, params=params)
    print("Status:", response.status_code)
    if response.status_code == 200:
        return response.json()
    return {}

def get_comments_from_apify(post_urn):
    print(f"\nFetching comments for: {post_urn}")
    url = "https://api.apify.com/v2/acts/apimaestro~linkedin-post-comments-replies-engagements-scraper-no-cookies/run-sync-get-dataset-items"
    params = {"token": apify_token}
    payload = {"postIds": [post_urn], "maxComments": 10}
    response = requests.post(url, params=params, json=payload, timeout=120)
    print("Apify status:", response.status_code)
    if response.status_code in [200, 201]:
        data = response.json()
        if isinstance(data, list):
            # Filter out summary objects — keep only comment objects
            comments = [
                item for item in data
                if item.get("text") or item.get("commentText") or item.get("content")
            ]
            return comments
    print("Apify error:", response.text[:300])
    return []

def draft_reply(comment_text):
    skill_instructions = read_skill("linkedin-comment-drafter")
    prompt = f"""
You are a LinkedIn engagement expert.
Draft a short genuine reply to this comment.
Keep it under 200 characters.
Be conversational and add value.
No hashtags.

Comment: {comment_text}

Write only the reply text — nothing else.
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    return response.text.strip()

def post_comment_to_linkedin(posted_id, message):
    url = "https://api.publora.com/api/v1/linkedin-comments"
    headers = {
        "x-publora-key": publora_key,
        "Content-Type": "application/json"
    }
    payload = {
        "postedId": posted_id,
        "message": message,
        "platformId": linkedin_id
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Comment post status:", response.status_code)
    print("Comment post response:", response.text)
    if response.text:
        return response.json()
    return {}

# Main pipeline
print("=" * 50)
print("AUTO COMMENT REPLY PIPELINE")
print("=" * 50)

# Load and update logs
logs = load_logs()
logs = log_keys(logs)
save_logs(logs)

post_urn = "urn:li:share:7505906074131120128"
replies_posted = 0

get_published_posts()

print("\n" + "=" * 50)
print("FETCHING COMMENTS FROM LINKEDIN...")
print("=" * 50)

comments = get_comments_from_apify(post_urn)
print(f"\nComments found: {len(comments)}")

if not comments:
    print("\nNo comments found on this post yet.")
else:
    for i, comment in enumerate(comments[:5]):
        print(f"\n--- Comment {i+1} ---")
        comment_text = (
            comment.get("text") or
            comment.get("commentText") or
            comment.get("content") or ""
        )
        print(f"Comment: {comment_text}")

        if comment_text:
            print("Drafting reply...")
            reply = draft_reply(comment_text)
            print(f"Reply: {reply}")

            approve = input(f"\nPost this reply? (yes/no): ")
            if approve.lower() == "yes":
                result = post_comment_to_linkedin(post_urn, reply)
                if result.get("success"):
                    replies_posted += 1
                    print("✅ Reply posted!")
            else:
                print("Skipped.")
        time.sleep(2)

# Log this run
logs = load_logs()
logs = log_run(logs, post_urn, len(comments), replies_posted)
save_logs(logs)
print("\n📝 Run logged to dashboard.")
print("\n✅ Pipeline complete!")
print("\nRun 'python dashboard.py' to see the full dashboard.")