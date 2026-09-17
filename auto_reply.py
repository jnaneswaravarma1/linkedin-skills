from google import genai
from dotenv import load_dotenv
import os
import requests
import time

# Load API keys
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
linkedin_id = os.getenv("LINKEDIN_PLATFORM_ID")
apify_token = os.getenv("APIFY_TOKEN")

# Setup Gemini
client = genai.Client(api_key=gemini_key)

def read_skill(skill_name):
    path = f"skills/{skill_name}/SKILL.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_published_posts():
    """Fetch published posts from Publora"""
    print("Fetching published posts from Publora...")
    url = "https://api.publora.com/api/v1/list-posts"
    headers = {
        "x-publora-key": publora_key,
        "Content-Type": "application/json"
    }
    params = {
        "platformId": linkedin_id
    }
    response = requests.get(url, headers=headers, params=params)
    print("Status:", response.status_code)
    if response.status_code == 200:
        return response.json()
    return {}

def get_comments_from_apify(post_urn):
    """Fetch comments from a LinkedIn post using Apify"""
    print(f"\nFetching comments for: {post_urn}")
    url = "https://api.apify.com/v2/acts/apimaestro~linkedin-post-comments-replies-engagements-scraper-no-cookies/run-sync-get-dataset-items"
    params = {"token": apify_token}
    payload = {
        "postIds": [post_urn],
        "maxComments": 10
    }
    response = requests.post(url, params=params, json=payload, timeout=120)
    print("Apify status:", response.status_code)
    if response.status_code == 200:
        return response.json()
    print("Apify error:", response.text[:300])
    return []

def draft_reply(comment_text):
    """Draft a reply using Gemini"""
    skill_instructions = read_skill("linkedin-comment-drafter")
    prompt = f"""
You are a LinkedIn engagement expert.
Follow these skill instructions:
{skill_instructions}

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
    """Post a comment to LinkedIn via Publora"""
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

# Step 1 — Get published posts from Publora
posts_data = get_published_posts()

# Step 2 — Use known post URN directly
print("\n" + "=" * 50)
print("FETCHING COMMENTS FROM LINKEDIN...")
print("=" * 50)

post_urn = "urn:li:share:7505589561696178176"

comments = get_comments_from_apify(post_urn)
print(f"\nComments found: {len(comments)}")

if not comments:
    print("\nNo comments found.")
    print("Possible reasons:")
    print("1. Post has no comments yet")
    print("2. Apify needs more time to scrape")
    print("3. Post URN format issue")
else:
    for i, comment in enumerate(comments[:5]):
        print(f"\n--- Comment {i+1} ---")
        comment_text = (
            comment.get("text") or
            comment.get("commentText") or
            comment.get("content") or
            ""
        )
        print(f"Comment: {comment_text}")
        print(f"Full comment data keys: {list(comment.keys())}")

        if comment_text:
            print("\nDrafting reply...")
            reply = draft_reply(comment_text)
            print(f"Reply: {reply}")

            approve = input(f"\nPost this reply to LinkedIn? (yes/no): ")
            if approve.lower() == "yes":
                result = post_comment_to_linkedin(post_urn, reply)
                print("Result:", result)
            else:
                print("Skipped.")

        time.sleep(2)

print("\n✅ Pipeline complete!")