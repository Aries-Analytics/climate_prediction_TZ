from pydantic import BaseModel
from typing import Optional, List, Any

class ErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    errors: Optional[List[ErrorDetail]] = None

class ValidationErrorResponse(BaseModel):
    detail: List[ErrorDetail]
