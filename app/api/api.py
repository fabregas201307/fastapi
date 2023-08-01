import json
import subprocess
import importlib.metadata
import pandas as pd
import numpy as np
import time



def read_user() -> dict:
    output = subprocess.check_output(['whoami'])
    users = {"output": output}
    return users


def check_package(package: str) -> dict:
    try:
        package_version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        package_version = "not available"
    
    results = {
        "package": package,
        "version": package_version
    }
    return results

def model_inference(data: str) -> dict:
    results = {
        "input": data,
        "output": data
    }
    return results


def read_alternatives(question_id: int):
    alternatives_question = []
    with open('data/alternatives.json') as stream:
        alternatives = json.load(stream)

    for alternative in alternatives:
        if alternative['question_id'] == question_id:
            alternatives_question.append(alternative)

    return alternatives_question


def create_answer(payload):
    answers = []
    result = []

    with open('data/alternatives.json') as stream:
        alternatives = json.load(stream)

    for question in payload['answers']:
        for alternative in alternatives:
            if alternative['question_id'] == question['question_id']:
                answers.append(alternative['alternative'])
                break

    with open('data/cars.json') as stream:
        cars = json.load(stream)

    for car in cars:
        if answers[0] in car.values() and answers[1] in car.values() and answers[2] in car.values():
            result.append(car)

    return result

def teddy_cnn_model_predict(payload) -> list:
    time.sleep(20)
    keys = payload.keys()
    result = list(keys)
    print("after sleep:")
    print(result)
    filename = "/fiquant/mlops" + "mlops_heavy_computing_results.json"
    with open(filename, "w") as f:
        json.dump(payload, f, indent=4)
    return result

def kai_model_predict(message) -> dict:
    data_dict = message
    data_received = pd.DataFrame.from_dict(data_dict)
    data_received = data_received.replace({"None": None})

    data_received = data_received.astype(float)
    result_df = data_received.describe()
    result_df = result_df.replace({np.nan: "None"}) # json don't like NaN

    result = result_df.to_dict()
    return result


def read_result(user_id: int):
    user_result = []

    with open('data/results.json') as stream:
        results = json.load(stream)

    with open('data/users.json') as stream:
        users = json.load(stream)

    with open('data/cars.json') as stream:
        cars = json.load(stream)

    for result in results:
        if result['user_id'] == user_id:
            for user in users:
                if user['id'] == result['user_id']:
                    user_result.append({'user': user})
                    break

        for car_id in result['cars']:
            for car in cars:
                if car_id == car['id']:
                    user_result.append(car)

    return user_result
