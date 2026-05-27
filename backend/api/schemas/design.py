from typing import Literal

from pydantic import BaseModel, Field

Tone = Literal["Romantic", "Formal", "Playful", "Poetic", "Simple"]
Layout = Literal["classic", "modern", "romantic"]


class ColorEntry(BaseModel):
    name: str
    hex: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    role: Literal["Primary", "Secondary", "Accent", "Neutral", "Highlight"]


class FontPairing(BaseModel):
    heading: str
    body: str
    description: str


class GeneratedTheme(BaseModel):
    """The structured output Gemini returns for an invitation."""

    tagline: str = Field(max_length=80)
    color_palette: list[ColorEntry] = Field(min_length=5, max_length=5)
    font_suggestions: list[FontPairing] = Field(min_length=3, max_length=3)
    invitation_text: str
    ceremony_time: str
    style_keywords: list[str] = Field(min_length=5, max_length=5)
    decor_suggestions: list[str] = Field(min_length=4, max_length=4)
    rsvp_info: str
    layout: Layout = "classic"


class GenerateDesignRequest(BaseModel):
    partner1_name: str = Field(min_length=1, max_length=100)
    partner2_name: str = Field(min_length=1, max_length=100)
    wedding_date: str
    location: str = Field(min_length=1, max_length=200)
    venue_name: str = Field(min_length=1, max_length=200)
    style: str = Field(min_length=1, max_length=100)
    primary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    tone: Tone = "Romantic"


class DesignPublic(BaseModel):
    id: int
    wedding_id: int
    design_type: str
    theme: GeneratedTheme
    created_at: str

    model_config = {"from_attributes": True}
