from fastapi import FastAPI

app = FastAPI(title="EquiCart Backend")


@app.get("/")
async def root():
    return {"message": "EquiCart Backend Running"}
