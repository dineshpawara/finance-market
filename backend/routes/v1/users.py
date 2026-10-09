from fastapi import APIRouter

from core.exceptions import BadRequestException, NotFoundException
from core.logging_config import app_logger, record_audit

userRoute = APIRouter(prefix="/users", tags=["Users V1"])


@userRoute.get("/")
def get_users():
    app_logger.info("Fetching users list from API V1")
    return {"message": "Get Users from API V1", "users": []}


@userRoute.get("/{user_id}")
def get_user_by_id(user_id: int):
    """
    Example demonstrating clean domain exception handling.
    If user_id <= 0, raises BadRequestException (400).
    If user is not found, raises NotFoundException (404).
    """
    if user_id <= 0:
        raise BadRequestException(
            message="User ID must be a positive number",
            details={"provided_id": user_id},
        )
    if user_id != 1:
        raise NotFoundException(
            message=f"User with ID {user_id} not found",
            details={"user_id": user_id},
        )
    return {"user_id": user_id, "name": "Dinesh Pawara", "role": "admin"}


@userRoute.post("/")
def create_users():
    """
    Example demonstrating structured audit logging for financial compliance.
    """
    record_audit(
        action="USER_CREATE_ATTEMPT",
        entity_type="user",
        entity_id="1",
        metadata={"created_by": "system", "role": "trader"},
    )
    return {"message": "Create Users from API V1", "status": "created"}
