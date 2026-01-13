from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any

# AUTH
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# GOALS
class GoalBase(BaseModel):
    id: str
    title: str
    type: str # MONTHLY, EXAM
    details: Any

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    owner_id: int
    class Config:
        from_attributes = True

# SUBJECTS
class SubjectBase(BaseModel):
    id: str
    goalId: str
    name: str
    color: str
    trackingMode: str = "SCHEDULE"
    schedule: Optional[Any] = None
    totalStudyHours: float = 0.0
    totalTargetHours: Optional[float] = None

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    owner_id: int
    class Config:
        from_attributes = True

# NOTIFICATIONS
class NotificationBase(BaseModel):
    id: str
    subjectId: str
    subjectName: str
    type: str
    scheduledHours: float
    scheduledTime: str
    scheduledDate: str
    status: str
    read: bool = False
    timestamp: int

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    owner_id: int
    class Config:
        from_attributes = True
# CHAPTERS
class ChapterBase(BaseModel):
    id: str
    subjectId: str
    name: str
    targetDate: str
    targetTime: Optional[str] = None
    estimatedDuration: Optional[str] = None
    completed: bool = False

class ChapterCreate(ChapterBase):
    pass

class Chapter(ChapterBase):
    class Config:
        from_attributes = True
