from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column, Mapped, relationship
from sqlalchemy import DateTime,String,Date,ForeignKey
import uuid
from datetime import datetime,date
from typing import List

class Base(DeclarativeBase):
    ...


class Chef(Base):
    __tablename__ = 'chef'
    chef_id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=lambda:uuid.uuid4(),unique=True)
    username: Mapped[str] = mapped_column(String(60),unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    email:Mapped[str]=mapped_column(String(100),nullable=False)
    date_of_birth:Mapped[date]=mapped_column(Date,nullable=False)
    chef_photo:Mapped[str]=mapped_column(String(),nullable=True)
    recipes:Mapped[List['Recipe']]=relationship('Recipe',back_populates='chef',cascade='all,delete-orphan')



class Recipe_Review(Base):
    __tablename__='recipe_review'

    review_id:Mapped[uuid.UUID] =mapped_column( default=lambda:uuid.uuid4(),primary_key=True,unique=True)
    comment_description:Mapped[str]=mapped_column(String(300),nullable=False)
    date_of_publish:Mapped[datetime] = mapped_column(DateTime,nullable=False,default=datetime.now)
    ratings:Mapped[str]=mapped_column(String(),nullable=False)
    vote_type: Mapped[str] = mapped_column(String(), nullable=False)
    chef_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('chef.chef_id'))
    recipe_id:Mapped[uuid.UUID]= mapped_column(ForeignKey('recipe.recipe_id'))
    recipe:Mapped['Recipe']=relationship('Recipe',back_populates='recipe_review')
 
class Recipe_Image(Base):
    __tablename__='recipe_image'
    image_id:Mapped[uuid.UUID]=mapped_column(default=lambda:uuid.uuid4(),primary_key=True,unique=True)
    image_url:Mapped[str]=mapped_column(String,nullable=True)
    recipe_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('recipe.recipe_id'),nullable=False)
    recipe:Mapped['Recipe']=relationship('Recipe', back_populates='images')

class Recipe(Base):
    __tablename__ = 'recipe'
    recipe_id:Mapped[uuid.UUID]=mapped_column(default=lambda:uuid.uuid4(),primary_key=True,unique=True)
    name: Mapped[str] = mapped_column(String(100))
    cusine:Mapped[str]= mapped_column(String(),nullable=False)
    ingredients:Mapped[str]= mapped_column(String(1000),nullable=False)
    cooking_instructions:Mapped[str]=mapped_column(String(2000),nullable=False)
    date_of_publish:Mapped[datetime] = mapped_column(DateTime,nullable=False,default=datetime.now)
    images:Mapped[list[Recipe_Image]]=relationship(
        'Recipe_Image',back_populates='recipe',cascade='all,delete-orphan')

    chef_id:Mapped[uuid.UUID]=mapped_column(ForeignKey('chef.chef_id'),nullable=False)
    chef:Mapped['Chef']=relationship('Chef',back_populates='recipes')
    recipe_review:Mapped[list[Recipe_Review]]=relationship(
        'Recipe_Review',back_populates='recipe',cascade='all,delete-orphan')
 