from google import genai
from google.genai import types
from pydantic import ValidationError

from api.core.config import settings
from api.schemas.design import GeneratedTheme, Tone


class AIServiceError(Exception):
    """Base for AI failures the route should translate to HTTP errors."""


class AIServiceUnconfigured(AIServiceError):
    """No API key configured — AI features disabled."""


class AIServiceUnauthorized(AIServiceError):
    """401/403 from Gemini — bad or expired key."""


class AIServiceUnavailable(AIServiceError):
    """Upstream failure after retries."""


_SYSTEM_PROMPT = (
    "You are an expert luxury wedding theme designer. "
    "You MUST respond with ONLY a valid JSON object — no markdown, no code blocks, "
    "no backticks, no explanatory text. Your entire response must start with { and end with }."
)

_TONE_DESCRIPTIONS = {
    "Romantic": "romantic and heartfelt",
    "Formal": "formal and sophisticated",
    "Playful": "playful and lighthearted",
    "Poetic": "poetic and lyrical",
    "Simple": "simple, clean, and understated",
}

_WORDING_GUIDANCE = {
    "Romantic": 'Warm and tender — classic structure but with a loving, heartfelt feel. Example: "joyfully invite you to share in their love\\nas they begin their journey together"',
    "Formal": 'Traditional and dignified — classic printed-invitation phrasing. Example: "request the honour of your presence\\nat the celebration of their marriage"',
    "Playful": 'Warm and fun — still invitation-appropriate but friendly and upbeat. Example: "can\'t wait to celebrate with you\\nas they tie the knot!"',
    "Poetic": 'Lyrical and evocative — may use imagery or gentle metaphor, 2-3 lines. Example: "where two rivers meet the sea\\nthey ask you to witness their becoming one"',
    "Simple": 'Clear and minimal — short, direct, no embellishment. Example: "invite you to their wedding ceremony"',
}


def _repair_json(text: str) -> str:
    """Strip code fences and escape bare newlines inside JSON string literals."""
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == "\\":
            result.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == "\n":
            result.append("\\n")
        elif in_string and ch == "\r":
            result.append("\\r")
        else:
            result.append(ch)
    return "".join(result)


def generate_wedding_theme(
    partner1_name: str,
    partner2_name: str,
    wedding_date: str,
    location: str,
    venue_name: str,
    style: str,
    primary_color: str,
    secondary_color: str,
    tone: Tone = "Romantic",
) -> GeneratedTheme:
    """Return a parsed GeneratedTheme. Raises AIServiceError subclasses on failure."""
    if not settings.gemini_api_key:
        raise AIServiceUnconfigured("GEMINI_API_KEY not configured")

    tone_desc = _TONE_DESCRIPTIONS.get(tone, "romantic and heartfelt")
    wording_guidance = _WORDING_GUIDANCE.get(tone, _WORDING_GUIDANCE["Romantic"])

    user_prompt = f"""Wedding theme for {partner1_name} & {partner2_name}.
Venue: {venue_name}, {location}. Date: {wedding_date}. Style: {style}. Colours: {primary_color}, {secondary_color}.
Tone: Use a {tone_desc} tone throughout ALL text fields — tagline, invitation_text, decor_suggestions, style_keywords.

JSON fields required:
- tagline: MAX 6 WORDS. A short evocative subtitle matching the {tone} tone — no full sentences.
- color_palette: array of 5 objects with keys name, hex, role — real CSS hex inspired by the given colours; roles: Primary/Secondary/Accent/Neutral/Highlight
- font_suggestions: array of EXACTLY 3 objects with keys heading, body, description. Each must use a DIFFERENT font style category — one must use a script/calligraphy heading (e.g. Tangerine, Great Vibes, Pinyon Script), one must use a classic serif heading (e.g. Cormorant Garamond, Playfair Display, EB Garamond), one must use a modern sans-serif heading (e.g. Josefin Sans, Raleway, Montserrat). The 3 pairings must look visually DISTINCT from each other. Body fonts must be readable (Lato, Lora, Source Serif Pro, etc). One sentence description per pairing explaining why it suits {style} and {tone} tone.
- invitation_text: 2-3 lines of invitation wording matching the {tone} tone. NO names, NO date, NO time, NO venue. Use \\n between lines. Guidance for {tone} tone: {wording_guidance}
- ceremony_time: a ceremony time string in simple format, e.g. "5:00 PM" or "4:30 PM"
- style_keywords: array of 5 strings that reflect both {style} style and {tone} tone
- decor_suggestions: array of 4 strings specific to {venue_name} and {style}, written in a {tone_desc} tone
- rsvp_info: a short string with only the RSVP deadline date. Example: "March 15, 2026"
- layout: ONE of "classic", "modern", "romantic". Pick the layout that best matches the {style} and {tone}:
    - "classic" = serif, centered, formal — best for traditional / formal styles
    - "modern" = sans-serif, asymmetric, minimal — best for contemporary / minimalist styles
    - "romantic" = script-heavy, ornate, decorative — best for garden / bohemian / fairytale styles
"""

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=GeneratedTheme,
    )

    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=config,
            )
            if getattr(response, "parsed", None) is not None:
                return response.parsed
            text = _repair_json(response.text.strip())
            return GeneratedTheme.model_validate_json(text)
        except (ValidationError, ValueError) as e:
            last_error = e
        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            msg = str(e)
            # Bad API key: Gemini returns 400 INVALID_ARGUMENT, not 401/403.
            if status in (401, 403) or "API_KEY_INVALID" in msg or "API key not valid" in msg:
                raise AIServiceUnauthorized(str(e)) from e
            last_error = e

    raise AIServiceUnavailable(f"Gemini failed after 2 attempts: {last_error}") from last_error
