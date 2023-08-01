from fastapi import FastAPI, HTTPException
from starlette.responses import Response

from app.db.models import UserAnswer
from app.api import api

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Fast API in Python"}


@app.get("/user")
def read_user():
    return api.read_user()


@app.get("/packageversion/{package}", status_code=200)
def read_questions(package: str, response: Response):
    question = api.check_package(package)

    if not question:
        raise HTTPException(status_code=400, detail="Error")

    return question

@app.get("/model_inference/{data}", status_code=200)
def get_prediction(data: str, response: Response):
    predictions = api.model_inference(data)

    if not predictions:
        raise HTTPException(status_code=400, detail="Error")

    return predictions

# @app.get("/alternatives/{question_id}")
# def read_alternatives(question_id: int):
#     return api.read_alternatives(question_id)


# @app.post("/answer", status_code=201)
# def create_answer(payload: UserAnswer):
#     payload = payload.dict()

#     return api.create_answer(payload)


# @app.get("/result/{user_id}")
# def read_result(user_id: int):
#     return api.read_result(user_id)
