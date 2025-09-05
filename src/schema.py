from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import TypeVar, Generic, List

class Admin(BaseModel):
    username: str
    password: str
    email: str
    name: str

class User(BaseModel):
    username: str
    password: str
    email: str
    name: str
    status: str
    
class LoginModel(BaseModel):
    username: str
    password: str
T = TypeVar('T')

class ResponseModel(GenericModel, Generic[T]):
    code: int
    message: str
    data: T

class ListResponseModel(GenericModel, Generic[T]):
    code: int
    message: str
    data: List[T]

UserCreateResponse = ResponseModel[User]
AdminCreateResponse = ResponseModel[Admin]

UserGetResponse = ResponseModel[User]
AdminGetResponse = ResponseModel[Admin]

UserListResponse = ListResponseModel[User]
AdminListResponse = ListResponseModel[Admin]

UserUpdateResponse = ResponseModel[User]
AdminUpdateResponse = ResponseModel[Admin]

UserDeleteResponse = ResponseModel[User]
AdminDeleteResponse = ResponseModel[Admin]
