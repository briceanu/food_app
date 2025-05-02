from fastapi import APIRouter


router = APIRouter(prefix='/recipe',tags=['recipes routes'])


@router.post('/create')
async def sign_up():
    return 'create a revipce up'