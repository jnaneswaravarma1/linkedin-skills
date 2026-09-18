from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import requests
import json

# Load API keys from .env
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
linkedin_id = os.getenv("LINKEDIN_PLATFORM_ID")
apify_token = os.getenv("APIFY_TOKEN")

# Setup Gemini
client = genai.Client(api_key=gemini_key)

LOG_FILE = "logs.json"

HASHTAGS = """
#SaiNithish #MG3Verse #TripuraAI #AI #GenerativeAI #AIAgents #AIAutomation #AIEngineering #BusinessAutomation #AIForBusiness #DigitalTransformation #FutureOfWork
"""

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

def log_run(logs, run_type, topic, success, published_at=None, post_id=None, verification=None):
    now = datetime.now()
    run = {
        "type": run_type,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "topic": topic,
        "success": success,
        "published_at": published_at or "-",
        "post_id": post_id or "-",
        "verification": verification or "-"
    }
    logs["runs"].append(run)
    return logs

def read_skill(skill_name):
    path = f"skills/{skill_name}/SKILL.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def clean_post(text):
    """Remove unnecessary gaps but keep emojis"""
    lines = text.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        stripped = line.strip()
        if stripped == '':
            if not prev_empty:
                cleaned.append('')
            prev_empty = True
        else:
            cleaned.append(stripped)
            prev_empty = False
    return '\n'.join(cleaned).strip()

def generate_post(topic):
    skill_instructions = read_skill("linkedin-post-writer")
    full_prompt = f"""
You are a LinkedIn content expert.
Follow these skill instructions exactly:
{skill_instructions}

Write only the post text — no strategy breakdown, no audit card, no metadata.
Just the raw post ready to publish.

FORMATTING RULES — follow strictly:
- Single line break between paragraphs only — no double spacing
- Use emojis only where they are relevant and add meaning
- Do not force emojis on every line
- Good emoji placements: key insights, stats, calls to action
- Bad emoji placements: random, decorative, forced
- Use 3 to 5 emojis maximum per post
- Keep the post clean and tight
- No extra blank lines anywhere
- No markdown formatting like ** or ##
- Do NOT add hashtags — they will be added automatically

User request: Write a viral LinkedIn post about: {topic}
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=full_prompt
    )
    post = clean_post(response.text)
    return post + "\n\n" + HASHTAGS.strip()

def verify_post(topic, post_content):
    """Gemini automatically verifies the post for relevance, facts, and quality"""
    print("\n" + "=" * 50)
    print("🔍 AUTO-VERIFYING POST...")
    print("=" * 50)

    verify_prompt = f"""
You are a LinkedIn content quality checker.

Topic requested: {topic}

Post content:
{post_content}

Verify the following and give a verdict:
1. Is the post relevant to the topic? (yes/no)
2. Are the facts and numbers realistic and credible? (yes/no)
3. Is the tone professional and engaging? (yes/no)
4. Is the formatting clean — no double spacing, no markdown? (yes/no)
5. Does it have a clear call to action? (yes/no)

Then give:
- VERDICT: PASS or FAIL
- REASON: one line explaining why
- SUGGESTION: one line on what to improve if FAIL

Be strict. If any fact seems made up or the post is off-topic — FAIL it.
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=verify_prompt
    )
    return response.text.strip()

def post_to_linkedin(content):
    url = "https://api.publora.com/api/v1/create-post"
    headers = {
        "x-publora-key": publora_key,
        "Content-Type": "application/json"
    }
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    payload = {
        "platforms": [linkedin_id],
        "content": content,
        "scheduledTime": now
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Status code:", response.status_code)
    if response.text:
        return response.json()
    return {}

# Main flow
print("=" * 50)
print("LINKEDIN AUTO-POSTER — POWERED BY GEMINI")
print("=" * 50)

# Load and update logs
logs = load_logs()
logs = log_keys(logs)
save_logs(logs)

topic = input("\nWhat topic do you want to post about? : ")

print("\nGenerating post...")
post_content = generate_post(topic)

print("\n" + "=" * 50)
print("GENERATED POST:")
print("=" * 50)
print(post_content)

# Auto verification by Gemini
verification_result = verify_post(topic, post_content)
print("\n" + verification_result)

# Check if post passed verification
if "FAIL" in verification_result.upper():
    print("\n❌ Post failed verification. Not publishing.")
    print("Fix the issue and run again.")
    logs = load_logs()
    logs = log_run(logs, "POST", topic, False, "-", "-", "FAILED VERIFICATION")
    save_logs(logs)
    exit()

print("\n✅ Post passed verification.")

# Ask user to post
approve = input("\nPost this to LinkedIn now? (yes/no): ")

if approve.lower() == "yes":
    print("\nPosting to LinkedIn...")
    result = post_to_linkedin(post_content)
    success = result.get("success", False)
    published_at = result.get("scheduledTime", "-")
    post_id = result.get("postGroupId", "-")

    if success:
        print("\n✅ Posted successfully to LinkedIn!")
    else:
        print("\n❌ Something went wrong.")

    logs = load_logs()
    logs = log_run(logs, "POST", topic, success, published_at, post_id, "PASSED VERIFICATION")
    save_logs(logs)
    print("📝 Run logged to dashboard.")
else:
    logs = load_logs()
    logs = log_run(logs, "POST", topic, False, "-", "-", "PASSED VERIFICATION - USER CANCELLED")
    save_logs(logs)
    print("\nPost cancelled.")