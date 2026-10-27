from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from jwt.exceptions import InvalidTokenError

import datetime
import secrets
import json
import random

from database import Base, engine, get_db
from schemas import UserCreate, RoomCreate
from security import hash_password, verify_password, encode_token, decode_token
from services import search_anime, get_popular_anime, search_anime_by_id
from redis_client import client

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


@app.post('/api/rooms')
def create_room(room_data: RoomCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        host_id = payload['sub']
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail='Неверный или просроченный токен')
    room_id = secrets.token_urlsafe(6)
    room_created_at = datetime.datetime.now().isoformat()
    room_dict = {   
        'room_id': room_id,
        'host_id': int(host_id),
        'room_name': room_data.room_name,
        'created_at': room_created_at,
        'members': [int(host_id)],
        'current_event': None
    }
    room_json = json.dumps(room_dict)
    client.set(name=f'room:{room_id}', ex=86400, value=room_json)
    return room_dict


@app.post('/api/rooms/{room_id}/join')
def join_room(room_id: str, token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        user_id = int(payload['sub'])
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail='Неверный или просроченный токен')
    room_data = client.get(f'room:{room_id}')
    if room_data is None:
        raise HTTPException(status_code=404, detail='Комната не найдена')
    room_dict = json.loads(room_data)
    if user_id not in room_dict['members']:
        room_dict['members'].append(user_id)
    room_json= json.dumps(room_dict)
    client.set(name=f'room:{room_id}', ex=86400, value=room_json)
    return room_dict['members']


@app.get('/api/rooms/{room_id}/info')
def get_info(room_id: str):
    room_data = client.get(f'room:{room_id}')
    if room_data is None:
        raise HTTPException(status_code=404, detail='Комната не найдена')
    room_dict = json.loads(room_data)
    return room_dict
    

@app.delete('/api/rooms/{room_id}/leave')
def leave_room(room_id: str, token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        user_id = int(payload['sub'])
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail='Неверный или просроченный токен')
    room_data = client.get(f'room:{room_id}')
    if not room_data:
        raise HTTPException(status_code=404, detail='Комната не найдена')
    room_dict = json.loads(room_data)
    if user_id in room_dict['members']:
        room_dict['members'].remove(user_id)
        if not room_dict['members']:
            client.delete(f'room:{room_id}')
            return {'status': '200', 'message': f'Последний участник покинул комнату {room_id}. Комната удалена.'}
        else:
            if room_dict['host_id'] == user_id:
                room_dict['host_id'] = random.choice(room_dict['members'])
                message = f'Хост покинул комнату. Новый хост - {room_dict["host_id"]}.'
            else:
                message = f'Пользователь {user_id} вышел из комнаты.'
            room_json = json.dumps(room_dict)
            client.set(name=f'room:{room_id}', ex=86400, value=room_json)
            return {'status': '200', 'message': message}
    else:
        raise HTTPException(status_code=404, detail='Пользователь не является участником комнаты')


@app.get('/health')
def health():
    return {'status': 'ok'}