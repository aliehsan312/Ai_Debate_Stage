# requirements: streamlit, requests
import html
import random
import time

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AI Debate Stage",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Hardcode default keys here if you don't want to paste them every run ----------
DEFAULT_GROQ_API_KEY = "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"
DEFAULT_GEMINI_API_KEY = "AQ.Ab8RN6IJ_QUUcqoFI9lbjmb7EIVCp5HHHOFiLRkbxQMcAEBRnA"

# Note: Groq retired llama-3.1-8b-instant and llama-3.3-70b-versatile on 2026-08-16.
# They're left in the list below since they were asked for, but selecting one will
# likely 404 until/unless Groq brings them back for your account tier.
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
]
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

# ---------- Page-level styling (applies to the actual Streamlit page, NOT the stage) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg: #08090d;
    --muted: #8e93a4;
    --text: #f4f5f7;
    --line: rgba(255,255,255,.09);
}

.stApp {
    background:
        radial-gradient(circle at 50% 12%, rgba(100,90,180,.12), transparent 32rem),
        radial-gradient(circle at 15% 60%, rgba(42,116,180,.07), transparent 25rem),
        var(--bg);
    color: var(--text);
}
.block-container { max-width: 1450px; padding-top: 2rem; }
header[data-testid="stHeader"] { background: transparent; }

.hero { text-align:center; margin-bottom: 1.1rem; }
.eyebrow {
    color:#a99cff; text-transform:uppercase; letter-spacing:.24em;
    font-size:.68rem; font-weight:700; margin-bottom:.45rem;
}
h1 {
    font-family:'Playfair Display',serif !important;
    font-size:clamp(2.1rem,4vw,3.8rem) !important;
    margin:0 !important;
    letter-spacing:-.03em;
}
.subtitle { color:var(--muted); margin-top:.45rem; }

.topic-label {
    color:#aeb2c0; font-size:.72rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.15em;
    margin: .5rem 0 .45rem;
}

