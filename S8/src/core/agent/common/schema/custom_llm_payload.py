from pydantic import BaseModel, Field

class CustomPayload(BaseModel):
    prompt: str = Field(default="")
    max_tokens: int = Field(default=100)
    temperature: float = Field(default=0.3)
    provider: str = Field(default="bedrock")
    top_p: float = Field(default=0.95)
    domain: str = Field(default="general")
    addition_system_prompt: str = Field(default="")