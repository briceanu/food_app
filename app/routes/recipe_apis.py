from fastapi import (APIRouter,
                    Depends,
                    status,
                    HTTPException,
                    Form, 
                    UploadFile, 
                    File,
                    Path,
                    Body,
                    Query)
from sqlalchemy.orm import Session
from db.db_connection import get_db
from . import chef_logic,recipe_logic
from sqlalchemy.exc import IntegrityError
from models import Chef
import schemas
from typing import List, Optional, Annotated
import uuid



router = APIRouter(prefix='/recipe',tags=['recipes routes'])


@router.post('/create')
async def create_recipe(
                        name: str = Form(...),
                        cusine: schemas.Cuisine = Form(...),
                        ingrediensts: str = Form(...),
                        cooking_instructions: str = Form(...),
                        images: Optional[List[UploadFile]] = File(None), 
                        session: Session = Depends(get_db),
                        chef: Chef = Depends(chef_logic.get_current_user),
                        )-> dict:
    try:
        data=recipe_logic.create_recipe(name,
                                        cusine,
                                        ingrediensts,
                                        cooking_instructions,
                                        images,
                                        session,
                                        chef)
        return data
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")
    
 






@router.post('/review/{recipe_id}')
async def create_review(
                        recipe_id: uuid.UUID = Path(...),
                        comment_description: str = Body(...),
                        ratings: schemas.Ratings = Body(...),
                        vote_type:schemas.VoteType=Body(...), 
                        session: Session = Depends(get_db),
                        chef: Chef = Depends(chef_logic.get_current_user),
                        )-> dict:
    try:
        data=recipe_logic.recipe_review(recipe_id,
                                        comment_description,
                                        ratings,
                                        vote_type,
                                        session,
                                        chef)

        return data
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'error: {e.orig}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")








@router.get('/all')
async def list_all_recipes(
                           cusine:Annotated[Optional[str],Query()] = None,
                           ingredients:Annotated[Optional[str],Query()] = None,
                           session:Session=Depends(get_db),
                           )-> list[dict]:
    try:
        recipes = recipe_logic.list_all_recipes(cusine,ingredients,session)
        return recipes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")
    


@router.get('/one/{recipe_id}')
async def list_all_recipes(recipe_id:uuid.UUID,session:Session=Depends(get_db))->dict:
    try:
        recipe = recipe_logic.list_one_recipe(recipe_id,session)
        return recipe
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")
    


@router.get('/chef_recipes')
async def list_all_chef_recipes(
    session:Session=Depends(get_db),
    chef:Chef = Depends(chef_logic.get_current_user))->dict:
    try:
        recipes = recipe_logic.all_recipes_of_one_chef(session,chef)
        return recipes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")
    
# a chef is able to delete its recipe



@router.delete('/remove')
async def remove_recipe(
    recipe_id:uuid.UUID,
    session:Session=Depends(get_db),
    chef:Chef = Depends(chef_logic.get_current_user),
    )-> dict:
    try:
        recipes = recipe_logic.remove_recipe(recipe_id,session,chef)
        return recipes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred: {str(e)}")
    


 