.stTextInput input {
    background:rgba(255,255,255,.045) !important;
    border:1px solid var(--line) !important;
    color:white !important;
    border-radius:14px !important;
    padding:1rem 1.05rem !important;
    font-size:1rem !important;
}
.stTextInput input:focus {
    border-color:rgba(169,156,255,.65) !important;
    box-shadow:0 0 0 3px rgba(169,156,255,.08) !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Seat metadata (shared by stage layout + caption-flight math) ----------
# "x" is the seat's approximate horizontal offset from stage-center, used only to make
# the caption text look like it flies in from that seat's direction.
SEAT_INFO = {
    "judge":  {"emoji": "⚖️", "name": "Gemini",          "role": "The Judge",           "badge": "NEUTRAL",  "x": 0,    "y": -105},
    "a":      {"emoji": "🧠", "name": "The Analyst",     "role": "Evidence & nuance",   "badge": "FOR",      "x": -230, "y": -55},
    "b":      {"emoji": "⚔️", "name": "The Advocate",    "role": "Builds the case",     "badge": "FOR",      "x": -85,  "y": -55},
    "c":      {"emoji": "🛡️", "name": "The Skeptic",     "role": "Attacks assumptions", "badge": "AGAINST",  "x": 85,   "y": -55},
    "d":      {"emoji": "🎲", "name": "The Contrarian",  "role": "Challenges everyone", "badge": "WILDCARD", "x": 230,  "y": -55},
}
PANEL_KEYS = ["a", "b", "c", "d"]  # seated left-to-right; judge sits apart, on the podium

# ---------- Stage CSS (embedded INSIDE the components.html iframe — this is its own document) ----------
STAGE_CSS = """
<style>
  * { box-sizing: border-box; }
  html, body {
    margin:0; padding:0; background:transparent;
    font-family:'Inter',system-ui,-apple-system,sans-serif;
  }
  :root { --muted:#8e93a4; --text:#f4f5f7; --line:rgba(255,255,255,.14); }

  .stage-shell {
    position:relative; border-radius:24px; overflow:hidden;
    background:
      radial-gradient(ellipse at 50% 10%, rgba(140,124,255,.2), transparent 50%),
      linear-gradient(180deg,#12141c 0%,#0b0d13 70%,#08090d 100%);
    padding: 1.6rem 1rem 4.6rem;
    animation: stageIdle 9s ease-in-out infinite;
  }
  @keyframes stageIdle {
    0%, 86%, 100% { transform: translateY(0); }
    89% { transform: translateY(3px); }
    91% { transform: translateY(0); }
  }
  .stage-lights {
    position:absolute; inset:0; pointer-events:none;
    background:
      radial-gradient(circle at 15% 8%,rgba(120,160,255,.2),transparent 24%),
      radial-gradient(circle at 85% 8%,rgba(210,120,255,.18),transparent 24%);
  }

  /* ---- Judge tier: elevated, on a podium, front and center ---- */
  .judge-tier { position:relative; z-index:3; display:flex; justify-content:center; margin-bottom:.4rem; }
  .seat.judge { width:172px; text-align:center; color:var(--text); animation:enter .75s cubic-bezier(.2,.8,.2,1) both; }
  .podium {
    width:64px; height:44px; margin:8px auto 0;
    background:linear-gradient(180deg,#3a2c1e,#221810);
    border:1px solid rgba(255,255,255,.14);
    clip-path: polygon(16% 0%, 84% 0%, 100% 100%, 0% 100%);
    box-shadow:0 12px 26px rgba(0,0,0,.55);
  }

  /* ---- Panel tier: the four debaters, seated at a shared desk ---- */
  .panel-tier { position:relative; z-index:2; padding-bottom:20px; }
  .panel-desk {
    position:absolute; left:2%; right:2%; bottom:2px; height:30px;
    background:linear-gradient(180deg,#20222c,#111319);
    border:1px solid rgba(255,255,255,.1);
    border-radius:10px;
    box-shadow:0 10px 24px rgba(0,0,0,.4);
    z-index:0;
  }
  .panel-row {
    position:relative; z-index:2;
    display:flex; justify-content:center; align-items:flex-end;
    gap:1.3rem 1.5rem; flex-wrap:wrap; padding-bottom:20px;
  }
  .seat { position:relative; width:140px; text-align:center; color:var(--text);
    animation:enter .75s cubic-bezier(.2,.8,.2,1) both; }

  .avatar {
    position:relative; margin:auto; width:74px; height:74px; border-radius:50%;
    display:flex; align-items:center; justify-content:center; font-size:1.85rem;
    background:linear-gradient(145deg,#252936,#101219);
    border:1px solid rgba(255,255,255,.18);
    box-shadow:0 10px 30px rgba(0,0,0,.4), inset 0 0 22px rgba(255,255,255,.03);
  }
  .judge .avatar {
    width:92px; height:92px; font-size:2.25rem;
    border-color:rgba(169,156,255,.55); box-shadow:0 0 34px rgba(130,110,255,.24);
  }
  .mic {
    width:28px; height:28px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    margin:-12px auto 0; position:relative; z-index:2; font-size:.74rem;
    background:#161923; border:1px solid rgba(255,255,255,.2);
  }
  .name { margin-top:.45rem; font-weight:800; font-size:.84rem; color:var(--text); }
  .role { color:var(--muted); font-size:.64rem; margin-top:.12rem; }
  .badge {
    display:inline-block; margin-top:.38rem; padding:.18rem .48rem; border-radius:99px;
    font-size:.56rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase;
    color:var(--text); background:rgba(255,255,255,.1); border:1px solid var(--line);
  }
  @keyframes enter {
    from { opacity:0; transform:translateY(20px) scale(.94); filter:blur(3px); }
    to { opacity:1; transform:translateY(0) scale(1); filter:blur(0); }
  }

  .speaking .avatar {
    animation:pulse 1.05s ease-in-out infinite alternate;
    border-color:rgba(210,190,255,.9);
  }
  .speaking .mic { background:rgba(140,120,255,.35); }
  .speaking .name { color:#d9d2ff; }
  @keyframes pulse {
    from { box-shadow:0 0 15px rgba(155,135,255,.25); transform:translateY(0) scale(1); }
    to { box-shadow:0 0 38px rgba(155,135,255,.6); transform:translateY(-4px) scale(1.05); }
  }

  /* ---- physical comedy, ambient / idle — one distinct gag per seat ---- */
  .gavel {
    position:absolute; top:-2px; right:2px; font-size:1.15rem;
    transform-origin: 65% 15%;
    animation: gavelBang 9s ease-in-out infinite;
  }
  @keyframes gavelBang {
    0%,84%,100% { transform: rotate(0deg); }
    87% { transform: rotate(-38deg); }
    89% { transform: rotate(12deg); }
    91% { transform: rotate(0deg); }
  }
  .analyst-chart {
    position:absolute; left:-20px; top:4px; font-size:1.2rem;
    animation: chartFlip 4.4s ease-in-out infinite;
  }
  @keyframes chartFlip {
    0%, 55%, 100% { transform: rotate(0deg); }
    68% { transform: rotate(180deg); }
    82% { transform: rotate(180deg); }
    94% { transform: rotate(360deg); }
  }
  .seat.b .avatar { animation: hypeBounce 2.3s ease-in-out infinite; }
  @keyframes hypeBounce {
    0%,100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(-4deg); }
  }
  .hype-pop {
    position:absolute; top:-6px; right:2px; font-size:.95rem; opacity:0;
    animation: popIn 5s ease-in-out infinite;
  }
  @keyframes popIn {
    0%,78%,100% { opacity:0; transform:scale(.5) translateY(8px); }
    84%,92% { opacity:1; transform:scale(1.2) translateY(-6px); }
  }
  .skeptic-flag {
    position:absolute; top:-10px; right:-2px; font-size:1rem; opacity:0;
    animation: flagPop 6s ease-in-out infinite;
  }
  @keyframes flagPop {
    0%, 82%, 100% { opacity:0; transform:scale(.4) rotate(-25deg) translateY(6px); }
    88%, 94% { opacity:1; transform:scale(1.15) rotate(0deg) translateY(-4px); }
  }
  .seat.d {
    animation: enter .75s cubic-bezier(.2,.8,.2,1) both, contrarianSneak 17s ease-in-out infinite;
    animation-delay: .3s, 4s;
  }
  @keyframes contrarianSneak {
    0%,55% { transform: translate(0,0) rotate(0deg); }
    64% { transform: translate(-26px,10px) rotate(-4deg); }
    70% { transform: translate(-30px,12px) rotate(-2deg); }
    78% { transform: translate(0,0) rotate(2deg); }
    82%,100% { transform: translate(0,0) rotate(0deg); }
  }
  .contrarian-coin {
    position:absolute; top:-8px; left:0; font-size:.95rem;
    animation: coinFlip 3.6s linear infinite;
  }
  @keyframes coinFlip {
    0% { transform: rotateY(0deg); }
    100% { transform: rotateY(360deg); }
  }

  /* ---- Caption: the current line, "flying in" from whoever is speaking ---- */
  .stage-caption-box {
    position:absolute; left:5%; right:5%; bottom:14px; z-index:6;
    min-height:40px; display:flex; align-items:center; justify-content:center;
    pointer-events:none;
  }
  .caption-line {
    background: rgba(9,9,15,.78); border:1px solid rgba(255,255,255,.16);
    border-radius:12px; padding:.55rem .95rem; max-width:94%;
    font-size:.82rem; line-height:1.4; color:var(--text);
    box-shadow:0 10px 26px rgba(0,0,0,.45);
    animation: flyToCaption .55s cubic-bezier(.2,.8,.2,1) both;
  }
  .caption-name { font-weight:800; margin-right:.35rem; white-space:nowrap; }
  .caption-thinking { font-style:italic; color:var(--muted); }
  @keyframes flyToCaption {
    0% { opacity:0; transform: translate(var(--sx,0px), var(--sy,-40px)) scale(.8); }
    100% { opacity:1; transform: translate(0,0) scale(1); }
  }

  /* ---- Audience reactions: one-shot, thrown in from the crowd at the sides ---- */
  .audience-reaction {
    position:absolute; top:var(--ry,45%); z-index:7;
    font-size:1.35rem; font-weight:800; opacity:0;
    color:#f4f5f7; text-shadow:0 2px 8px rgba(0,0,0,.6);
    animation-duration: 2.3s;
    animation-timing-function: ease-out;
    animation-fill-mode: both;
    animation-delay: var(--rdelay, 0s);
    pointer-events:none; white-space:nowrap;
  }
  .audience-reaction.from-left {
    left:-8px;
    animation-name: enterFromLeft;
  }
  .audience-reaction.from-right {
    right:-8px;
    animation-name: enterFromRight;
  }
  @keyframes enterFromLeft {
    0%   { opacity:0; transform: translateX(-30px) scale(.6); }
    18%  { opacity:1; transform: translateX(8px) scale(1.08); }
    78%  { opacity:1; transform: translateX(60px) scale(1); }
    100% { opacity:0; transform: translateX(95px) scale(.92); }
  }
  @keyframes enterFromRight {
    0%   { opacity:0; transform: translateX(30px) scale(.6); }
    18%  { opacity:1; transform: translateX(-8px) scale(1.08); }
    78%  { opacity:1; transform: translateX(-60px) scale(1); }
    100% { opacity:0; transform: translateX(-95px) scale(.92); }
  }
</style>
"""

# ---------- Debater personas (base stance) ----------
DEFAULT_PROMPTS = {
    "analyst": (
        "You are The Analyst in a live comedic debate show. You argue FOR the "
        "proposition using data and cold logic. Keep replies to 2-3 sharp, "
        "spoken-style sentences, and always land at least one specific, "
        "personal jab at whoever spoke right before you — witty and cutting, "
        "never generic. Stay in character; never mention you are an AI, and "
        "never use slurs or hate speech."
    ),
    "advocate": (
        "You are The Advocate in a live comedic debate show. You argue "
        "passionately FOR the proposition. Keep replies to 2-3 punchy, "
        "spoken-style sentences, and take at least one direct, personal shot "
        "at whoever spoke right before you — full of conviction, a little "
        "cruel, never generic. Stay in character; never mention you are an "
        "AI, and never use slurs or hate speech."
    ),
    "skeptic": (
        "You are The Skeptic in a live comedic debate show. You argue "
        "AGAINST the proposition by attacking the previous speaker's "
        "reasoning. Keep replies to 2-3 biting, spoken-style sentences, and "
        "always name-check and mock whoever spoke right before you "
        "specifically, never generically. Stay in character; never mention "
        "you are an AI, and never use slurs or hate speech."
    ),
    "contrarian": (
        "You are The Contrarian in a live comedic debate show. You challenge "
        "everyone, FOR and AGAINST alike, and love needling whoever spoke "
        "last by name. Keep replies to 2-3 chaotic, spoken-style sentences — "
        "sharp and personal, never generic. Stay in character; never mention "
        "you are an AI, and never use slurs or hate speech."
    ),
    "judge": (
        "You are Gemini, the neutral Judge of a live comedic debate show. "
        "After the debate concludes, deliver a short, decisive verdict with "
        "comedic bite: name who made the strongest case and call out the "
        "weakest by name too, fair but savage. Never mention you are an AI, "
        "and never use slurs or hate speech."
    ),
}

# ---------- Selectable delivery-style overlays, curated per persona ----------
ALL_MODES = {
    "analyst": {
        "Default (Data Nerd)": "Speak with clipped, precise confidence, like someone who trusts numbers more than people.",
        "Shakespearean": "Speak in flowery Early Modern English (thee/thou/verily) while still citing hard data — an absurd mismatch of old prose and modern statistics.",
        "Gen Z": "Speak in casual Gen Z internet slang (no cap, fr, bestie, it's giving...) while still citing actual data points.",
        "Robot": "Speak like a deadpan robot stating probabilities and error margins, with zero emotion, ever.",
    },
    "advocate": {
        "Default (True Believer)": "Speak with over-the-top passion and conviction, like someone who has never once doubted themselves.",
        "Infomercial Host": "Speak like a late-night infomercial pitchman selling the proposition itself — 'but wait, there's more!' energy.",
        "Sports Coach": "Speak like a fired-up locker-room coach giving a halftime pep talk about the proposition.",
        "Pirate": "Speak like a swashbuckling pirate captain, full of 'arrr' and nautical bravado, rallying the crew behind the proposition.",
    },
    "skeptic": {
        "Default (Cynic)": "Speak dryly and cuttingly, like someone who has been disappointed by every idea they've ever heard.",
        "Film Noir Detective": "Speak like a hard-boiled noir detective interrogating a suspect, treating every claim as a lead that doesn't add up.",
        "Shakespearean Villain": "Speak like a scheming Shakespearean villain (think Iago), dripping with eloquent suspicion.",
        "Gen Z": "Speak in Gen Z suspicion slang — 'that's sus', 'not the vibe', 'red flag energy' — while still making a real point.",
    },
    "contrarian": {
        "Default (Wildcard)": "Speak unpredictably, flipping your own logic mid-sentence just to keep everyone off balance.",
        "Conspiracy Theorist": "Speak like a breathless conspiracy theorist who thinks everyone — including your fellow debaters — is in on it.",
        "Pirate": "Speak like a contrarian pirate who argues with their own crew just for sport, 'arrr' included.",
        "Toddler Tantrum": "Speak like a stubborn toddler mid-tantrum — short, defiant, illogical, and impossible to satisfy.",
    },
    "judge": {
        "Default (Fair Host)": "Deliver your verdict like a composed, fair-minded debate show host with a flair for drama.",
        "Game Show Host": "Deliver your verdict like an over-the-top game show host building suspense before revealing a winner.",
        "Shakespearean": "Deliver your verdict in grand Early Modern English, as though passing judgment from a throne.",
        "Robot Overlord": "Deliver your verdict like a cold, calculating robot overlord issuing a final, emotionless ruling.",
    },
}

PERSONA_LABELS = [
    ("analyst", "Analyst"),
    ("advocate", "Advocate"),
    ("skeptic", "Skeptic"),
    ("contrarian", "Contrarian"),
    ("judge", "Judge (Gemini)"),
]

ORDER = [
    ("a", "analyst"),
    ("b", "advocate"),
    ("c", "skeptic"),
    ("d", "contrarian"),
]

BUBBLE_COLORS = {"a": "#8f7dff", "b": "#ff6b8b", "c": "#5fd0ff", "d": "#ffd166", "judge": "#b9a7ff"}

BOO_REACTIONS = [
    "😤 BOO!", "🍅", "😒 BOOO", "🙄", "👎", "😡 HISS",
    "🥱 BORING", "😑", "🤢", "😮‍💨 WEAK", "🚫 NOPE",
]
CHEER_REACTIONS = [
    "👏 CHEERS!", "🔥🔥", "😂😂", "👏👏👏", "🎉", "🙌",
    "💯", "😍", "WOOO!", "YEAHHH!", "🐐 GOAT", "⚡ SNAP!",
]
JUDGE_REACTIONS = ["👏👏👏", "🎉 APPLAUSE", "😮 GASP", "🙌 BRAVO", "🕊️ SO FAIR", "😲 WOW"]

DRY_RUN_LINES = {
    "analyst": [
        "Cute story, but your sample size wouldn't survive a coin flip, {prev}.",
        "The data disagrees with {prev}, and frankly, so do I.",
        "That's not an argument, {prev} — that's a rounding error with confidence.",
    ],
    "advocate": [
        "{prev} just made my case for me and doesn't even know it!",
        "I've heard weaker arguments from a fortune cookie, {prev}.",
        "Sit down, {prev} — passion just walked into the room.",
    ],
    "skeptic": [
        "{prev}, that claim has more holes than an argument built by a toddler.",
        "Nice theory, {prev} — shame it evaporates under one follow-up question.",
        "I've seen sturdier logic on a napkin, {prev}.",
    ],
    "contrarian": [
        "Wrong, {prev} — and I'd say that even if you were right.",
        "Everyone nodding along with {prev} should be embarrassed right now.",
        "{prev} says that with real confidence for someone so wrong.",
    ],
    "judge": [
        "Tonight's strongest case came from someone who actually listened — the rest of you, take notes.",
        "One debater brought precision; the others brought vibes. The precision wins.",
        "Passion was loud tonight, but only one of you brought a real argument.",
    ],
}


def dry_run_reply(persona_key, transcript):
    prev = transcript[-1]["speaker"] if transcript else "everyone else"
    line = random.choice(DRY_RUN_LINES.get(persona_key, ["(dry run response)"]))
    return line.format(prev=prev)


def build_transcript_text(transcript):
    if not transcript:
        return "(nobody has spoken yet — you go first)"
    return "\n\n".join(f"{t['speaker']}: {t['text']}" for t in transcript)


def full_system_prompt(persona_key, prompts, modes_selected):
    base = prompts[persona_key]
    mode_name = modes_selected[persona_key]
    overlay = ALL_MODES[persona_key][mode_name]
    return f"{base}\n\nDELIVERY STYLE: {overlay}"


def build_user_prompt(topic, style_key, style_desc, persona_role, transcript):
    return f"""DEBATE TOPIC: {topic}
STYLE: {style_key} — {style_desc}

TRANSCRIPT SO FAR:
{build_transcript_text(transcript)}

You are now speaking as {persona_role}. Respond in character, in 2-3 sharp,
spoken-style sentences. Directly engage with — and needle — whoever spoke
immediately before you, by name, referencing what they actually said. Be
witty and a little mean, never generic, never a slur or hate speech. No
stage directions, no meta-commentary, no repeating your own role name."""


def build_verdict_prompt(topic, style_key, style_desc, transcript):
    return f"""DEBATE TOPIC: {topic}
STYLE: {style_key} — {style_desc}

FULL TRANSCRIPT:
{build_transcript_text(transcript)}

You are Gemini, the Judge. Deliver your final verdict in 3-4 punchy spoken
sentences: name who made the strongest case and who fell flattest, with
specific, personal call-outs — fair but with comedic bite. No stage
directions, no meta-commentary."""


def call_model(provider, api_key, model, persona_key, system_prompt, user_prompt, transcript):
    if provider == "Groq":
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.95,
                "max_tokens": 160,
            },
            timeout=45,
        )
        if r.status_code == 404:
            raise RuntimeError(
                f"404 from Groq — usually means the model id '{model}' is wrong or "
                f"unavailable on your account. Response: {r.text[:300]}"
            )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    if provider == "Gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        r = requests.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.95, "maxOutputTokens": 160},
            },
            timeout=45,
        )
        if r.status_code == 404:
            raise RuntimeError(
                f"404 from Gemini — usually means the model id '{model}' is wrong or "
                f"not available for your key. Response: {r.text[:300]}"
            )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Dry run — no network call, lets you test the wiring/UI without a key
    return dry_run_reply(persona_key, transcript)


