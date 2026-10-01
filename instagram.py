from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import os
import re
import requests
import json
import subprocess

# ---------- Setup ----------
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
instagram_id = os.getenv("INSTAGRAM_PLATFORM_ID")

client = genai.Client(api_key=gemini_key)

LOG_FILE = "logs.json"
OUTPUT_DIR = "instagram_posts"
MODEL = "gemini-3.5-flash-lite"

MUSIC_DIR = "music"      # folder with red.mp3, green.mp3, navy.mp3, purple.mp3, gold.mp3
MAKE_REEL = True         # True = post a Reel with music, False = post the plain image
REEL_SECONDS = 15        # Reel length (Instagram allows 3-90 seconds)

HASHTAGS = """
#SaiNithish #MG3Verse #TripuraAI #AI #GenerativeAI #AIAgents #AIAutomation #AIEngineering #BusinessAutomation #AIForBusiness #DigitalTransformation #FutureOfWork
"""

# ---------- Themes (picked automatically from the topic) ----------
THEMES = {
    "urgent":    {"name": "Bold Red",      "color": (196, 30, 48),  "music": "red.mp3"},
    "jobs":      {"name": "Forest Green",  "color": (30, 106, 58),  "music": "green.mp3"},
    "founders":  {"name": "Deep Navy",     "color": (18, 44, 112),  "music": "navy.mp3"},
    "data":      {"name": "Purple",        "color": (108, 48, 160), "music": "purple.mp3"},
    "quickwins": {"name": "Classic Gold",  "color": (180, 130, 30), "music": "gold.mp3"},
}

KEYWORDS = {
    "urgent":   ["risk", "danger", "replac", "urgent", "warning", "fall behind", "threat",
                 "security", "ignore", "crisis", "autonomous", "growing"],
    "jobs":     ["job", "skill", "career", "hire", "hiring", "salary", "learn", "workforce",
                 "automate", "judgment", "thinking"],
    "founders": ["founder", "personal", "story", "stories", "human", "leader", "mindset",
                 "entrepreneur", "audience", "brand"],
    "data":     ["data", "company", "analytics", "enterprise", "report", "search", "rank",
                 "chatgpt", "google", "seo"],
}


def pick_theme(topic):
    """Keyword-based theme choice (used as fallback and to force red on urgent topics)."""
    t = topic.lower()
    for key, words in KEYWORDS.items():
        if any(w in t for w in words):
            return key
    return "quickwins"


# ---------- Colors ----------
DARK = (20, 20, 40)
SOFT = (85, 85, 105)
LINE = (222, 222, 232)
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
    """Ask Gemini for the text on the image AND the best theme for the topic."""
    prompt = f"""
You design viral Instagram cards. Topic: "{topic}"

Return ONLY valid JSON (no markdown, no backticks) in this exact shape:
{{
  "theme": "one of: urgent, jobs, founders, data, quickwins",
  "headline": "bold hook, max 7 words, makes people stop scrolling",
  "highlight": "the 1-2 most important words copied from the headline (never filler words like by, in, for)",
  "points": [
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}},
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}},
    {{"title": "max 28 characters", "desc": "max 55 characters, one clear benefit"}}
  ]
}}

Theme rules:
- urgent = urgent, risky or warning topics
- jobs = jobs, skills, careers topics
- founders = personal, human, founder or story topics
- data = data, company, search or analytics topics
- quickwins = quick wins, tips, general topics

Rules: punchy, specific, no emojis, no numbering.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        data = json.loads(text)
        assert data.get("headline") and len(data.get("points", [])) >= 3
        if data.get("theme") not in THEMES:
            data["theme"] = pick_theme(topic)
        # urgent/risky topics always get red, even if Gemini picks another theme
        if pick_theme(topic) == "urgent":
            data["theme"] = "urgent"
        return data
    except Exception as e:
        print(f"(Card text fallback used: {e})")
        return {
            "theme": pick_theme(topic),
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


def balanced_lines(draw, text, font, max_w, max_lines=2):
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


def generate_image(content, theme_key="quickwins"):
    """Light 1080x1350 card. Accent color changes with the topic's theme."""
    print("Generating image...")
    theme = THEMES.get(theme_key, THEMES["quickwins"])
    ACCENT = theme["color"]
    W, H = 1080, 1350
    LEFT, RIGHT = 100, W - 100

    # 1. Light background
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(252 - 8 * t), int(252 - 8 * t), int(255 - 5 * t)))
    base = bg.convert("RGBA")
    draw = ImageDraw.Draw(base)

    # 2. Themed frame + top and bottom bars
    draw.rectangle([44, 44, W - 44, H - 44], outline=ACCENT, width=2)
    draw.rectangle([44, 44, W - 44, 54], fill=ACCENT)
    draw.rectangle([44, H - 54, W - 44, H - 44], fill=ACCENT)

    # 3. Headline — serif, auto-fit, highlighted words in theme color
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
    draw.rectangle([LEFT, y - 34, LEFT + 90, y - 29], fill=ACCENT)
    space = draw.textlength(" ", font=f_head)
    for line in lines:
        x = LEFT
        for w in line:
            key = re.sub(r"\W", "", w.lower())
            draw.text((x, y), w, font=f_head, fill=ACCENT if key in hl_set else DARK)
            x += draw.textlength(w, font=f_head) + space
        y += line_h

    # 4. Divider
    draw.rectangle([LEFT, 655, RIGHT, 657], fill=ACCENT)

    # 5. Numbered list
    points = [norm_point(p) for p in content["points"][:3]]
    row_h, list_top = 185, 680
    f_num = load_font(68, serif=True)
    f_desc = load_font(31, False)
    text_x = LEFT + 150
    text_w = RIGHT - text_x
    for i, p in enumerate(points):
        row_top = list_top + i * row_h
        cy = row_top + row_h // 2
        draw.text((LEFT, cy), f"0{i + 1}", font=f_num, fill=ACCENT, anchor="lm")

        t_size = 44
        while t_size > 30 and draw.textlength(p["title"], font=load_font(t_size, serif=True)) > text_w:
            t_size -= 2
        f_t = load_font(t_size, serif=True)
        d_lines = balanced_lines(draw, p["desc"], f_desc, text_w) if p["desc"] else []
        block = 52 + ((10 + len(d_lines) * 40) if d_lines else 0)
        ty = cy - block // 2
        draw.text((text_x, ty), p["title"], font=f_t, fill=DARK)
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


