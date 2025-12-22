from fastapi import Header, HTTPException, status

def admin_required(x_role: str = Header(...)):
    if x_role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