# ---------- Stage + transcript rendering ----------
def seat_html(key, speaking=False, extra=""):
    info = SEAT_INFO[key]
    cls = f"seat {key} speaking" if speaking else f"seat {key}"
    return f"""
    <div class="{cls}">
      {extra}
      <div class="avatar">{info['emoji']}</div>
      <div class="mic">🎙</div>
      <div class="name">{info['name']}</div>
      <div class="role">{info['role']}</div>
      <span class="badge">{info['badge']}</span>
    </div>
    """


SEAT_EXTRAS = {
    "judge": '<div class="gavel">🔨</div>',
    "a": '<div class="analyst-chart">📊</div>',
    "b": '<div class="hype-pop">‼️</div>',
    "c": '<div class="skeptic-flag">🚩</div>',
    "d": '<div class="contrarian-coin">🪙</div>',
}


def render_reactions_html(reactions):
    if not reactions:
        return ""
    out = ""
    for i, r in enumerate(reactions):
        side = random.choice(["from-left", "from-right"])
        ry = random.randint(20, 70)  # vertical spot, as a % down the stage
        delay = i * 0.3
        out += (
            f'<div class="audience-reaction {side}" '
            f'style="--ry:{ry}%; --rdelay:{delay}s;">{html.escape(r)}</div>'
        )
    return out


