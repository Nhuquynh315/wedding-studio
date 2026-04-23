import json
import os

from google import genai
from google.genai import types


def _repair_json(text):
    """Strip code fences and escape bare newlines inside JSON string literals."""
    # Strip markdown code fences
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    # Walk the text and escape bare newlines/carriage returns inside strings
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == '\\':
            result.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\r':
            result.append('\\r')
        else:
            result.append(ch)
    return ''.join(result)

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

_WORDING_GUIDANCE = {
    'Romantic':  'Warm and tender — classic structure but with a loving, heartfelt feel. Example: "joyfully invite you to share in their love\\nas they begin their journey together"',
    'Formal':    'Traditional and dignified — classic printed-invitation phrasing. Example: "request the honour of your presence\\nat the celebration of their marriage"',
    'Playful':   'Warm and fun — still invitation-appropriate but friendly and upbeat. Example: "can\'t wait to celebrate with you\\nas they tie the knot!"',
    'Poetic':    'Lyrical and evocative — may use imagery or gentle metaphor, 2-3 lines. Example: "where two rivers meet the sea\\nthey ask you to witness their becoming one"',
    'Simple':    'Clear and minimal — short, direct, no embellishment. Example: "invite you to their wedding ceremony"',
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
    wording_guidance = _WORDING_GUIDANCE.get(tone, _WORDING_GUIDANCE['Formal'])
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
"""

    client = genai.Client(api_key=api_key)
    cfg = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
    )

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=cfg,
            )
            text = _repair_json(response.text.strip())
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[ai_service] JSON parse error (attempt {attempt + 1}): {e}")
            print(f"[ai_service] Raw response: {response.text[:300]!r}")
        except Exception as e:
            status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
            if status in (401, 403):
                print(f"[ai_service] invalid or unauthorised API key: {e}")
                return None
            print(f"[ai_service] generate_wedding_theme failed (attempt {attempt + 1}): {e}")

    return None
