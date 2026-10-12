from fastapi import FastAPI
from fastapi.responses import HTMLResponse 
from database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get('/')
def welcome():
    return HTMLResponse('welcome')

@app.get('/health')
def health():
    return {'status': 'ok'}