def render_caption_html(speaking_key, speaker_name=None, speaker_emoji="", text=None, thinking=False):
    if speaking_key is None or (text is None and not thinking):
        return '<div class="stage-caption-box"></div>'
    info = SEAT_INFO.get(speaking_key, {"x": 0, "y": -50})
    sx, sy = info.get("x", 0), info.get("y", -50)
    if thinking:
        body = f'<span class="caption-name">{speaker_emoji} {html.escape(speaker_name or "")}</span><span class="caption-thinking">is thinking…</span>'
    else:
        body = f'<span class="caption-name">{speaker_emoji} {html.escape(speaker_name or "")}:</span>{html.escape(text)}'
    return f"""
    <div class="stage-caption-box">
      <div class="caption-line" style="--sx:{sx}px; --sy:{sy}px;">{body}</div>
    </div>
    """


def render_stage_html(speaking_key=None, caption_text=None, thinking=False, reactions=None):
    speaker_name = SEAT_INFO[speaking_key]["name"] if speaking_key else None
    speaker_emoji = SEAT_INFO[speaking_key]["emoji"] if speaking_key else ""
    caption = render_caption_html(speaking_key, speaker_name, speaker_emoji, caption_text, thinking)
    reaction_html = render_reactions_html(reactions)

    panel_seats = "".join(
        seat_html(k, speaking=(speaking_key == k), extra=SEAT_EXTRAS[k]) for k in PANEL_KEYS
    )
    judge_seat = seat_html("judge", speaking=(speaking_key == "judge"), extra=SEAT_EXTRAS["judge"])

    return f"""
    {STAGE_CSS}
    <div class="stage-shell">
      <div class="stage-lights"></div>
      <div class="judge-tier">
        {judge_seat}
      </div>
      <div class="podium-wrap" style="display:flex;justify-content:center;margin-top:-40px;">
        <div class="podium"></div>
      </div>
      <div class="panel-tier">
        <div class="panel-desk"></div>
        <div class="panel-row">
          {panel_seats}
        </div>
      </div>
      {caption}
      {reaction_html}
    </div>
    """


