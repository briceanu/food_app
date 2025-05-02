from fastapi import FastAPI
from routes.chef_apis import router as chef_router 
from routes.recipe_apis import router as recipe_router

app = FastAPI()




app.include_router(chef_router)
app.include_router(recipe_router)