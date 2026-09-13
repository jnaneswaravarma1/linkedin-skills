from google import genai
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Setup Gemini
client = genai.Client(api_key=api_key)

def read_skill(skill_name):
    """Read the SKILL.md file for a given skill"""
    path = f"skills/{skill_name}/SKILL.md"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_skill(skill_name, user_prompt):
    """Run a skill with a user prompt"""
    skill_instructions = read_skill(skill_name)
    
    full_prompt = f"""
You are a LinkedIn content expert.
Follow these skill instructions exactly:

{skill_instructions}

User request: {user_prompt}

Generate the output now following the skill instructions.
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=full_prompt
    )
    return response.text

# Run linkedin-post-writer skill
print("=" * 50)
print("LINKEDIN POST WRITER — OUTPUT")
print("=" * 50)
output = run_skill(
    "linkedin-post-writer",
    "Write a viral LinkedIn post about why AI skills are essential for developers in 2026"
)
print(output)

print("\n" + "=" * 50)
print("LINKEDIN COMMENT DRAFTER — OUTPUT")
print("=" * 50)
output2 = run_skill(
    "linkedin-comment-drafter",
    "Draft a thoughtful comment on a post about AI replacing developers"
)
print(output2)