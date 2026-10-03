from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import re
import math
import json
import subprocess
import requests

# ---------- Setup ----------
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
publora_key = os.getenv("PUBLORA_API_KEY")
instagram_id = os.getenv("INSTAGRAM_PLATFORM_ID")

client = genai.Client(api_key=gemini_key)

LOG_FILE = "logs.json"
OUTPUT_DIR = "instagram_posts"
MODEL = "gemini-3.5-flash-lite"
MUSIC_DIR = "music"

# Reel settings
W, H = 1080, 1920          # full-screen vertical Reel
FPS = 30
SLIDE_SECONDS = 4          # every slide gets exactly this many seconds (4 slides = 16s)
TURN_SECONDS = 0.9         # length of the page-turn between slides
MUSIC_START = 0            # start the song from this second (e.g. 30 to skip a slow intro)

# Brand shown only on the last slide
BRAND_NAME = "MG3Verse"
BRAND_TAGLINE = "mg3verse.com"

HASHTAGS = """
#SaiNithish #MG3Verse #TripuraAI #AI #GenerativeAI #AIAgents #AIAutomation #AIEngineering #BusinessAutomation #AIForBusiness #DigitalTransformation #FutureOfWork
"""

# ---------- Themes (neon colors for the dark design) ----------
THEMES = {
    "urgent":    {"name": "Bold Red",     "color": (255, 64, 96),  "music": "red.mp3"},
    "jobs":      {"name": "Forest Green", "color": (48, 230, 140), "music": "green.mp3"},
    "founders":  {"name": "Deep Navy",    "color": (70, 140, 255), "music": "navy.mp3"},
    "data":      {"name": "Purple",       "color": (176, 92, 255), "music": "purple.mp3"},
    "quickwins": {"name": "Classic Gold", "color": (255, 196, 40), "music": "gold.mp3"},
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

ICONS = ["bolt", "target", "chart", "gear", "shield", "star", "check"]

WHITE = (255, 255, 255)
SOFT = (170, 178, 205)
GHOST = (26, 30, 58)
SECOND_GLOW = (110, 60, 220)
STOPWORDS = {"by", "in", "the", "a", "an", "for", "to", "of", "and", "on", "at", "with",
             "your", "you", "need", "is", "are", "that", "this", "it", "as", "be"}


def pick_theme(topic):
    t = topic.lower()
    for key, words in KEYWORDS.items():
        if any(w in t for w in words):
            return key
    return "quickwins"


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


# ---------- Gemini ----------
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
    prompt = f"""
You design viral Instagram Reel slides. Topic: "{topic}"

Return ONLY valid JSON (no markdown, no backticks) in this exact shape:
{{
  "theme": "one of: urgent, jobs, founders, data, quickwins",
  "headline": "bold hook, max 7 words, stops scrolling",
  "subheadline": "one supporting sentence, max 12 words",
  "highlight": "the 1-2 most important words copied from the headline (never filler words like by, in, for)",
  "points": [
    {{"title": "max 24 characters", "desc": "max 60 characters, one clear benefit", "icon": "one of: bolt, target, chart, gear, shield, star, check"}},
    {{"title": "max 24 characters", "desc": "max 60 characters, one clear benefit", "icon": "one of: bolt, target, chart, gear, shield, star, check"}}
  ],
  "cta": "closing line, max 10 words"
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
        assert data.get("headline") and len(data.get("points", [])) >= 2
        if data.get("theme") not in THEMES:
            data["theme"] = pick_theme(topic)
        if pick_theme(topic) == "urgent":
            data["theme"] = "urgent"
        return data
    except Exception as e:
        print(f"(Fallback used: {e})")
        return {
            "theme": pick_theme(topic),
            "headline": topic[:50].title(),
            "subheadline": "What you need to know right now",
            "highlight": topic.split()[0] if topic.split() else "",
            "points": [
                {"title": "Learn it first", "desc": "Move before your competitors do", "icon": "bolt"},
                {"title": "Start small", "desc": "Automate one task, then scale it", "icon": "target"},
            ],
            "cta": "Save this and share it with your team",
        }


# ---------- Fonts & text helpers ----------
FONT_HEAVY = [
    "C:/Windows/Fonts/seguibl.ttf",
    "C:/Windows/Fonts/ariblk.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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


def load_font(size, weight="reg"):
    paths = {"heavy": FONT_HEAVY, "bold": FONT_BOLD}.get(weight, FONT_REG)
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


def fit_text(draw, text, weight, start, min_size, max_w, max_lines):
    size = start
    while True:
        f = load_font(size, weight)
        lines = wrap_words(draw, text.split(), f, max_w)
        if (len(lines) <= max_lines and all(draw.textlength(w, font=f) <= max_w for l in lines for w in l)) \
                or size <= min_size:
            return f, size, lines
        size -= 4


def highlight_set(text, highlight):
    hl = {re.sub(r"\W", "", w.lower()) for w in highlight.split()}
    hl = {w for w in hl if w and w not in STOPWORDS}
    if not hl and text.split():
        hl = {re.sub(r"\W", "", max(text.split(), key=len).lower())}
    return hl


# ---------- Glow helpers ----------
def add_glow(base, center, radius, color, alpha=140):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.6))
    return Image.alpha_composite(base, layer)


def glow_rect(base, box, radius, color, width, glow_alpha=180, blur=14):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, outline=color + (glow_alpha,), width=width + 4)
    base = Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).rounded_rectangle(box, radius=radius, outline=color, width=width)
    return base


def paste_glow_layer(base, layer, blur=18):
    base = Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(blur)))
    return Image.alpha_composite(base, layer)


def draw_words_block(base, lines, font, y, line_h, color, accent, hl_set):
    """Draw centered lines; highlighted words are neon with a glow behind them."""
    draw = ImageDraw.Draw(base)
    space = draw.textlength(" ", font=font)
    items, yy = [], y
    for line in lines:
        widths = [draw.textlength(w, font=font) for w in line]
        x = (W - (sum(widths) + space * (len(line) - 1))) / 2
        for w, wd in zip(line, widths):
            items.append((x, yy, w, re.sub(r"\W", "", w.lower()) in hl_set))
            x += wd + space
        yy += line_h
    if any(i[3] for i in items):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for x, ty, w, hl in items:
            if hl:
                ld.text((x, ty), w, font=font, fill=accent + (255,))
        glow = layer.filter(ImageFilter.GaussianBlur(28))
        base = Image.alpha_composite(base, glow)
        base = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(base)
    for x, ty, w, hl in items:
        draw.text((x, ty), w, font=font, fill=accent if hl else color)
    return base, yy


# ---------- Icons (drawn with shapes, no emoji needed) ----------
def sparkle(d, cx, cy, r, fill):
    k = 0.22
    d.polygon([(cx, cy - r), (cx + r * k, cy - r * k), (cx + r, cy), (cx + r * k, cy + r * k),
               (cx, cy + r), (cx - r * k, cy + r * k), (cx - r, cy), (cx - r * k, cy - r * k)], fill=fill)


def icon_layer(name, cx, cy, r, color):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color + (255,)
    lw = max(6, int(r * 0.13))
    if name == "bolt":
        d.polygon([(cx + 0.18 * r, cy - r), (cx - 0.6 * r, cy + 0.12 * r), (cx - 0.05 * r, cy + 0.12 * r),
                   (cx - 0.22 * r, cy + r), (cx + 0.6 * r, cy - 0.2 * r), (cx + 0.05 * r, cy - 0.2 * r)], fill=c)
    elif name == "target":
        for rr in (1.0, 0.64):
            d.ellipse([cx - rr * r, cy - rr * r, cx + rr * r, cy + rr * r], outline=c, width=lw)
        d.ellipse([cx - 0.27 * r, cy - 0.27 * r, cx + 0.27 * r, cy + 0.27 * r], fill=c)
    elif name == "chart":
        bw, gap, bottom = 0.42 * r, 0.2 * r, cy + 0.85 * r
        x = cx - (3 * bw + 2 * gap) / 2
        for h in (0.75 * r, 1.25 * r, 1.75 * r):
            d.rounded_rectangle([x, bottom - h, x + bw, bottom], radius=int(bw * 0.2), fill=c)
            x += bw + gap
    elif name == "gear":
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + math.cos(a) * 0.7 * r, cy + math.sin(a) * 0.7 * r),
                    (cx + math.cos(a) * 1.0 * r, cy + math.sin(a) * 1.0 * r)], fill=c, width=int(r * 0.3))
        d.ellipse([cx - 0.76 * r, cy - 0.76 * r, cx + 0.76 * r, cy + 0.76 * r], outline=c, width=int(r * 0.2))
        d.ellipse([cx - 0.28 * r, cy - 0.28 * r, cx + 0.28 * r, cy + 0.28 * r], outline=c, width=lw)
    elif name == "shield":
        pts = [(cx - 0.72 * r, cy - 0.78 * r), (cx, cy - r), (cx + 0.72 * r, cy - 0.78 * r),
               (cx + 0.72 * r, cy + 0.1 * r), (cx, cy + r), (cx - 0.72 * r, cy + 0.1 * r)]
        d.line(pts + [pts[0]], fill=c, width=lw, joint="curve")
        d.line([(cx - 0.32 * r, cy), (cx - 0.08 * r, cy + 0.28 * r), (cx + 0.38 * r, cy - 0.25 * r)],
               fill=c, width=lw, joint="curve")
    elif name == "check":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=lw)
        d.line([(cx - 0.45 * r, cy), (cx - 0.12 * r, cy + 0.35 * r), (cx + 0.5 * r, cy - 0.32 * r)],
               fill=c, width=lw + 2, joint="curve")
    else:  # star / sparkle
        sparkle(d, cx, cy, r, c)
        sparkle(d, cx + 0.8 * r, cy - 0.8 * r, 0.32 * r, c)
    return layer


# ---------- Dark background ----------
def dark_bg(accent):
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(7 + 14 * t), 9, int(22 + 26 * t)))
    for gx in range(36, W, 72):
        for gy in range(36, H, 72):
            d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(34, 38, 68))
    base = bg.convert("RGBA")
    base = add_glow(base, (W - 100, 240), 430, accent, 85)
    base = add_glow(base, (80, H - 260), 380, SECOND_GLOW, 70)
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for r in (260, 380, 500):
        rd.ellipse([W - 100 - r, 240 - r, W - 100 + r, 240 + r], outline=accent + (34,), width=2)
    base = Image.alpha_composite(base, ring)
    return glow_rect(base, (40, 40, W - 40, H - 40), 36, accent, 3, 150, 12)


# ---------- The 4 slides ----------
def slide_hook(content, accent):
    base = dark_bg(accent)
    draw = ImageDraw.Draw(base)
    headline = content["headline"].strip()
    hl = highlight_set(headline, content.get("highlight", ""))
    f, size, lines = fit_text(draw, headline, "heavy", 150, 70, 900, 5)
    line_h = int(size * 1.16)
    f_sub = load_font(46)
    sub = content.get("subheadline", "").strip()
    sub_lines = wrap_words(draw, sub.split(), f_sub, 820) if sub else []
    block = len(lines) * line_h + ((70 + len(sub_lines) * 62) if sub_lines else 0)
    y = (H - block) // 2 - 40
    draw.rounded_rectangle([W // 2 - 70, y - 60, W // 2 + 70, y - 52], radius=4, fill=accent)
    base, yend = draw_words_block(base, lines, f, y, line_h, WHITE, accent, hl)
    draw = ImageDraw.Draw(base)
    yy = yend + 50
    for sl in sub_lines:
        draw.text((W // 2, yy), " ".join(sl), font=f_sub, fill=SOFT, anchor="ma")
        yy += 62
    return base.convert("RGB")


def slide_point(content, accent, idx):
    p = content["points"][idx]
    base = dark_bg(accent)
    draw = ImageDraw.Draw(base)
    f_title, tsize, t_lines = fit_text(draw, p["title"], "heavy", 82, 54, 780, 2)
    t_lh = int(tsize * 1.18)
    f_desc = load_font(44)
    d_lines = wrap_words(draw, p.get("desc", "").split(), f_desc, 780)[:3]
    card_h = 80 + len(t_lines) * t_lh + 50 + len(d_lines) * 60 + 80
    card_top, top_icon = 880, 390
    oy = (H - (card_top + card_h - top_icon)) // 2 - top_icon
    cx, icy = W // 2, 560 + oy

    # ghost number behind the icon
    draw.text((cx, icy - 40), f"0{idx + 1}", font=load_font(460, "heavy"), fill=GHOST, anchor="mm")

    # glowing icon badge
    draw.ellipse([cx - 170, icy - 170, cx + 170, icy + 170], fill=(14, 18, 40))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([cx - 170, icy - 170, cx + 170, icy + 170], outline=accent + (255,), width=6)
    base = paste_glow_layer(base, ring, 20)
    icon = (p.get("icon") or "").lower()
    if icon not in ICONS:
        icon = ICONS[(idx * 2) % len(ICONS)]
    base = paste_glow_layer(base, icon_layer(icon, cx, icy, 82, accent), 16)

    # glass card with neon border
    box = (90, card_top + oy, W - 90, card_top + oy + card_h)
    fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(fill).rounded_rectangle(box, radius=40, fill=(255, 255, 255, 16))
    base = Image.alpha_composite(base, fill)
    base = glow_rect(base, box, 40, accent, 3, 170, 14)

    draw = ImageDraw.Draw(base)
    y = card_top + oy + 80
    for line in t_lines:
        draw.text((cx, y), " ".join(line), font=f_title, fill=WHITE, anchor="ma")
        y += t_lh
    y += 10
    draw.rounded_rectangle([cx - 70, y, cx + 70, y + 8], radius=4, fill=accent)
    y += 40
    for dl in d_lines:
        draw.text((cx, y), " ".join(dl), font=f_desc, fill=SOFT, anchor="ma")
        y += 60
    return base.convert("RGB")


def slide_cta(content, accent):
    base = dark_bg(accent)
    base = add_glow(base, (W // 2, H // 2 - 100), 460, accent, 70)
    draw = ImageDraw.Draw(base)
    cta = (content.get("cta") or "Save this and share it with your team").strip()
    hl = {re.sub(r"\W", "", w.lower()) for w in cta.split()[-2:]}
    f, size, lines = fit_text(draw, cta, "heavy", 112, 60, 880, 4)
    line_h = int(size * 1.16)
    block = len(lines) * line_h + 80 + 130 + 90
    y = (H - block) // 2
    base, yend = draw_words_block(base, lines, f, y, line_h, WHITE, accent, hl)

    f_brand = load_font(64, "heavy")
    tw = ImageDraw.Draw(base).textlength(BRAND_NAME, font=f_brand)
    pw = int(tw) + 170
    px0, py0 = (W - pw) // 2, yend + 80
    base = glow_rect(base, (px0, py0, px0 + pw, py0 + 130), 65, accent, 4, 200, 16)
    draw = ImageDraw.Draw(base)
    draw.text((W // 2, py0 + 65), BRAND_NAME, font=f_brand, fill=WHITE, anchor="mm")
    if BRAND_TAGLINE:
        draw.text((W // 2, py0 + 130 + 40), BRAND_TAGLINE, font=load_font(40), fill=SOFT, anchor="ma")
    return base.convert("RGB")


def generate_slides(content, theme_key):
    accent = THEMES[theme_key]["color"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slides = [slide_hook(content, accent),
              slide_point(content, accent, 0),
              slide_point(content, accent, 1),
              slide_cta(content, accent)]
    paths = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(OUTPUT_DIR, f"slide{i}_{ts}.jpg")
        s.save(p, "JPEG", quality=95)
        paths.append(p)
    print("✅ 4 slides created")
    return paths


# ---------- Page-turn transition ----------
def _shadow_mask(width, strength, flip=False):
    m = Image.new("L", (width, 1))
    for x in range(width):
        v = min((1 - x / width) ** 2 * strength, 1)
        m.putpixel((width - 1 - x if flip else x, 0), int(255 * v))
    return m.resize((width, H))


def page_turn(old, new, t):
    """The old page folds over to the left edge, like turning a page."""
    e = t * t * (3 - 2 * t)
    w = int(W * (1 - e))
    if w <= 2:
        return new
    frame = new.copy()
    sh_w = min(300, W - w)
    if sh_w > 0:
        m = _shadow_mask(300, 0.75 * (1 - 0.4 * e)).crop((0, 0, sh_w, H))
        frame.paste(Image.new("RGB", (sh_w, H), (0, 0, 0)), (w, 0), m)
    old_s = old.resize((w, H), Image.BILINEAR)
    in_w = min(220, w)
    m2 = _shadow_mask(220, 0.55, flip=True).crop((220 - in_w, 0, 220, H))
    old_s.paste(Image.new("RGB", (in_w, H), (0, 0, 0)), (w - in_w, 0), m2)
    frame.paste(old_s, (0, 0))
    ImageDraw.Draw(frame).line([(w - 1, 0), (w - 1, H)], fill=(255, 255, 255), width=2)
    return frame


# ---------- Reel ----------
def make_reel(slide_paths, theme_key):
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        print("❌ Run: pip install moviepy imageio-ffmpeg")
        return None

    slides = [Image.open(p).convert("RGB") for p in slide_paths]
    n = len(slides)
    total = n * SLIDE_SECONDS
    n_frames = int(total * FPS)
    music_path = os.path.join(MUSIC_DIR, THEMES[theme_key]["music"])
    out_path = os.path.join(OUTPUT_DIR, f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    cmd = [ffmpeg, "-y", "-loglevel", "error", "-nostats",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if os.path.exists(music_path):
        cmd += ["-stream_loop", "-1", "-i", music_path]
    else:
        print(f"⚠️ Music not found: {music_path} — silent Reel")
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    af = f"afade=t=in:st=0:d=1,afade=t=out:st={max(total - 2, 0)}:d=2"
    if MUSIC_START > 0:
        af = f"atrim=start={MUSIC_START},asetpts=PTS-STARTPTS," + af
    cmd += ["-map", "0:v", "-map", "1:a", "-t", str(total), "-af", af,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", out_path]

    print(f"Rendering Reel: {n} slides x {SLIDE_SECONDS}s = {total}s with page-turn transitions...")
    static = [s.tobytes() for s in slides]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for f in range(n_frames):
            T = f / FPS
            i = min(int(T // SLIDE_SECONDS), n - 1)
            local = T - i * SLIDE_SECONDS
            turn_start = SLIDE_SECONDS - TURN_SECONDS
            if i < n - 1 and local >= turn_start:
                t = (local - turn_start) / TURN_SECONDS
                data = page_turn(slides[i], slides[i + 1], t).tobytes()
            else:
                data = static[i]
            proc.stdin.write(data)
            if f % 120 == 0:
                print(f"  ...{int(100 * f / n_frames)}%")
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode(errors="ignore")
    proc.wait()
    if proc.returncode != 0:
        print("❌ Reel creation failed:")
        print(err[-800:])
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

    print("\nGenerating slide content...")
    card = generate_card_content(topic)
    theme_key = card.get("theme", "quickwins")
    print(f"🎨 Theme: {THEMES[theme_key]['name']}")

    slide_paths = generate_slides(card, theme_key)
    reel_path = make_reel(slide_paths, theme_key)

    media_path = reel_path if reel_path else slide_paths[0]
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