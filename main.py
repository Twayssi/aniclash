from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from jwt.exceptions import InvalidTokenError

from database import Base, engine, get_db
from schemas import UserCreate
from security import hash_password, verify_password, encode_token, decode_token
from services import search_anime, get_popular_anime, search_anime_by_id

import models

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

Base.metadata.create_all(bind=engine)

@app.get('/')
def welcome():
    return HTMLResponse('welcome')


@app.post('/register')
def register(user: UserCreate, db: Session = Depends(get_db)):
    user_table = models.User(username=user.username,
                             hashed_password=hash_password(user.password),
                             email=user.email)

    existing_username = db.query(models.User).filter(models.User.username == user_table.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail='Указанный никнейм уже используется.')
    
    existing_mail = db.query(models.User).filter(models.User.email == user_table.email).first()
    if existing_mail:
        raise HTTPException(status_code=400, detail='Указанный адрес электронной почты уже используется.')

    db.add(user_table)
    db.commit()
    db.refresh(user_table)
    user_token = encode_token(user_id=user_table.id, username=user_table.username)
    return {'access_token': user_token, 'token_type': 'bearer'}


@app.post('/login')
def login(user_form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if '@' in user_form.username:
        user_entry = db.query(models.User).filter(models.User.email == user_form.username).first()
    else:
        user_entry = db.query(models.User).filter(models.User.username == user_form.username).first()
    if not user_entry:
        raise HTTPException(status_code=403, detail='Пользователь с указанным никнеймом/ эл. почтой не найден')

    if verify_password(user_entry.hashed_password, user_form.password):
        token = encode_token(user_id=user_entry.id, username=user_entry.username)
        return {'access_token': token, 'token_type': 'bearer'}
    else:
        raise HTTPException(status_code=401, detail='Неверный пароль.')


@app.get('/me')
def me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail='Неверный или просроченный токен.')
    user_entry = db.query(models.User).filter(models.User.id == int(payload['sub'])).first()
    if user_entry is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    return {'id': user_entry.id, 'username': user_entry.username, 'email': user_entry.email, 'created_at': user_entry.created_at}


@app.get('/api/anime/search')
def get_anime_by_q(q: str, page: int = 1):
    response = search_anime(query=q, page=page)
    if 'errors' in response:
        raise HTTPException(status_code=404, detail='Ошибка запроса')
    return response


@app.get('/api/anime/popular')
def get_popular(page: int = 1):
    response = get_popular_anime(page=page)
    if 'errors' in response:
        raise HTTPException(status_code=404, detail='Ошибка запроса')
    return response


@app.get('/api/anime/{anime_id}')
def get_anime_by_id(anime_id: int):
    response = search_anime_by_id(anime_id)
    if 'errors' in response:
        raise HTTPException(status_code=404, detail='Ошибка запроса')
    return response

@app.get('/health')
def health():
    return {'status': 'ok'}