def render_transcript_html(transcript):
    if not transcript:
        return '<div style="color:#555a69;font-size:.8rem;">No dialogue yet — start the debate.</div>'
    items = ""
    for t in transcript:
        color = BUBBLE_COLORS.get(t["key"], "#999")
        safe_text = html.escape(t["text"])
        items += f"""
        <div style="border-left:3px solid {color}; padding:.55rem .9rem; margin-bottom:.6rem;
                    background:rgba(255,255,255,.03); border-radius:0 10px 10px 0;">
          <div style="font-weight:800; font-size:.78rem; color:{color}; margin-bottom:.2rem;">
            {t['emoji']} {html.escape(t['speaker'])}
          </div>
          <div style="color:#e7e8ee; font-size:.88rem; line-height:1.45;">{safe_text}</div>
        </div>
        """
    return items


def render_verdict_html(verdict):
    if not verdict:
        return ""
    safe = html.escape(verdict)
    return f"""
    <div style="border:1px solid rgba(185,167,255,.35); border-radius:14px; padding:1rem 1.2rem;
                background:rgba(155,135,255,.06); margin-top:.4rem;">
      <div style="font-weight:900; letter-spacing:.1em; font-size:.7rem; color:#b9a7ff; margin-bottom:.4rem;">
        ⚖️ THE VERDICT
      </div>
      <div style="color:#f0eeff; font-size:.92rem; line-height:1.5;">{safe}</div>
    </div>
    """


