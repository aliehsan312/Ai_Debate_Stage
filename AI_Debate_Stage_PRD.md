# Product Requirements Document

## AI Debate Stage — A Multi-Model Prompt Engineering Sandbox

**Program:** PakAngel's GenAI & AgenticAI | Cohort 11 | Hackathon

---

## 1. Problem & Context

Prompt engineering is usually taught the same way in every cohort: read a
guideline, paste a prompt into a single-turn playground, read the output,
repeat. That workflow has three specific gaps for a hackathon-stage learner:

1. **No visible comparison surface.** OpenAI's Playground, Google AI Studio,
   and the Groq console each let you test one prompt against one model in
   isolation. Nothing lets a learner run the *same* scenario across two
   providers back-to-back and see the divergence in tone, length compliance,
   or reasoning quality.
2. **No multi-turn, multi-persona pressure test.** Most playgrounds are
   single system prompt → single reply. They don't reveal how a model holds
   a persona under pressure across many turns, or how it behaves once its
   own prior output becomes part of the context it has to react to —
   exactly the situation production agentic systems live in.
3. **Low engagement, low retention.** A blank text box is a poor teaching
   surface. Cohort participants forget playground experiments quickly
   because nothing about the format is memorable or shareable.

**Who feels this:** primarily PakAngel Cohort 11 participants who are
learning system-prompt design, persona construction, and cross-provider
model selection, and more broadly any developer who wants a fast, visual
way to A/B system prompts without standing up their own harness.

**Why existing solutions fall short:** they optimize for correctness
testing of a single call, not for *comparative, iterative, multi-agent*
experimentation — which is the actual skill the cohort is being trained on.

**The angle this PRD takes:** the "AI Debate Stage" is not, at its core, a
comedy app. The comedic debate format is the *engagement wrapper* around
what is functionally a sandbox for:

- Switching the underlying model (Groq ⇄ Gemini) mid-session and observing
  behavioral differences on an identical scenario.
- Live-editing five distinct system prompts and instantly re-running to see
  the effect — the fastest possible prompt-iteration loop available in a
  no-code UI.
