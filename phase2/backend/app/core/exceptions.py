from fastapi import HTTPException, status

class APIException(HTTPException):
    """Base exception for API errors"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "API_ERROR"
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class AuthenticationError(APIException):
    """Authentication failed"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTH_001"
        )

class AuthorizationError(APIException):
    """Insufficient permissions"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTH_002"
        )

class ResourceNotFoundError(APIException):
    """Resource not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RES_001"
        )

class ValidationError(APIException):
    """Validation error"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VAL_001"
        )

class DatabaseError(APIException):
    """Database error"""
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="DB_001"
        )
