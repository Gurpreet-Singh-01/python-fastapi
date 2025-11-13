from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from app.utils.responses import APIError, APIResponse
from app.schema import PostCreate
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return exc.to_response()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    validation_errors = exc.errors()  

    custom_error = APIError(
        status_code=422,
        message="Validation failed",
        errors=validation_errors  # directly include Pydantic details here
    )
    return custom_error.to_response()
text_posts = {
    1: {"title": "Post 1", "content": "This is the content of post 1."},
    2: {"title": "Post 2", "content": "Exploring how FastAPI handles requests."},
    3: {"title": "Post 3", "content": "Understanding custom exceptions in Python."},
    4: {"title": "Post 4", "content": "Building REST APIs with FastAPI."},
    5: {"title": "Post 5", "content": "Implementing global error handlers."},
    6: {"title": "Post 6", "content": "How to structure FastAPI projects effectively."},
    7: {"title": "Post 7", "content": "Working with Pydantic models and validation."},
    8: {"title": "Post 8", "content": "Creating reusable API response formats."},
    9: {"title": "Post 9", "content": "Handling HTTP exceptions in a clean way."},
    10: {"title": "Post 10", "content": "Deploying FastAPI apps to production."}
}


@app.get('/')
def root():
    return {"message": "Hello world"}


@app.get('/post')
def get_all_posts(limit:int = None)-> APIResponse:
    posts_list = list(text_posts.values())
    if limit:
        if limit <= len(text_posts):
            return APIResponse(
            data=posts_list[:limit],
            message=f"{limit} posts fetched successfully",
            status_code=200,
            ).to_response()
        raise APIError(message="Limit exceed", status_code=405)
    
    return APIResponse(
            data=posts_list,
            message=f"Posts fetched successfully",
            status_code=200,
            ).to_response()

@app.get("/post/{id}")
def get_post_by_id(id: str)-> APIResponse:
    if id not in text_posts:
        raise APIError(message="id not found", status_code=404)

    return APIResponse(status_code=202, data=text_posts.get(id), message="Posts Fetched Successfully").to_response()


@app.post("/posts") 
def create_post(post: PostCreate) -> APIResponse:
    new_post= {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    
    return APIResponse(status_code=201, data=new_post, message="Post Created Successfully").to_response()