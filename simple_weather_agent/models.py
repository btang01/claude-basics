from pydantic import BaseModel, Field

class CityInput(BaseModel):
    city: str = Field(..., description="City name for weather lookup")

class ProfileInput(BaseModel):
    profile: str = Field(..., description="User profile (e.g., 'brian')")