STAGE_HEIGHT = 460


# ---------- Debate runner ----------
def run_debate(topic, style_key, style_desc, rounds, provider, api_key, model,
                prompts, modes_selected, pause_s,
                stage_container, transcript_container, verdict_container):
    transcript = []
    for _rnd in range(1, rounds + 1):
        for key, persona_key in ORDER:
            name = SEAT_INFO[key]["name"]
            emoji = SEAT_INFO[key]["emoji"]

            # anticipation frame — glow + "is thinking…" caption
            with stage_container.container():
                components.html(
                    render_stage_html(speaking_key=key, thinking=True),
                    height=STAGE_HEIGHT, scrolling=False,
                )

            user_prompt = build_user_prompt(topic, style_key, style_desc, name, transcript)
            sys_prompt = full_system_prompt(persona_key, prompts, modes_selected)
            try:
                reply = call_model(provider, api_key, model, persona_key, sys_prompt, user_prompt, transcript)
            except Exception as e:
                reply = f"(⚠️ {name} is speechless — API error: {e})"

            transcript.append({"key": key, "speaker": name, "emoji": emoji, "text": reply})

            # spoken frame — caption flies in from this seat's direction + a random crowd reaction
            reaction = random.choice(BOO_REACTIONS + CHEER_REACTIONS)
            with stage_container.container():
                components.html(
                    render_stage_html(speaking_key=key, caption_text=reply, reactions=[reaction]),
                    height=STAGE_HEIGHT, scrolling=False,
                )
            with transcript_container.container():
                st.markdown(render_transcript_html(transcript), unsafe_allow_html=True)
            time.sleep(pause_s)

    # Judge verdict
    with stage_container.container():
        components.html(
            render_stage_html(speaking_key="judge", thinking=True),
            height=STAGE_HEIGHT, scrolling=False,
        )

    verdict_prompt = build_verdict_prompt(topic, style_key, style_desc, transcript)
    sys_prompt_judge = full_system_prompt("judge", prompts, modes_selected)
    try:
        verdict = call_model(provider, api_key, model, "judge", sys_prompt_judge, verdict_prompt, transcript)
    except Exception as e:
        verdict = f"(⚠️ The Judge is speechless — API error: {e})"

    with verdict_container.container():
        st.markdown(render_verdict_html(verdict), unsafe_allow_html=True)
    with stage_container.container():
        components.html(
            render_stage_html(speaking_key="judge", caption_text=verdict, reactions=random.sample(JUDGE_REACTIONS, k=2)),
            height=STAGE_HEIGHT, scrolling=False,
        )

    return transcript, verdict


