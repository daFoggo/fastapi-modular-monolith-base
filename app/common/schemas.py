from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseSchema[T](BaseModel):
    success: bool = True
    message: str = "Success"
    data: T | None = None


class FindResult[T](BaseModel):
    founds: list[T]
    total_count: int
    page: int
    page_size: int
