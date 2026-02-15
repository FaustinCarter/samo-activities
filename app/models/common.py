import typing
import pydantic


class PageInfo(pydantic.BaseModel):
    order_by: str = ""
    order_option: str = "ASC"
    total_page: int = 1
    total_records_per_page: int = 20
    total_records: int = 0
    page_number: int = 1


class ResponseHeaders(pydantic.BaseModel):
    response_code: str
    response_message: str
    page_info: PageInfo = pydantic.Field(default_factory=PageInfo)


T = typing.TypeVar("T")


class ResponseEnvelope(pydantic.BaseModel, typing.Generic[T]):
    headers: ResponseHeaders
    body: T
