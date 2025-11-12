import uvicorn

if __name__ == "__main__":
    uvicorn.run(app="app.app:app", port=4000, reload=True)
