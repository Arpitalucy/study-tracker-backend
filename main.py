import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

import models, schemas, auth, database
from database import engine, get_db
from jose import JWTError, jwt

load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Study Tracker API")

# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173") # Default Vite port
origins = [
    frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("NODE_ENV") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# AUTH ENDPOINTS
@app.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# GOALS ENDPOINTS
@app.get("/goals", response_model=List[schemas.Goal])
def read_goals(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Goal).filter(models.Goal.owner_id == current_user.id).all()

@app.post("/goals", response_model=schemas.Goal)
def create_goal(goal: schemas.GoalCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_goal = models.Goal(**goal.dict(), owner_id=current_user.id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id, models.Goal.owner_id == current_user.id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Also delete child subjects
    db.query(models.Subject).filter(models.Subject.goal_id == goal_id).delete()
    db.delete(db_goal)
    db.commit()
    return {"message": "Goal deleted"}

# SUBJECTS ENDPOINTS
@app.get("/subjects", response_model=List[schemas.Subject])
def read_subjects(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_subjects = db.query(models.Subject).filter(models.Subject.owner_id == current_user.id).all()
    # Map from DB model to schema (handle camelCase vs snake_case if needed)
    return [
        schemas.Subject(
            id=s.id, goalId=s.goal_id, name=s.name, color=s.color,
            trackingMode=s.tracking_mode, schedule=s.schedule,
            totalStudyHours=s.total_study_hours, totalTargetHours=s.total_target_hours
        ) for s in db_subjects
    ]

@app.post("/subjects", response_model=schemas.Subject)
def create_or_update_subject(subject: schemas.SubjectCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject.id, models.Subject.owner_id == current_user.id).first()
    
    data = {
        "id": subject.id,
        "goal_id": subject.goalId,
        "name": subject.name,
        "color": subject.color,
        "tracking_mode": subject.trackingMode,
        "schedule": subject.schedule,
        "total_study_hours": subject.totalStudyHours,
        "total_target_hours": subject.totalTargetHours,
        "owner_id": current_user.id
    }

    if db_subject:
        for key, value in data.items():
            setattr(db_subject, key, value)
    else:
        db_subject = models.Subject(**data)
        db.add(db_subject)
    
    db.commit()
    db.refresh(db_subject)
    return schemas.Subject(
        id=db_subject.id, goalId=db_subject.goal_id, name=db_subject.name, color=db_subject.color,
        trackingMode=db_subject.tracking_mode, schedule=db_subject.schedule,
        totalStudyHours=db_subject.total_study_hours, totalTargetHours=db_subject.total_target_hours
    )

@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id, models.Subject.owner_id == current_user.id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(db_subject)
    db.commit()
    return {"message": "Subject deleted"}

# NOTIFICATIONS ENDPOINTS
@app.get("/notifications", response_model=List[schemas.Notification])
def read_notifications(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_notifs = db.query(models.Notification).filter(models.Notification.owner_id == current_user.id).all()
    return [
        schemas.Notification(
            id=n.id, subjectId=n.subject_id, subjectName=n.subject_name,
            type=n.type, scheduledHours=n.scheduled_hours, scheduledTime=n.scheduled_time,
            scheduledDate=n.scheduled_date, status=n.status, read=n.read, timestamp=n.timestamp
        ) for n in db_notifs
    ]

@app.post("/notifications/sync", response_model=List[schemas.Notification])
def sync_notifications(notifications: List[schemas.NotificationCreate], current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Bulk update/insert notifications
    for n in notifications:
        db_n = db.query(models.Notification).filter(models.Notification.id == n.id, models.Notification.owner_id == current_user.id).first()
        data = {
            "id": n.id, "subject_id": n.subjectId, "subject_name": n.subjectName,
            "type": n.type, "scheduled_hours": n.scheduledHours, "scheduled_time": n.scheduledTime,
            "scheduled_date": n.scheduledDate, "status": n.status, "read": n.read,
            "timestamp": n.timestamp, "owner_id": current_user.id
        }
        if db_n:
            for key, value in data.items(): setattr(db_n, key, value)
        else:
            db.add(models.Notification(**data))
    
    db.commit()
    return read_notifications(current_user, db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
