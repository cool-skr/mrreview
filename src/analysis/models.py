from pydantic import BaseModel, Field
from typing import Literal

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

class Issue(BaseModel):
    """
    A Pydantic model representing a single code quality issue.
    """
    file_path: str
    line_number: int
    column_number: int
    code: str = Field(..., description="A short code for the issue type, e.g., 'complexity'")
    message: str = Field(..., description="A developer-friendly message explaining the issue.")
    severity: Severity

    class Config:
        use_enum_values = True