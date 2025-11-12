from fastapi import FastAPI, Request
from app.utils.responses import APIError, APIResponse

app = FastAPI()

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return exc.to_response()

@app.get('/')
def root():
    return {"message":"Hello world"}


@app.get("/success")
def success_example():
    response = APIResponse(
        status_code=200,
        data={"user": {"id": 1, "name": "Gurpreet"}},
        message="User fetched successfully"
    )
    return response.to_response()

@app.get("/error")
def error_example():
    raise APIError(
        status_code=404,
        message="User not found",
        errors=["User with given ID does not exist"]
    )