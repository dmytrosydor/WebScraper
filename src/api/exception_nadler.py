from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    
    for error in exc.errors():
    
        field = error["loc"][-1] 
        msg = error["msg"]
        
    
        if error["type"] == "enum":
            allowed_values = error.get("ctx", {}).get("expected", "")
            msg = f"Invalid value. Allowed values are: {allowed_values}"
            
        error_messages.append({
            "field": field,
            "message": msg
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": error_messages
        }
    )