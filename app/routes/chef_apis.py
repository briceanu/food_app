from fastapi import (APIRouter,
                      Depends,
                    HTTPException,
                    status,
                    Header,
                    Form)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from schemas import (Chef_Schema_In,
                    Chef_Schema_Out,
                    Token,
                    NewAccessToken,
                    UpdatePassword,
                    UpdateUserData,
                    UpdatePhoto)
from . import chef_logic
from db.db_connection import get_db
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from jwt.exceptions import InvalidTokenError
from models import Chef

router = APIRouter(prefix='/chef',tags=['chefs routes'])


# route for creating a chef account
@router.post('/sign_up')
async def sign_up(user_data:Chef_Schema_In,session:Session=Depends(get_db)) -> str:
    try:
        create_account=chef_logic.sign_up(user_data,session)
        return create_account
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")


# route for signing in and getting access and refresh tokens
@router.post('/sign_in')
async def get_tokens(
    form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
    session:Session=Depends(get_db))-> Token:
    unauthoriezed_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Invalid username or password',
                    headers={"WWW-Authenticate": "Bearer"}) 
    user = chef_logic.authenticate_user(form_data.username,form_data.password,session)
    if not user:
        raise unauthoriezed_exception
    access_token = chef_logic.create_access_token(timedelta(minutes=30),data={'sub':form_data.username})
    refresh_token = chef_logic.create_refresh_token(timedelta(minutes=2),data={'sub':form_data.username})
    return {'token_type':'bearer', 'access_token':access_token,'refresh_token':refresh_token}
     



# route for logout and blacklist the refresh token
@router.post('/logout')
async def logout_user(token:Annotated[str,Header()])-> dict:
    try:
        logout = chef_logic.logout(token)
        return logout
    except HTTPException:
        raise
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

# route used to send a new access token when the client
# sends a refesh token
@router.post('/new_access_token')
async def get_access_from_refresh(token:Annotated[str,Header()], 
                    session:Session=Depends(get_db))-> NewAccessToken:
    try:
        new_acess_token = chef_logic.return_access_from_refresh(token,session)
        return new_acess_token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")


# route for updating the password
@router.patch('/chanage_password')
async def update_password(
                            user_data:Annotated[UpdatePassword,Form()],
                            session:Session=Depends(get_db),
                            user:Chef=Depends(chef_logic.get_current_user),
                            )-> dict:

    try:
        result = chef_logic.update_password(user_data,session,user)
        return result
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")




# update user data (email,username,date_of_birth)
@router.patch('/update_data')
async def update_user_data(
                            user_data:UpdateUserData,
                            session:Session=Depends(get_db),
                            user:Chef=Depends(chef_logic.get_current_user),
                            ) -> dict:

    try:
        result = chef_logic.update_user_data(user_data,session,user)
        return result
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")



@router.patch('/update_photo')
async def update_user_photo(
                            photo_file:UpdatePhoto = Depends(),
                            session:Session=Depends(get_db),
                            user:Chef=Depends(chef_logic.get_current_user),
                            )-> dict:

    try:
        result = chef_logic.upload_photo(photo_file,session,user)
        return result
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")

# remove account
@router.delete('/remove_account')
async def remove_user_account(
                            session:Session=Depends(get_db),
                            user:Chef=Depends(chef_logic.get_current_user),
                            )-> dict:

    try:
        result = chef_logic.remove_account(session,user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")








@router.get('/all')
async def get_all_chefs(session:Session=Depends(get_db),
                user:Chef=Depends(chef_logic.get_current_user))-> list[Chef_Schema_Out]:
    try:
        get_chefs=chef_logic.all_chefs(session)
        return get_chefs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")


