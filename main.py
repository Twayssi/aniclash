from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from schemas import UserCreate, UserLogin
from security import hash_password, verify_password

import models

app = FastAPI()

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
    return {'user_id': user_table.id, 'user_username': user_table.username}


@app.post('/login')
def login(user: UserLogin, db: Session = Depends(get_db)):
    if '@' in user.identifier:
        user_entry = db.query(models.User).filter(models.User.email == user.identifier).first()
    else:
        user_entry = db.query(models.User).filter(models.User.username == user.identifier).first()
    if not user_entry:
        raise HTTPException(status_code=403, detail='Пользователь с указанным никнеймом/ эл. почтой не найден')

    if verify_password(user_entry.hashed_password, user.password):
        return {'id': user_entry.id, 'username': user_entry.username}
    else:
        raise HTTPException(status_code=401, detail='Неверный пароль.')

    
@app.get('/health')
def health():
    return {'status': 'ok'}