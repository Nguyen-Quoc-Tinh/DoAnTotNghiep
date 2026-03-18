from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

FEATURES_COUNT = 30

class PredictionRequest(BaseModel):
    features: List[float] = Field(..., min_length=FEATURES_COUNT, max_length=FEATURES_COUNT)

class PredictionResponse(BaseModel):
    prediction: Literal["benign", "malignant"]
    probability: float
    explanation: Optional[Dict[str, Any]] = None
    history_id: Optional[str] = None
    record_code: Optional[str] = None
    created_at: Optional[str] = None

class ImagePredictionResponse(BaseModel):
    prediction: Literal["benign", "malignant"]
    confidence: float
    probabilities: Dict[str, float]
    gradcam: Optional[str] = None
    history_id: Optional[str] = None
    record_code: Optional[str] = None
    created_at: Optional[str] = None


class UserCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    role: str = "doctor"
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse


class AdminUserRecord(BaseModel):
    id: str
    username: str
    role: str
    created_at: str
    history_count: int = 0


class UpdateUserRequest(BaseModel):
    role: Optional[Literal["admin", "doctor"]] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class DiagnosisHistoryRecord(BaseModel):
    id: str
    record_code: Optional[str] = None
    diagnosis_type: Literal["biochemical", "image"]
    prediction: Literal["benign", "malignant"]
    confidence: float
    created_at: str
    file_name: Optional[str] = None
    probabilities: Optional[Dict[str, float]] = None
    explanation: Optional[Dict[str, Any]] = None
    input_data: Dict[str, Any]