# ---------- Reel (image + music -> MP4) ----------
def make_reel(image_path, theme_key, seconds=REEL_SECONDS):
    """Turn the card into a 1080x1920 MP4 Reel with the theme's music."""
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        print("❌ Run: pip install moviepy imageio-ffmpeg")
        return None

    music_path = os.path.join(MUSIC_DIR, THEMES[theme_key]["music"])
    out_path = image_path.replace(".jpg", ".mp4")
    fade_out_at = max(seconds - 2, 0)

    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", "30", "-i", image_path]
    if os.path.exists(music_path):
        cmd += ["-stream_loop", "-1", "-i", music_path]
    else:
        print(f"⚠️ Music file not found: {music_path} — making a silent Reel")
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += [
        "-t", str(seconds),
        "-vf", "scale=1080:1350,pad=1080:1920:0:285:color=0xFCFCFF,format=yuv420p",
        "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={fade_out_at}:d=2",
        "-c:v", "libx264", "-tune", "stillimage", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        out_path,
    ]
    print(f"Making Reel with music ({THEMES[theme_key]['music']})...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Video creation failed:")
        print(result.stderr[-600:])
        return None
    print(f"✅ Reel created: {os.path.abspath(out_path)}")
    return out_path


# ---------- Publora ----------
def upload_media_to_publora(file_path):
    print("Uploading to Publora...")
    try:
        url = "https://api.publora.com/api/v1/upload-media"
        headers = {"x-publora-key": publora_key}
        is_video = file_path.lower().endswith(".mp4")
        name, mime = ("reel.mp4", "video/mp4") if is_video else ("image.jpg", "image/jpeg")
        with open(file_path, "rb") as f:
            files = {"file": (name, f, mime)}
            response = requests.post(url, headers=headers, files=files, timeout=300)
        print("Upload status:", response.status_code)
        print("Upload response:", response.text[:300])
        if response.status_code == 200:
            data = response.json()
            return data.get("url") or data.get("mediaUrl")
    except Exception as e:
        print(f"Upload failed: {e}")
    return None


def post_to_instagram(caption, media_url):
    url = "https://api.publora.com/api/v1/create-post"
    headers = {"x-publora-key": publora_key, "Content-Type": "application/json"}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    payload = {
        "platforms": [instagram_id],
        "content": caption,
        "mediaUrls": [media_url],
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
    theme_key = card.get("theme", "quickwins")
    print(f"🎨 Theme selected: {THEMES[theme_key]['name']}")
    image_path = generate_image(card, theme_key)

    media_path = image_path
    if MAKE_REEL:
        reel_path = make_reel(image_path, theme_key)
        if reel_path:
            media_path = reel_path

    # Open the result automatically (Reel plays with music)
    try:
        if os.name == "nt":
            os.startfile(os.path.abspath(media_path))
    except Exception:
        pass

    kind = "Reel" if media_path.endswith(".mp4") else "image"
    approve = input(f"\nDo you want to post this {kind} to Instagram? (yes/no): ")

    if approve.lower() == "yes":
        media_url = upload_media_to_publora(media_path)
        if media_url:
            print(f"\nMedia URL: {media_url}")
            print("\nPosting to Instagram...")
            result = post_to_instagram(caption, media_url)
            success = result.get("success", False)
            post_id = result.get("postGroupId", "-")
            print("\n✅ Posted successfully to Instagram!" if success else "\n❌ Something went wrong.")
            logs = log_run(load_logs(), topic, success, post_id)
            save_logs(logs)
            print("📝 Run logged to dashboard.")
        else:
            print("\n❌ Upload failed.")
    else:
        logs = log_run(load_logs(), topic, False)
        save_logs(logs)
        print("\nPost cancelled.")