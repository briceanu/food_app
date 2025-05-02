from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALGORITHM : str  
    SECRET: str
    REFRESH_SECRET:str


    class Config:
        env_file='.env'

settings = Settings()