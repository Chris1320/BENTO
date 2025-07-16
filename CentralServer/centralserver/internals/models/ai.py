from typing import Optional
from pydantic import BaseModel, Field


class AIInsightsRequest(BaseModel):
    """Request model for AI insights generation."""

    school_id: Optional[int] = Field(
        None, description="Specific school ID (for admins)"
    )
    year: Optional[int] = Field(None, description="Year for analysis")
    month: Optional[int] = Field(None, description="Month for analysis")


class AIInsightsResponse(BaseModel):
    """Response model for AI insights."""

    insights: str = Field(..., description="Generated insights text (max 50 words)")
    school_name: str = Field(..., description="Name of the school")
    period: str = Field(..., description="Period analyzed (e.g., 'January 2025')")


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat interaction."""

    message: str = Field(..., description="User message")
    school_id: Optional[int] = Field(
        None, description="Specific school ID (for admins)"
    )
    conversation_history: list[ChatMessage] = Field(
        default=[], description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    """Response model for chat interaction."""

    response: str = Field(..., description="AI assistant response")
    school_name: str = Field(..., description="Name of the school context")
