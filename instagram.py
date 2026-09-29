from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import re
import requests
import json

# ---------- Setup ----------
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
instagram_id = os.getenv("INSTAGRAM_PLATFORM_ID")

client = genai.Client(api_key=gemini_key)

LOG_FILE = "logs.json"
OUTPUT_DIR = "instagram_posts"
MODEL = "gemini-3.5-flash-lite"

HASHTAGS = """
#SaiNithish #MG3Verse #TripuraAI #AI #GenerativeAI #AIAgents #AIAutomation #AIEngineering #BusinessAutomation #AIForBusiness #DigitalTransformation #FutureOfWork
"""

# Colors — classic navy + gold
WHITE = (255, 255, 255)
GOLD = (226, 183, 74)
GOLD_DIM = (150, 122, 58)
NAVY_GLOW = (40, 80, 170)
SOFT = (190, 198, 222)
LINE = (52, 64, 96)
STOPWORDS = {"by", "in", "the", "a", "an", "for", "to", "of", "and", "on", "at", "with",
             "your", "you", "need", "is", "are", "that", "this", "it", "as", "be"}


# ---------- Logging ----------
def load_logs():
    if not os.path.exists(LOG_FILE):
        return {"keys": {}, "runs": []}
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def log_run(logs, topic, success, post_id=None):
    now = datetime.now()
    run = {
        "type": "INSTAGRAM POST",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "topic": topic,
        "success": success,
        "published_at": now.strftime("%H:%M:%S") if success else "-",
        "post_id": post_id or "-",
    }
    logs["runs"].append(run)
    return logs


# ---------- Gemini content ----------
def generate_caption(topic):
    prompt = f"""
You are an Instagram content expert.

Write an Instagram caption about: "{topic}"

STRICT RULES:
- First line must be a hook — max 125 characters
- Short punchy sentences — not long paragraphs
- 3 to 5 relevant emojis only where they add meaning
- Maximum 300 characters for the caption text
- End with one question to drive comments
- Do NOT add hashtags — added automatically
- No markdown like ** or ##

Write ONLY the caption text. Nothing else.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip() + "\n\n" + HASHTAGS.strip()


def generate_card_content(topic):
    """Ask Gemini for the text that goes ON the image."""
    prompt = f"""
You design viral Instagram cards. Topic: "{topic}"

Return ONLY valid JSON (no markdown, no backticks) in this exact shape:
{{
  "headline": "bold hook, max 7 words, makes people stop scrolling",
  "highlight": "the 1-2 most important words copied from the headline (never filler words like by, in, for)",
  "points": [
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}},
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}},
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}}
  ]
}}

Rules: punchy, specific, no emojis, no numbering.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        data = json.loads(text)
        assert data.get("headline") and len(data.get("points", [])) >= 3
        return data
    except Exception as e:
        print(f"(Card text fallback used: {e})")
        return {
            "headline": topic[:50].title(),
            "highlight": topic.split()[0] if topic.split() else "",
            "points": [
                {"title": "Learn it first", "desc": "Move before your competitors do"},
                {"title": "Start small", "desc": "Automate one task, then scale it"},
                {"title": "Stay consistent", "desc": "Consistency beats perfection"},
            ],
        }


# ---------- Image helpers ----------
FONT_SERIF = [
    "C:/Windows/Fonts/georgiab.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]
FONT_BOLD = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_REG = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(size, bold=False, serif=False):
    paths = FONT_SERIF if serif else (FONT_BOLD if bold else FONT_REG)
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_words(draw, words, font, max_w):
    lines, current = [], []
    for w in words:
        test = " ".join(current + [w])
        if current and draw.textlength(test, font=font) > max_w:
            lines.append(current)
            current = [w]
        else:
            current.append(w)
    if current:
        lines.append(current)
    return lines


def add_glow(base, center, radius, color, alpha=140):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.6))
    return Image.alpha_composite(base, layer)


def balanced_lines(draw, text, font, max_w, max_lines=2):
    """Wrap text; if it needs two lines, split them evenly (no lonely last word)."""
    words = text.split()
    lines = wrap_words(draw, words, font, max_w)
    if len(lines) == 2:
        best = None
        for k in range(1, len(words)):
            a = " ".join(words[:k])
            b = " ".join(words[k:])
            wa = draw.textlength(a, font=font)
            wb = draw.textlength(b, font=font)
            if max(wa, wb) <= max_w and (best is None or max(wa, wb) < best[0]):
                best = (max(wa, wb), [a, b])
        if best:
            return best[1]
    return [" ".join(l) for l in lines[:max_lines]]


def norm_point(p):
    if isinstance(p, str):
        return {"title": p, "desc": ""}
    return {"title": p.get("title", ""), "desc": p.get("desc", "")}


