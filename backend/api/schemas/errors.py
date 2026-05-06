from pydantic import BaseModel, ConfigDict, Field


class ProblemDetails(BaseModel):
    """RFC 7807 'application/problem+json' envelope.

    https://datatracker.ietf.org/doc/html/rfc7807
    """

    model_config = ConfigDict(extra="allow")

    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