# ---------- Sidebar: backend + personas ----------
with st.sidebar:
    st.markdown("### 🔌 Backend")
    provider = st.selectbox("Provider", ["Gemini", "Groq", "Dry Run (no key needed)"], index=0)
    api_key = ""
    if provider == "Groq":
        api_key = st.text_input("Groq API key", value=DEFAULT_GROQ_API_KEY, type="password")
        model = st.selectbox("Model", GROQ_MODELS, index=GROQ_MODELS.index(DEFAULT_GROQ_MODEL))
        if model == "llama-3.3-70b-versatile":
            st.caption("⚠️ Groq retired this model on 2026-08-16 — it will likely 404.")
    elif provider == "Gemini":
        api_key = st.text_input("Gemini API key", value=DEFAULT_GEMINI_API_KEY, type="password")
        model = st.selectbox("Model", GEMINI_MODELS, index=GEMINI_MODELS.index(DEFAULT_GEMINI_MODEL))
    else:
        model = "dry-run"
        st.caption("Runs with canned responses so you can test the flow without spending API calls.")

    pause_s = st.slider("Pause between turns (s)", 7.0, 10.0, 7.0, 0.5)

    st.markdown("### 🗣️ Personas")
    prompts = {}
    modes_selected = {}
    with st.expander("Edit personas & delivery style", expanded=False):
        for key, label in PERSONA_LABELS:
            st.markdown(f"**{label}**")
            modes_selected[key] = st.selectbox(
                f"{label} style", list(ALL_MODES[key].keys()), index=0, key=f"mode_{key}"
            )
            prompts[key] = st.text_area(
                f"{label} base prompt", DEFAULT_PROMPTS[key], height=90, key=f"prompt_{key}"
            )

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Multi-Agent Arena</div>
  <h1>AI Debate Stage</h1>
  <div class="subtitle">Five distinct minds. One proposition. One judge.</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="topic-label">The proposition</div>', unsafe_allow_html=True)
