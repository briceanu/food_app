from pydantic import (BaseModel,
                      Field,
                      EmailStr,
                      field_validator,
                      model_validator)
from fastapi import UploadFile, HTTPException, status
from datetime import date
import re
from enum import Enum
 
def validate(value):
    if len(value) < 6:
        raise ValueError('Password must be at least 6 characters long')
    if not re.search(r'[A-Za-z]', value):  # Check for at least one letter
        raise ValueError('Password must include at least one letter')
    if not re.search(r'\d', value): 
        raise ValueError('Password must contain at least one number')
    return value


def validate_birth(value):
    today = date.today()
    age  = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18 :
        raise ValueError('Age can not be less than 18 years old.')
    return value




class Chef_Schema_In(BaseModel):
    username:str=Field(...,max_length=60)
    password:str
    confirm_password:str
    email:EmailStr
    date_of_birth:date
    class Config:
        extra = 'forbid'
# validating the user to be greater than 18 years old
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls,value):
        return validate_birth(value)

    @field_validator('password')
    @classmethod
    def validate_password(cls,value):
        return validate(value)

    @model_validator(mode='before')
    @classmethod
    def validate( cls,values):
        if values.get('password') != values.get('confirm_password'):
            raise ValueError('Passwords do not match')
        return values




class Chef_Schema_Out(BaseModel):
    username:str
    password:str
    email:EmailStr
    date_of_birth:date
    chef_photo:str|None
    class Config:
        extra='forbid'


class Token(BaseModel):
    token_type:str
    access_token:str
    refresh_token:str


class NewAccessToken(BaseModel):
    access_token:str



class UpdatePassword(BaseModel):
    new_password:str=Field(...,min_length=6)
    confirm_new_password:str=Field(...,min_length=6)
    class Config:
        extra = 'forbid'


    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls,value):
        return validate(value)
    
    @model_validator(mode='before')
    @classmethod
    def validate(cls, values):
        if values.get('new_password') != values.get('confirm_new_password'):
            raise ValueError('Passwords do not match')
        return values
        

class UpdateUserData(BaseModel):
    username:str
    email:EmailStr
    date_of_birth:date
    class Config:
        extra = 'forbid'
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls,value):
        return validate_birth(value)
    
class UpdatePhoto(BaseModel):
    photo:UploadFile
    class Config:
        extra = 'forbid'


    @field_validator('photo')
    @classmethod
    def validate_photo(cls,value):
        allowed_ext = ['jpg','jpeg','png']
        filename = value.filename.lower()
        parts = filename.split('.')
        if len(parts) > 2 :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name: Double extensions are not allowed. No more than one dot allowed."
            )
        ext = parts[-1]
        if ext not in allowed_ext:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Only jpeg, jpg, and png files are allowed for images.')
        return value 


 

# cuisine schema

class Cuisine(Enum):
    ITALIAN = "Italian"
    CHINESE = "Chinese"
    INDIAN = "Indian"
    MEXICAN = "Mexican"
    FRENCH = "French"


 


class Ratings(Enum):
    EXCELLENT = 'Excellent'
    VERY_GOOD = 'Very Good'
    SATISFACTORY = 'Satisfactory'
    DISAPPOINTING = 'Disappointing'
    UNPALATABLE = 'Unpalatable'


class Cuisine(Enum):
    ITALIAN = "Italian"
    CHINESE = "Chinese"
    INDIAN = "Indian"
    MEXICAN = "Mexican"
    FRENCH = "French"

class VoteType(Enum):
    LIKE = "Like"
    DISLIKE = "Dislike"

