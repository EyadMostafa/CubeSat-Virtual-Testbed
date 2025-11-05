from fastapi import FastAPI
from cvt.config.config import config

app = FastAPI()

@app.get('/status')
async def test():
    return config

