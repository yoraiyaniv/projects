from pydantic import BaseModel, field_validator, ValidationInfo, Field
from typing import Optional


class UrlAssignmentInput(BaseModel):
    url: Optional[str] = Field(default=None)
    ttl: int = Field(default=86400, validate_default=True)
    
    @field_validator("ttl")
    def validate_url(cls, ttl, info: ValidationInfo):
        if info.data["url"] is None:
            raise ValueError("Url is not given in the request.")
        else:
            return ttl
        