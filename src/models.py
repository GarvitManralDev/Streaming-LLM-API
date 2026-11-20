from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Data sent by the client.
    """

    # User message cannot be empty.
    message: str = Field(
        min_length=1,
        max_length=2000
    )

    # Keep temperature in a safe demo range.
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2
    )



class ChatResponse(BaseModel):
    """
    Normal non-streaming response.
    """

    answer: str
    model: str
    cached: bool = False
