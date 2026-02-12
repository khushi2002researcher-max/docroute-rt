import secrets

fake_tokens = {}

@router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(16)
    fake_tokens[token] = db_user.id

    return {
        "access_token": token,
        "user": {
            "id": db_user.id,
            "name": db_user.full_name,
            "email": db_user.email
        }
    }