- Testing delivery-style overlays (e.g., "make the Skeptic speak like a
  film-noir detective") as a hands-on lesson in prompt composition —
  base persona + stylistic instruction layered together.
- Watching context-chaining in action: every turn's request is provably
  built from the full prior transcript, making "the model sees what was
  said before" a visible, not theoretical, concept.

---

## 2. Scope & Non-Goals

### In scope for V1
- Streamlit web app, single active session, no login required.
- Five-persona debate structure (Analyst, Advocate, Skeptic, Contrarian,
  Judge) with independently editable system prompts.
- Pluggable model backend: **Groq**, **Gemini**, and a **Dry Run** mode that
  requires no key or network access, for testing UI/flow.
- Per-persona **delivery-style overlay** dropdown (curated presets, e.g.
  Pirate, Shakespearean, Gen Z, Film Noir Detective), each with a sensible
  default.
- Configurable debate style (Oxford, Socratic, Academic, Hostile, Casual),
  round count (1–5), and turn pacing (7–10s).
- Full-transcript context chaining: each debater's prompt is built from
  every prior turn, not just the immediately preceding one.
- On-stage animated captions per turn, ambient "physical comedy" stage
  visuals, and a plain-text Live Transcript panel.
- Inline, actionable error handling (bad model ID, missing key, failed
  call) that never crashes the running debate.

### Explicit non-goals for V1
- **No accounts, no persistence.** Nothing is saved server-side between
  sessions; transcripts live only in Streamlit session state.
- **No other providers.** OpenAI, Anthropic, or local/self-hosted models
  are out of scope until a V2 decision is made.
- **No token-by-token streaming.** Replies render whole, once complete.
- **No automated model-quality scoring.** The tool surfaces outputs
  side-by-side for a human to judge; it does not compute win-rates or
  benchmark scores.
- **No production-grade moderation pipeline.** Safety is enforced at the
  prompt-instruction level only (see Guardrails below), not via a
  separate classifier layer.
- **No mobile app or voice/audio output.**
- **No monetization or multi-tenant hosting concerns** — this is a
  hackathon-scale, single-user-at-a-time sandbox.

---

## 3. Functional & AI Requirements

### User inputs
| Input | Where | Notes |
|---|---|---|
| Debate topic | Main panel, free text | Required to start |
| Debate style | Dropdown (5 presets) | Shapes tone via prompt injection |
| Round count | Dropdown, 1–5 | Each round = all 4 debaters speak once |
| Provider | Sidebar dropdown | Gemini (default) / Groq / Dry Run |
| API key | Sidebar, password field | Session-only; optional hardcoded default constants for local use |
| Model | Sidebar dropdown, provider-specific | Curated, user-editable list (see Risks — model IDs deprecate) |
| Per-persona system prompt | Sidebar expander, 5 text areas | Live-editable, takes effect on next debate run |
| Per-persona delivery style | Sidebar dropdown, 5 selectors | Curated per role, "Default" pre-selected |
| Turn pacing | Sidebar slider, 7–10s | Controls perceived pacing and API load |

### Expected outputs
- Sequential animated stage captions, one per turn, visually attributed to
  the speaking persona.
- A full plain-text transcript, updated live.
- A closing Judge verdict, generated only after all rounds complete, using
  the entire transcript as context.
- Ambient audience reaction cues (visual only, non-blocking).

### Model / prompt-chaining requirement
Every debater's request **must** be built from `topic + style + full prior
transcript`, not just the last line — this is the core "agentic memory"
lesson the sandbox is meant to demonstrate. The Judge's verdict prompt uses
the complete transcript across all rounds.

### AI guardrails
- Persona lock: each debater's stance (FOR / AGAINST / wildcard) is fixed
  in its base prompt and must not be overridden by style overlays.
- Reply length is bounded (2–3 sentences for debaters, 3–4 for the Judge)
  to control latency, cost, and comedic pacing.
- Every base prompt explicitly forbids slurs, hate speech, and breaking
  character to mention being an AI — a floor requirement even when the
  "meaner, more personal" tone is intentionally dialed up.
- Model output is HTML-escaped before rendering, so a model reply can never
  inject markup into the page.

### Error handling
- Missing API key blocks the debate start with an inline, specific message;
  Dry Run remains available as a zero-friction fallback at all times.
- Each model call is wrapped individually — a single failed turn renders as
  an in-character "is speechless" line rather than halting the whole
  debate.
- A 404 response is caught and re-raised with a targeted hint ("model id is
  likely wrong or deprecated") rather than a raw stack trace, since model
  ID churn (see Risks) is the most common real-world failure mode observed
  during build.

---

## 4. Impact Metrics

Because this is framed as a **learning and comparison sandbox** rather than
a production tool, success is measured on engagement-with-the-mechanism,
not on debate "quality":

**Prompt-engineering engagement**
- Number of system-prompt edits made per session (proxy for iteration).
- Number of delivery-style-overlay changes per session.
- % of sessions that run ≥2 providers on the same topic (direct signal the
  comparison use case is being exercised, not just the entertainment one).

**Cohort / hackathon outcomes**
- Successful live demo without falling back to Dry Run.
- Number of Cohort 11 peers who run the app with their own key after the
  demo (organic reuse signal).
- Qualitative mentor/judge feedback on originality of the teaching
  mechanism for prompt-engineering concepts (system prompts, persona
  design, context chaining, model comparison).

**Technical reliability**
- Turn-level error rate (failed calls ÷ total calls).
- Average latency per turn, per provider.
- Estimated cost per full debate run, per provider/model combination.

---

## 5. Risks & Open Questions

- **Model ID churn.** Already observed during build: Groq deprecated
  `llama-3.3-70b-versatile` mid-project. Mitigation: model IDs live in an
  editable dropdown, not hardcoded, and 404s surface a specific hint.
- **Distastefulness risk.** The "meaner, personalized" debate tone is
  enforced only via prompt instruction, not a moderation layer — acceptable
  for a hackathon demo, not for a public deployment.
- **Latency stacking.** Sequential (non-parallel) calls plus mandatory 7–10s
  pacing mean a 5-round debate takes several minutes; acceptable for a demo,
  worth revisiting if usage grows.
- **Open question:** should V2 add a structured side-by-side comparison
  view (same prompt, two providers, two columns) to make the "sandbox"
  framing more explicit than the current single-stream format allows?