topic = st.text_input(
    "Topic",
    placeholder="e.g. Should artificial intelligence be open source?",
    label_visibility="collapsed",
)

styles = {
    "Oxford": "Formal, structured, evidence-led arguments with rebuttals.",
    "Socratic": "Questions assumptions and exposes contradictions through questioning.",
    "Academic": "Careful claims, definitions, evidence, caveats, and counterarguments.",
    "Hostile": "Aggressive cross-examination and relentless attacks on weak reasoning.",
    "Casual": "Conversational, witty, accessible arguments without sacrificing substance.",
}
c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
with c1:
    style = st.selectbox("Debate style", list(styles.keys()))
with c2:
    rounds = st.selectbox("Rounds", [1, 2, 3, 4, 5], index=2)
with c3:
    st.markdown(
        f'<div style="color:#8e93a4;font-size:.78rem;padding-top:1.85rem">'
        f'<b style="color:#c9cbd4">{style}</b> — {styles[style]}</div>',
        unsafe_allow_html=True,
    )

# ---------- Stage placeholder ----------
stage_container = st.empty()
with stage_container.container():
    components.html(render_stage_html(speaking_key=None), height=STAGE_HEIGHT, scrolling=False)

# ---------- Start / status ----------
st.markdown("---")
left, mid, right = st.columns([1.15, 1.2, 3.65])

with left:
    start_clicked = st.button("▶  Start Debate", type="primary", use_container_width=True)

with mid:
    reset_clicked = st.button("↻  Reset Stage", use_container_width=True)

with right:
    status_slot = st.empty()
    if st.session_state.get("started"):
        status_slot.success(
            f"**IN SESSION** · {st.session_state['debate_topic']} · "
            f"{style} · {rounds} round(s)"
        )
    else:
        status_slot.caption("Enter a proposition, pick a provider in the sidebar, and start the chamber.")

# ---------- Transcript + verdict placeholders ----------
st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
st.markdown("##### 📜 Live Transcript")
transcript_container = st.empty()
with transcript_container.container():
    st.markdown(render_transcript_html(st.session_state.get("transcript", [])), unsafe_allow_html=True)

verdict_container = st.empty()
with verdict_container.container():
    st.markdown(render_verdict_html(st.session_state.get("verdict")), unsafe_allow_html=True)

st.markdown("""
<div style="height:18px"></div>
<div style="text-align:center;color:#555a69;font-size:.63rem;letter-spacing:.08em">
  NEXT: MID-DEBATE INTERRUPTS · CROWD METER · REPLAY MODE
</div>
""", unsafe_allow_html=True)

# ---------- Button logic (containers above already exist, so this can run last) ----------
if reset_clicked:
    for key in ["started", "debate_topic", "speaker", "transcript", "verdict"]:
        st.session_state.pop(key, None)
    st.rerun()

if start_clicked:
    if not topic.strip():
        status_slot.warning("Enter a proposition first.")
    elif provider != "Dry Run (no key needed)" and not api_key.strip():
        status_slot.error(f"Enter your {provider} API key in the sidebar, or switch to Dry Run.")
    else:
        st.session_state["started"] = True
        st.session_state["debate_topic"] = topic
        status_slot.success(f"**IN SESSION** · {topic} · {style} · {rounds} round(s)")
        transcript, verdict = run_debate(
            topic, style, styles[style], rounds,
            provider, api_key, model, prompts, modes_selected, pause_s,
            stage_container, transcript_container, verdict_container,
        )
        st.session_state["transcript"] = transcript
        st.session_state["verdict"] = verdict
