from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from src.config import settings

# Read the API key from:
#
# X-API-Key: course-secret
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)



def verify_api_key(
    api_key: str | None = Depends(api_key_header)
):
    """
    Very simple API-key authentication.
    """

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    return api_key
