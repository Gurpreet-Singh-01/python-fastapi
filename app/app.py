from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, Depends
from fastapi.exceptions import RequestValidationError
from app.utils.responses import APIError, APIResponse
from app.schema import PostCreate
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get('/')
def root():
    return {"message": "Hello world"}


@app.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    post = Post(
        caption=caption,
        url="dummy_url",
        file_type="photo",
        file_name="dummy file"
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)
    return APIResponse(data=[post.to_dict()], message="Post Created Successfully",  status_code=201).to_response()


@app.get('/feed')
async def get_feed(
    db: AsyncSession = Depends(get_async_session)
) -> APIResponse:
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    post_data = []

    for post in posts:
        post_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat()
            }
        )
    return APIResponse(data=post_data, message="Post Fetched Successfully", status_code=200).to_response()
