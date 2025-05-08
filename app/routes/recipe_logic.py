from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session,joinedload
from models import Chef,Recipe, Recipe_Image, Recipe_Review
from sqlalchemy import select,insert, func,and_, delete
import os, shutil,uuid
from schemas import VoteType






def validate_photos(value: UploadFile):
    allowed_ext = ['jpg', 'jpeg', 'png']
    filename = value.filename.lower()

    # Check for double extensions
    if filename.count('.') > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name: Double extensions are not allowed. Only one dot is allowed."
        )

    ext = filename.split('.')[-1]
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpeg, jpg, and png files are allowed for images."
        )
    return value

def protection_against_xss(value):
    not_allowed_char=['script','<','>']
    for i in not_allowed_char:
        if i in value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='forbidden characters: script,>,<')
    return value

def create_recipe(name,
                  cusine,
                  ingrediensts,
                  cooking_instructions,
                  images,
                  session:Session,
                  chef:Chef,
                  ):

    protection_against_xss(name)
    protection_against_xss(ingrediensts)
    protection_against_xss(cooking_instructions)


    chef_id_from_db=session.execute(select(Chef.chef_id).where(Chef.username==chef)).scalar()
    if chef_id_from_db is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'not user with the name {chef}')
    # allow chefs to upload no more than 6 pictures
    if images and len(images) > 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='You can only upload 6 images.')
    # in a production app the images are saved in a S3 bucket
    DIR = 'uploads/recipes'
    IMG_DIR = os.path.join(DIR, chef)  
    images_list= []

    if images:
        os.makedirs(IMG_DIR, exist_ok=True)  # Only make the directory once
        for image in images:  
            validate_photos(image)
            file_path = os.path.join(IMG_DIR, image.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            images_list.append(Recipe_Image(image_url=file_path))

    new_recipe = Recipe(
        name=name,
        cusine=cusine.value,
        ingredients=ingrediensts,
        cooking_instructions=cooking_instructions,
        chef_id=chef_id_from_db,
        images=images_list  
    )

    session.add(new_recipe)
    session.commit()
    session.refresh(new_recipe)


    return {'success':'recipe saved'}


def recipe_review(recipe_id,
                  comment_description,
                  ratings,
                  vote_type,
                  session:Session,
                  chef:Chef):
    
    protection_against_xss(comment_description)
    chef_id = session.execute(select(Chef.chef_id).where(Chef.username==chef)).scalar()
    stmt = insert(Recipe_Review).values(
        recipe_id=recipe_id,
        comment_description=comment_description,
        ratings=ratings.value,
        vote_type=vote_type.value,
        chef_id=chef_id
        )
    session.execute(stmt)
    session.commit()

 


    return {'success':'review saved'}

 





def list_all_recipes(cusine:str,ingredients:str,session:Session):
    stmt = (
        select(Recipe)
        .options(joinedload(Recipe.images))
        .options(joinedload(Recipe.recipe_review))
        .offset(0)
        .limit(10)
    )

    filters = []

    if cusine:
        filters.append(Recipe.cusine == cusine.strip().capitalize())

    if ingredients:
        filters.append(func.lower(Recipe.ingredients).ilike(f"%{ingredients.strip().lower()}%"))

    if filters:
        stmt = stmt.where(and_(*filters))

    recipes = session.execute(stmt).scalars().unique().all()



    updated_recipes=[]
    for recipe in recipes:
        like_count = sum(1 for review in recipe.recipe_review if review.vote_type== "Like")
        dislike_count = sum(1 for review in recipe.recipe_review if review.vote_type == 'Dislike')

        recipe_fields = {
            "name": recipe.name,
            "cusine": recipe.cusine,
            "cooking_instructions": recipe.cooking_instructions,
            "chef_id": recipe.chef_id,
            "recipe_id": recipe.recipe_id,
            "ingredients": recipe.ingredients,
            "date_of_publish": recipe.date_of_publish,
            "images": [{"image_url": img.image_url} for img in recipe.images],
            "recipe_review": [
                {
                    "review_id": review.review_id,
                    "comment_description": review.comment_description,
                    "vote_type": review.vote_type,
                    "ratings": review.ratings,
                    "date_of_publish": review.date_of_publish,
                    "chef_id": review.chef_id,
                    "recipe_id": review.recipe_id,
                }
                for review in recipe.recipe_review
            ],
            "total_likes": like_count,
            "total_dislikes": dislike_count,
        }
        
        updated_recipes.append(recipe_fields)
    return updated_recipes

 

def list_one_recipe(recipe_id:uuid.UUID,session:Session):
    stmt=(select(Recipe)
          .where(Recipe.recipe_id==recipe_id)
          .options(joinedload(Recipe.images))
          .options(joinedload(Recipe.recipe_review)))

    recipe = session.execute(stmt).scalars().unique().first()
    like_count = sum(1 for review in recipe.recipe_review if review.vote_type== "Like")
    dislike_count = sum(1 for review in recipe.recipe_review if review.vote_type == 'Dislike')

    return {
            "name": recipe.name,
            "cusine": recipe.cusine,
            "cooking_instructions": recipe.cooking_instructions,
            "chef_id": recipe.chef_id,
            "recipe_id": recipe.recipe_id,
            "ingredients": recipe.ingredients,
            "date_of_publish": recipe.date_of_publish,
            "images": [{"image_url": img.image_url} for img in recipe.images],
            "recipe_review": [
                {
                    "review_id": review.review_id,
                    "comment_description": review.comment_description,
                    "vote_type": review.vote_type,
                    "ratings": review.ratings,
                    "date_of_publish": review.date_of_publish,
                    "chef_id": review.chef_id,
                    "recipe_id": review.recipe_id,
                }
                for review in recipe.recipe_review
            ],
            "total_likes": like_count,
            "total_dislikes": dislike_count,
        }



# get all the recipes of one chef
def all_recipes_of_one_chef(session:Session,chef:Chef):
    chef_id = session.execute(select(Chef.chef_id).where(Chef.username==chef)).scalar()
    stmt = (select(Recipe)
            .options(joinedload(Recipe.recipe_review))
            .options(joinedload(Recipe.images))
            .where(Recipe.chef_id==chef_id))
    recipes = session.execute(stmt).scalars().unique().all()
    return recipes


# delete a recipe
def remove_recipe(recipe_id:uuid.UUID,session:Session,chef:Chef):
    chef_id = session.execute(select(Chef.chef_id).where(Chef.username==chef)).scalar_one()
    if chef_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=f'no chef with the name {chef} found.')
    stmt = (delete(Recipe)
                    # validating the the chef owns the recipes
            .where(Recipe.recipe_id==recipe_id,Recipe.chef_id==chef_id))
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail=f'No allowed to remove this recipe.')
    return {'success':'recipe removed'}

 