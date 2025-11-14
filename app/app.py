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
import shutil
import os
import uuid
import tempfile


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

    temp_file_path = None
    upload_result = None

    try:
        suffix = os.path.splitext(file.filename)[1] or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name

            shutil.copyfileobj(file.file, temp_file)

        with open(temp_file_path, 'rb') as f:
            upload_result = imagekit.upload_file(
                file=f,
                file_name=file.filename,
                options=UploadFileRequestOptions(
                    use_unique_file_name=True,
                    tags=["Backend-upload"]
                )
            )

        status_code = None

        try:
            status_code = getattr(
                upload_result.response_metadata, "http_status_code", None)
        except Exception:
            status_code = None

        if status_code == 200 or status_code == 201 or (hasattr(upload_result, "url") and upload_result.url):
            post = Post(
                caption=caption,
                url=upload_result.url,
                file_type="video" if file.content_type.startswith(
                    "video/") else "image",
                file_name=upload_result.name if hasattr(
                    upload_result, "name") else file.filename
            )
            db.add(post)
            await db.commit()
            await db.refresh(post)
            return APIResponse(data=[post.to_dict()], message="Post Created Successfully",  status_code=201).to_response()

        raise APIError(
                status_code=500,
                message="Failed uploading to imagekit",
                errors=[f"imagekit status: {status_code}", getattr(upload_result, "response_metadata", None)]
            )

    
    except APIError:
        # re-raise APIError so your exception handler deals with it
        raise


    except Exception as e:
        raise APIError(
            status_code=500,
            message="Failed uploading image",
            errors=[str(e)]
        )

    
    finally:
        # Safely remove temporary file if it exists
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception:
            # don't let cleanup errors mask the original exception
            pass
        # ensure the UploadFile's internal file is closed
        try:
            file.file.close()
        except Exception:
            pass


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


@app.delete('/post/{post_id}')
async def delete_post(post_id:str, session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    try:
        post_uuid = uuid.UUID(post_id)
        result  = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()
        
        if not post:
            raise APIError(message="Post not found", data=None, status_code=404)
        await session.delete(post)
        await session.commit()
        return APIResponse(data={}, message="Post deleted successfully",status_code=200 ).to_response()
    except Exception as e:
        print(e)
        raise APIError(message=str(e))
        