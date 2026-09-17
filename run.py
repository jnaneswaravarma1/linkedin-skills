from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import requests

# Load API keys from .env
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
linkedin_id = os.getenv("LINKEDIN_PLATFORM_ID")

# Setup Gemini
client = genai.Client(api_key=gemini_key)

# Hashtags for better reach
HASHTAGS = """
#SaiNithish #MG3Verse #TripuraAI #AI #GenerativeAI #AIAgents #AIAutomation #AIEngineering #BusinessAutomation #AIForBusiness #DigitalTransformation #FutureOfWork
"""

def read_skill(skill_name):
    path = f"skills/{skill_name}/SKILL.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def clean_post(text):
    """Remove unnecessary gaps and clean formatting"""
    lines = text.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        if line.strip() == '':
            if not prev_empty:
                cleaned.append('')
            prev_empty = True
        else:
            cleaned.append(line.strip())
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
- Use relevant emojis naturally in the text
- Use emojis like 🚀 💡 ⚡ 🎯 🔥 📊 ✅ where they fit
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
    # Add hashtags at the end
    return post + "\n\n" + HASHTAGS.strip()

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
    print("Raw response:", response.text)
    if response.text:
        return response.json()
    else:
        return {"status": "empty response from Publora"}

# Main flow
print("=" * 50)
print("LINKEDIN AUTO-POSTER — POWERED BY GEMINI")
print("=" * 50)

topic = input("\nWhat topic do you want to post about? : ")

print("\nGenerating post...")
post_content = generate_post(topic)

print("\n" + "=" * 50)
print("GENERATED POST:")
print("=" * 50)
print(post_content)

approve = input("\nDo you want to post this to LinkedIn? (yes/no): ")

if approve.lower() == "yes":
    print("\nPosting to LinkedIn...")
    result = post_to_linkedin(post_content)
    print("\nResult:", result)
    if result.get("success"):
        print("\n✅ Posted successfully to LinkedIn!")
    else:
        print("\n❌ Something went wrong. Check result above.")
else:
    print("\nPost cancelled. Run again to try a new topic.")