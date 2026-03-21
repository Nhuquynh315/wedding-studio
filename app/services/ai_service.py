import json
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert wedding theme designer with deep knowledge of aesthetics,
colour theory, typography, and event styling. When given details about a couple's wedding,
you craft a cohesive, personalised theme package and return it as valid JSON — nothing else."""


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
    user_prompt = f"""Generate a wedding theme for the following details:

- Couple: {partner1_name} & {partner2_name}
- Date: {wedding_date}
- Location: {location}
- Venue: {venue_name}
- Style: {style}
- Primary colour: {primary_color}
- Secondary colour: {secondary_color}

Return a JSON object with exactly these fields:
- color_palette: a description of 4–5 complementary colours that work with the primary and secondary colours
- font_suggestions: a list of 3 font pairing names (e.g. "Playfair Display + Lato")
- invitation_text: complete formal invitation wording for this couple
- tagline: a short romantic one-liner for the couple
- style_keywords: a list of 3–5 aesthetic keywords describing the theme
- decor_suggestions: a list of 3–4 specific decoration ideas suited to the venue and style"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[ai_service] generate_wedding_theme failed: {e}")
        return None
