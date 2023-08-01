from fastapi import FastAPI, HTTPException, BackgroundTasks
from starlette.responses import Response
import pandas as pd

from app.db.models import UserAnswer, UserPredictions
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

@app.post("/teddy_cnn_predict", status_code=202)
async def teddy_cnn_predict(payload: UserPredictions, background_tasks: BackgroundTasks):
    payload = payload.dict()
    run_id = pd.Timestamp.now().strftime('%Y-%m-%d-%H-%M-%S')
    background_tasks.add_task(api.teddy_cnn_model_predict, payload)
    return {
        "run_id": run_id,
        "message": "heavy computing in the background",
    }


@app.post("/kai_predict", status_code=201)
def kai_predict(payload: UserPredictions):
    payload = payload.dict()
    run_id, message = pd.Timestamp.now().strftime('%Y-%m-%d-%H-%M-%S'), payload.get("message")
    result = {
        "run_id": run_id,
        "result": api.kai_model_predict(message),
    }
    return result



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
