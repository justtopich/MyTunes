from pydantic import BaseModel, Field


class CoverSettings(BaseModel):
    convert: bool
    jpegNext: bool
    quality: int = Field(int, ge=1, le=100)
