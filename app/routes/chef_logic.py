from fastapi import status,HTTPException,Depends
from sqlalchemy.orm import Session
from schemas import (Chef_Schema_In,
                    UpdatePassword,
                    UpdateUserData,
                    UpdatePhoto)
from models import Chef
from sqlalchemy import insert, select, update, delete
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import timedelta,datetime,timezone
from config import settings
import uuid
from redis_client import redis_client
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from db.db_connection import get_db
import os, shutil

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/chef/sign_in')
pwd_context=CryptContext(schemes=['bcrypt'], deprecated='auto')

ALGORITHM= settings.ALGORITHM
SECRET = settings.SECRET
REFRESH_SECRET = settings.REFRESH_SECRET


# logic for creating an account
def sign_up(chef_data:Chef_Schema_In,session:Session):
    stmt = insert(Chef).values(
        username=chef_data.username,
        password=pwd_context.hash(chef_data.password),
        email=chef_data.email,
        date_of_birth=chef_data.date_of_birth
        )
    session.execute(stmt)
    session.commit()
    return 'account successfully saved'

# authenticate the user 
def authenticate_user(username:str,password:str,session:Session):
    user = session.execute(select(Chef).where(Chef.username==username)).scalar()
    if not user:
        return False
    if not pwd_context.verify(password,user.password):
        return False
    return user


# create and access token
def create_access_token(expires_delta:timedelta,data:dict):
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + expires_delta
    to_encode.update({'exp': expires})
    access_token = jwt.encode(to_encode,SECRET,algorithm=ALGORITHM)
    return access_token

# create refresh token
def create_refresh_token(expires_delta:timedelta,data:dict):
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + expires_delta
    jti = str(uuid.uuid4())
    to_encode.update({'exp':expires,'jti':jti})
    refresh_token = jwt.encode(to_encode,REFRESH_SECRET,algorithm=ALGORITHM)
    return refresh_token

#  black list the token
def black_list_token(jti:str,ttl:int):
    redis_client.setex(f'blacklist:{jti}',ttl,'true')

# check to see if the token is blacklisted
def is_token_blacklisted(jti:str)->bool:
    return redis_client.exists(f'blacklist:{jti}') == 1


# logout the user
def logout(token:str):
    try:
        payload = jwt.decode(token,REFRESH_SECRET,algorithms=ALGORITHM)
        jti = payload.get('jti')
        exp = payload.get('exp')
        if not jti or not exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Invalid token')
        if redis_client.exists(f'blacklist:{jti}')==1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Token already blacklisted')
        ttl = exp - int(datetime.now(timezone.utc).timestamp())
        black_list_token(jti,ttl)
        return {'success':'Logged out successfully'}
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

# get a new access token when the client provides a refesh token
def return_access_from_refresh(token:str,session:Session):
    try:
        payload = jwt.decode(token,REFRESH_SECRET,algorithms=ALGORITHM)
        user = payload.get('sub')
        jti = payload.get('jti')
        username_in_db = session.execute(select(Chef.username).where(Chef.username==user)).scalar()
        if not jti or not username_in_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Invalid Token')
        if is_token_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        access_token = create_access_token(timedelta(minutes=30),data={'sub':username_in_db})
        return {'access_token':access_token}

    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
 
# extract the user from the token
def get_current_user(token:Annotated[str,Depends(oauth2_scheme)],
                    session: Session = Depends(get_db)):
        credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token,SECRET,algorithms=ALGORITHM)
            username = payload.get('sub')
            if username is None:
                raise credentials_exception
        except InvalidTokenError:
            raise credentials_exception
        username_from_db = session.execute(select(Chef.username).where(Chef.username==username)).scalar_one()
        if username_from_db is None:
            raise credentials_exception
        return username_from_db 


# update the users' password
def update_password(data:UpdatePassword,session:Session,user:Chef):
    stmt = (update(Chef)
            .where(Chef.username == user)
            .values(password=pwd_context.hash(data.new_password)))
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'no user with the username {user} found.')
    session.commit()
    return {'success':'password updated'}



def update_user_data(data:UpdateUserData,session:Session,user:Chef):
    stmt = (update(Chef)
            .where(Chef.username==user)
            .values(username=data.username,
                    date_of_birth=data.date_of_birth,
                    email=data.email))
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    session.commit()
    return {'success':'data updated'}


# add a photo to the user account
# in a production base app the photos will be uploaded in a 
# cloud service and the url of the photo is still saved in the db
def upload_photo(photo_file:UpdatePhoto,session:Session,user:Chef):
    MAX_FILE_SIZE = 3.5 * 1024 * 1024 
        # --- Check file size ---
    photo_file.photo.file.seek(0, os.SEEK_END)
    file_size = photo_file.photo.file.tell()
    photo_file.photo.file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 3.5 MB limit"
        )

    DIR = 'uploads/chefs'
    IMG_DIR = os.path.join(DIR,user)
    os.makedirs(IMG_DIR,exist_ok=True)
    # --- Delete old photo if it exists ---
    chef_photo = session.execute(select(Chef.chef_photo).where(Chef.username==user)).scalar()
    if chef_photo and os.path.exists(chef_photo):
            try:
                os.remove(chef_photo)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to remove old photo: {str(e)}")

    file_path = os.path.join(IMG_DIR,photo_file.photo.filename)
    with open(file_path,'wb') as buffer:
        shutil.copyfileobj(photo_file.photo.file,buffer)

    stmt = (update(Chef)
            .where(Chef.username==user)
            .values(chef_photo=file_path))
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    session.commit()
    return {'success':'photo updated'}



def remove_account(session:Session,user:Chef):
    chef_photo = session.execute(select(Chef.chef_photo).where(Chef.username==user)).scalar()
    stmt = delete(Chef).where(Chef.username==user)
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'No user with the name {user} found.')
    
    user_folder = os.path.join('uploads', user)
    if chef_photo and os.path.exists(user_folder):
        try:
            shutil.rmtree(user_folder)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to remove user folder: {str(e)}")

    session.commit()
    return {'success':'account removed'}



def all_chefs(session:Session):
    chefs = session.execute(select(Chef)).scalars().all()
    return chefs