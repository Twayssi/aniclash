from fastapi import FastAPI
from fastapi.responses import HTMLResponse 


app = FastAPI()

@app.get('/')
def welcome():
    return HTMLResponse('welcome')

@app.get('/health')
def health():
    return {'status': 'ok'}