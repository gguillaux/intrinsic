import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:server", host="0.0.0.0", port=8050, reload=True)
