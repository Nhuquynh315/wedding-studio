import json
import os

from google import genai
from google.genai import types

SYSTEM_PROMPT = (
    "You are an expert luxury wedding theme designer. "
    "You MUST respond with ONLY a valid JSON object — no markdown, no code blocks, "
    "no backticks, no explanatory text. Your entire response must start with { and end with }."
)

_TONE_DESCRIPTIONS = {
    'Romantic':  'romantic and heartfelt',
    'Formal':    'formal and sophisticated',
    'Playful':   'playful and lighthearted',
    'Poetic':    'poetic and lyrical',
    'Simple':    'simple, clean, and understated',
}


def generate_wedding_theme(
    partner1_name,
    partner2_name,
    wedding_date,
    location,
    venue_name,
    style,
    primary_color,
    secondary_color,
    tone='Romantic',
):
    """Call Gemini to generate a wedding theme and return a parsed dict, or None on failure."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ai_service] GEMINI_API_KEY is not set")
        return None

    tone_desc = _TONE_DESCRIPTIONS.get(tone, 'romantic and heartfelt')
    user_prompt = f"""Wedding theme for {partner1_name} & {partner2_name}.
Venue: {venue_name}, {location}. Date: {wedding_date}. Style: {style}. Colours: {primary_color}, {secondary_color}.
Tone: Use a {tone_desc} tone throughout all text fields.

JSON fields required:
- tagline: MAX 6 WORDS. A short evocative subtitle only — no full sentences. Example: "Where two hearts become one"
- color_palette: array of 5 objects with keys name, hex, role — real CSS hex inspired by the given colours; roles: Primary/Secondary/Accent/Neutral/Highlight
- font_suggestions: array of 3 objects with keys heading, body, description — real Google Font names, one sentence why it suits {style}
- invitation_text: EXACTLY 2-3 lines of CLASSIC, TRADITIONAL invitation wording. Rules: NO names, NO date, NO time, NO venue. NO flowery or poetic language — keep it simple and direct. Use \\n between lines. The wording must sound like a real printed wedding invitation, not a poem. Example: "request the honour of your presence\\nat the celebration of their marriage"
- ceremony_time: a ceremony time string in simple format, e.g. "5:00 PM" or "4:30 PM"
- style_keywords: array of 5 strings
- decor_suggestions: array of 4 strings specific to {venue_name} and {style}
- rsvp_info: a short string with only the RSVP deadline date. Example: "March 15, 2026"
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[ai_service] JSON parse error: {e}")
        return None
    except Exception as e:
        status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
        if status in (401, 403):
            print(f"[ai_service] invalid or unauthorised API key: {e}")
        else:
            print(f"[ai_service] generate_wedding_theme failed: {e}")
        return None