def generate_image(content):
    """Classic 1080x1350 (4:5) card: navy + gold, serif headline, numbered list."""
    print("Generating image...")
    W, H = 1080, 1350
    LEFT, RIGHT = 100, W - 100

    # 1. Navy gradient background with very soft glows
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(9 + 9 * t), int(16 + 18 * t), int(36 + 34 * t)))
    base = bg.convert("RGBA")
    base = add_glow(base, (1000, 60), 380, NAVY_GLOW, 55)
    base = add_glow(base, (40, 1300), 400, NAVY_GLOW, 60)
    draw = ImageDraw.Draw(base)

    # 2. Thin gold frame + top accent rule
    draw.rectangle([44, 44, W - 44, H - 44], outline=GOLD_DIM, width=2)

    # 3. Headline — serif, auto-fit, highlighted words in gold
    headline = content["headline"].strip()
    words = headline.split()
    hl_set = {re.sub(r"\W", "", w.lower()) for w in content.get("highlight", "").split()}
    hl_set = {w for w in hl_set if w and w not in STOPWORDS}
    if not hl_set:
        hl_set = {re.sub(r"\W", "", max(words, key=len).lower())}

    max_w = RIGHT - LEFT
    size = 128
    while size > 52:
        f_head = load_font(size, serif=True)
        lines = wrap_words(draw, words, f_head, max_w)
        if len(lines) <= 4 and len(lines) * int(size * 1.2) <= 440:
            break
        size -= 4
    f_head = load_font(size, serif=True)
    lines = wrap_words(draw, words, f_head, max_w)
    line_h = int(size * 1.2)
    y = 170 + (440 - len(lines) * line_h) // 2
    draw.rectangle([LEFT, y - 34, LEFT + 90, y - 29], fill=GOLD)
    space = draw.textlength(" ", font=f_head)
    for line in lines:
        x = LEFT
        for w in line:
            key = re.sub(r"\W", "", w.lower())
            draw.text((x, y), w, font=f_head, fill=GOLD if key in hl_set else WHITE)
            x += draw.textlength(w, font=f_head) + space
        y += line_h

    # 4. Divider between headline and list
    draw.rectangle([LEFT, 655, RIGHT, 657], fill=GOLD_DIM)

    # 5. Numbered list: 01 / 02 / 03
    points = [norm_point(p) for p in content["points"][:3]]
    row_h, list_top = 185, 680
    f_num = load_font(68, serif=True)
    f_desc = load_font(31, False)
    text_x = LEFT + 150
    text_w = RIGHT - text_x
    for i, p in enumerate(points):
        row_top = list_top + i * row_h
        cy = row_top + row_h // 2
        draw.text((LEFT, cy), f"0{i + 1}", font=f_num, fill=GOLD, anchor="lm")

        t_size = 44
        while t_size > 30 and draw.textlength(p["title"], font=load_font(t_size, serif=True)) > text_w:
            t_size -= 2
        f_t = load_font(t_size, serif=True)
        d_lines = balanced_lines(draw, p["desc"], f_desc, text_w) if p["desc"] else []
        block = 52 + ((10 + len(d_lines) * 40) if d_lines else 0)
        ty = cy - block // 2
        draw.text((text_x, ty), p["title"], font=f_t, fill=WHITE)
        dy = ty + 62
        for dl in d_lines:
            draw.text((text_x, dy), dl, font=f_desc, fill=SOFT)
            dy += 40
        if i < len(points) - 1:
            draw.rectangle([LEFT, row_top + row_h, RIGHT, row_top + row_h + 1], fill=LINE)

    # 6. Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    base.convert("RGB").save(path, "JPEG", quality=95)
    print(f"✅ Image created: {os.path.abspath(path)}")
    return path


# ---------- Publora ----------
def upload_image_to_publora(image_path):
    print("Uploading image to Publora...")
    try:
        url = "https://api.publora.com/api/v1/upload-media"
        headers = {"x-publora-key": publora_key}
        with open(image_path, "rb") as f:
            files = {"file": ("image.jpg", f, "image/jpeg")}
            response = requests.post(url, headers=headers, files=files)
        print("Upload status:", response.status_code)
        print("Upload response:", response.text[:200])
        if response.status_code == 200:
            data = response.json()
            return data.get("url") or data.get("mediaUrl")
    except Exception as e:
        print(f"Upload failed: {e}")
    return None


def post_to_instagram(caption, image_url):
    url = "https://api.publora.com/api/v1/create-post"
    headers = {"x-publora-key": publora_key, "Content-Type": "application/json"}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    payload = {
        "platforms": [instagram_id],
        "content": caption,
        "mediaUrls": [image_url],
        "scheduledTime": now,
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Status code:", response.status_code)
    print("Raw response:", response.text[:300])
    if response.text:
        return response.json()
    return {}


# ---------- Main ----------
if __name__ == "__main__":
    print("=" * 50)
    print("INSTAGRAM AUTO-POSTER — POWERED BY GEMINI")
    print("=" * 50)

    topic = input("\nWhat topic do you want to post about? : ")

    print("\nGenerating caption...")
    caption = generate_caption(topic)
    print("\n" + "=" * 50)
    print("GENERATED CAPTION:")
    print("=" * 50)
    print(caption)

    print("\nGenerating card text...")
    card = generate_card_content(topic)
    image_path = generate_image(card)

    # Open the image automatically on Windows
    try:
        if os.name == "nt":
            os.startfile(os.path.abspath(image_path))
    except Exception:
        pass

    approve = input("\nDo you want to post this to Instagram? (yes/no): ")

    if approve.lower() == "yes":
        image_url = upload_image_to_publora(image_path)
        if image_url:
            print(f"\nImage URL: {image_url}")
            print("\nPosting to Instagram...")
            result = post_to_instagram(caption, image_url)
            success = result.get("success", False)
            post_id = result.get("postGroupId", "-")
            print("\n✅ Posted successfully to Instagram!" if success else "\n❌ Something went wrong.")
            logs = log_run(load_logs(), topic, success, post_id)
            save_logs(logs)
            print("📝 Run logged to dashboard.")
        else:
            print("\n❌ Image upload failed.")
    else:
        logs = log_run(load_logs(), topic, False)
        save_logs(logs)
        print("\nPost cancelled.")