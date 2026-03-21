import json
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = (
    "You are an expert luxury wedding theme designer. "
    "You MUST respond with ONLY a valid JSON object — no markdown, no code blocks, "
    "no backticks, no explanatory text. Your entire response must start with { and end with }."
)


def generate_wedding_theme(
    partner1_name,
    partner2_name,
    wedding_date,
    location,
    venue_name,
    style,
    primary_color,
    secondary_color,
):
    """Call Gemini to generate a wedding theme and return a parsed dict, or None on failure."""
    user_prompt = f"""Wedding theme for {partner1_name} & {partner2_name}.
Venue: {venue_name}, {location}. Date: {wedding_date}. Style: {style}. Colours: {primary_color}, {secondary_color}.

JSON fields required:
- tagline: short romantic one-liner for this couple
- color_palette: array of 5 objects {{name, hex, role}} — real CSS hex inspired by the given colours; roles: Primary/Secondary/Accent/Neutral/Highlight
- font_suggestions: array of 3 objects {{heading, body, description}} — real Google Font names, one sentence why it suits {style}
- invitation_text: formal wording for {partner1_name} & {partner2_name} at {venue_name} on {wedding_date}, \\n between sections
- style_keywords: array of 5 strings
- decor_suggestions: array of 4 strings specific to {venue_name} and {style}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        # Strip accidental markdown code fences if present
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
        print(f"[ai_service] generate_wedding_theme failed: {e}")
        return None
