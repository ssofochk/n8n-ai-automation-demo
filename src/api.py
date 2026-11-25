from pathlib import Path
from typing import Literal
import math
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, FiniteFloat
from src.calculator import add, subtract, multiply, divide

app = FastAPI(title="Kawaii Calculator")

class Calculation(BaseModel):
    a: FiniteFloat
    b: FiniteFloat
    operation: Literal['add', 'subtract', 'multiply', 'divide']

@app.post('/api/calculate')
def calculate(data: Calculation):
    operations = {'add': add, 'subtract': subtract, 'multiply': multiply, 'divide': divide}
    try:
        result = operations[data.operation](data.a, data.b)
        if not math.isfinite(result):
            raise ValueError('Result is too large')
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'result': result}

app.mount('/', StaticFiles(directory=Path(__file__).resolve().parents[1] / 'frontend', html=True), name='frontend')
