from typing import Any, Optional, List
from pydantic import BaseModel
from fastapi.responses import JSONResponse


class APIResponse(BaseModel):
    status_code: int
    data: Optional[Any] = None
    message: str = "Success"
    success: bool = True

    def to_response(self):
        # Converting API objet to fastAPI json response

        return JSONResponse(
            status_code=self.status_code,
            content={
                "success": self.success,
                "message": self.message,
                "data": self.data
            }
        )


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str = "Something went wrong",
        errors: Optional[List[Any]] = None,
        stack: Optional[str] = None,
    ):
        self.status_code = status_code
        self.success = False
        self.data = None
        self.message = message
        self.errors = errors or []
        self.stack = stack
        super().__init__(message)

    def to_response(self):

        # Converts the APIError into a FastAPI JSONResponse.
        return JSONResponse(
            status_code=self.status_code,
            content={
                "success": False,
                "message": self.message,
                "data": None,
                "errors":self.errors
            },
        )
