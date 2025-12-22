from fastapi import Header, HTTPException, status


def get_idempotency_key(
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key")
):
    if not x_idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Idempotency-Key header is required for this operation",
        )
    return x_idempotency_key
