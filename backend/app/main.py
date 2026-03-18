import io
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import numpy as np
import shap
import torch
from bson import ObjectId
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pymongo.errors import DuplicateKeyError
from torchvision import models, transforms
from PIL import Image

from .auth import (
    create_access_token,
    get_admin_user,
    get_current_user,
    get_optional_current_user,
    get_users_collection,
    hash_password,
    require_database,
    serialize_user,
    verify_password,
)
from .db import ensure_indexes, get_database
from .model import XGBoostModel
from .pdf_utils import build_diagnosis_pdf
from .schemas import (
    FEATURES_COUNT,
    AdminUserRecord,
    AuthResponse,
    DiagnosisHistoryRecord,
    ImagePredictionResponse,
    PredictionRequest,
    PredictionResponse,
    UpdateUserRequest,
    UserCredentials,
    UserResponse,
)

app = FastAPI(title="Breast Cancer Diagnosis API")

LOGGER = logging.getLogger(__name__)


XGBOOST_MODEL = XGBoostModel()
MODEL = {
    'model': XGBOOST_MODEL.model,
    'scaler': XGBOOST_MODEL.scaler
}


@app.on_event("startup")
async def startup_event():
    try:
        ensure_indexes()
        _ensure_admin_account()
    except Exception as exc:
        LOGGER.warning("MongoDB is unavailable during startup: %s", exc)


def _ensure_admin_account() -> None:
    import os
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@1234")
    users = get_users_collection()
    existing = users.find_one({"username": admin_username})
    if existing is None:
        insert_result = users.insert_one({
            "username": admin_username,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "created_at": datetime.now(timezone.utc),
        })
        admin_id = str(insert_result.inserted_id)
        LOGGER.info("Admin account '%s' created.", admin_username)
    else:
        admin_id = str(existing["_id"])
        if existing.get("role") != "admin":
            users.update_one({"_id": existing["_id"]}, {"$set": {"role": "admin"}})
            LOGGER.info("User '%s' promoted to admin.", admin_username)

    # Admin chỉ quản lý tài khoản, không lưu hay giữ lịch sử chẩn đoán.
    removed = get_database()["histories"].delete_many({"user_id": admin_id}).deleted_count
    if removed:
        LOGGER.info("Removed %s diagnosis histories for admin account.", removed)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


def serialize_history(record: dict) -> dict:
    record_code = record.get("record_code") or f"HS-{str(record['_id'])[-8:].upper()}"
    return {
        "id": str(record["_id"]),
        "record_code": record_code,
        "diagnosis_type": record["diagnosis_type"],
        "prediction": record["prediction"],
        "confidence": record["confidence"],
        "created_at": record["created_at"].isoformat(),
        "file_name": record.get("file_name"),
        "probabilities": record.get("probabilities"),
        "explanation": record.get("explanation"),
        "input_data": record.get("input_data", {}),
    }


def _generate_record_code() -> str:
    now = datetime.now(timezone.utc)
    suffix = secrets.token_hex(2).upper()
    return f"HS-{now.strftime('%Y%m%d-%H%M%S')}-{suffix}"


def store_history(
    current_user: dict | None,
    diagnosis_type: str,
    prediction: str,
    confidence: float,
    input_data: dict,
    explanation: dict | None = None,
    probabilities: dict | None = None,
    file_name: str | None = None,
    created_at: datetime | None = None,
) -> tuple[str | None, str | None]:
    if current_user is None:
        return None, None

    timestamp = created_at or datetime.now(timezone.utc)
    histories = require_database()["histories"]

    for _ in range(5):
        record_code = _generate_record_code()
        history_document = {
            "user_id": str(current_user["_id"]),
            "record_code": record_code,
            "diagnosis_type": diagnosis_type,
            "prediction": prediction,
            "confidence": float(confidence),
            "input_data": input_data,
            "explanation": explanation,
            "probabilities": probabilities,
            "file_name": file_name,
            "created_at": timestamp,
        }

        try:
            result = histories.insert_one(history_document)
            return str(result.inserted_id), record_code
        except DuplicateKeyError:
            continue
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Không thể lưu lịch sử chẩn đoán: {exc}",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Không thể tạo mã hồ sơ chẩn đoán. Vui lòng thử lại.",
    )


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(credentials: UserCredentials, admin: dict = Depends(get_admin_user)):
    users = get_users_collection()
    username = credentials.username.strip().lower()

    if username == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên này đã được dành riêng.")

    existing_user = users.find_one({"username": username})
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã tồn tại.")

    created_at = datetime.now(timezone.utc)
    insert_result = users.insert_one(
        {
            "username": username,
            "password_hash": hash_password(credentials.password),
            "role": "doctor",
            "created_by": str(admin["_id"]),
            "created_at": created_at,
        }
    )

    user = users.find_one({"_id": insert_result.inserted_id})
    access_token = create_access_token(str(insert_result.inserted_id))
    return AuthResponse(access_token=access_token, user=UserResponse(**serialize_user(user)))


# ─── Admin endpoints ──────────────────────────────────────────────────────────

@app.get("/admin/users", response_model=list[AdminUserRecord])
async def admin_list_users(admin: dict = Depends(get_admin_user)):
    db = get_database()
    users = list(db["users"].find({}).sort("created_at", 1))
    result = []
    for user in users:
        uid = str(user["_id"])
        history_count = db["histories"].count_documents({"user_id": uid})
        result.append(AdminUserRecord(
            id=uid,
            username=user["username"],
            role=user.get("role", "doctor"),
            created_at=user["created_at"].isoformat(),
            history_count=history_count,
        ))
    return result


@app.patch("/admin/users/{user_id}", response_model=AdminUserRecord)
async def admin_update_user(
    user_id: str,
    body: UpdateUserRequest,
    admin: dict = Depends(get_admin_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
    if user_id == str(admin["_id"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể sửa chính tài khoản đang đăng nhập.")

    updates: dict = {}
    if body.role is not None:
        updates["role"] = body.role
    if body.password is not None:
        updates["password_hash"] = hash_password(body.password)

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không có trường nào được cập nhật.")

    db = get_database()
    db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    user = db["users"].find_one({"_id": ObjectId(user_id)})
    uid = str(user["_id"])
    history_count = db["histories"].count_documents({"user_id": uid})
    return AdminUserRecord(
        id=uid,
        username=user["username"],
        role=user.get("role", "doctor"),
        created_at=user["created_at"].isoformat(),
        history_count=history_count,
    )


@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    admin: dict = Depends(get_admin_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
    if user_id == str(admin["_id"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa chính tài khoản đang đăng nhập.")
    db = get_database()
    user = db["users"].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
    if user.get("role") == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa tài khoản admin.")
    db["users"].delete_one({"_id": ObjectId(user_id)})
    db["histories"].delete_many({"user_id": user_id})


@app.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserCredentials):
    users = get_users_collection()
    username = credentials.username.strip().lower()
    user = users.find_one({"username": username})

    if user is None or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai tài khoản hoặc mật khẩu.")

    access_token = create_access_token(str(user["_id"]))
    return AuthResponse(access_token=access_token, user=UserResponse(**serialize_user(user)))


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**serialize_user(current_user))


@app.get("/history", response_model=list[DiagnosisHistoryRecord])
async def list_history(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        return []

    records = (
        get_database()["histories"]
        .find({"user_id": str(current_user["_id"])})
        .sort("created_at", -1)
        .limit(50)
    )
    return [DiagnosisHistoryRecord(**serialize_history(record)) for record in records]


@app.get("/history/search", response_model=DiagnosisHistoryRecord)
async def search_history_by_record_code(record_code: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản admin không có lịch sử chẩn đoán.")

    code = record_code.strip().upper()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng nhập mã hồ sơ.")

    record = get_database()["histories"].find_one(
        {
            "user_id": str(current_user["_id"]),
            "record_code": code,
        }
    )
    if record is None:
        legacy_records = (
            get_database()["histories"]
            .find({"user_id": str(current_user["_id"]), "record_code": {"$exists": False}})
            .sort("created_at", -1)
            .limit(200)
        )
        for legacy in legacy_records:
            legacy_code = f"HS-{str(legacy['_id'])[-8:].upper()}"
            if legacy_code == code:
                record = legacy
                break

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ theo mã này.")

    return DiagnosisHistoryRecord(**serialize_history(record))


@app.get("/history/{history_id}/pdf")
async def download_history_pdf(history_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản admin không có báo cáo chẩn đoán.")

    if not ObjectId.is_valid(history_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi.")

    record = get_database()["histories"].find_one(
        {
            "_id": ObjectId(history_id),
            "user_id": str(current_user["_id"]),
        }
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi.")

    pdf_bytes = build_diagnosis_pdf(record, current_user["username"])
    record_code = record.get("record_code") or f"HS-{history_id[-8:].upper()}"
    filename = f"diagnosis-{record_code}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Predict bằng chỉ số sinh hóa (XGBoost model) và trả về giải thích SHAP."""
    if current_user and current_user.get("role") == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản admin chỉ dùng để quản lý tài khoản bác sĩ.")

    if len(request.features) != FEATURES_COUNT:
        raise HTTPException(status_code=400, detail=f"Cần đúng {FEATURES_COUNT} đặc trưng.")

    features = np.array(request.features, dtype=float)
    explanation = None
    if XGBOOST_MODEL is not None:
        prediction, score = XGBOOST_MODEL.predict(features)
        # SHAP explainability (top 5 features)
        try:
            explainer = shap.TreeExplainer(MODEL['model'])
            features_scaled = MODEL['scaler'].transform(features.reshape(1, -1))
            shap_values = explainer.shap_values(features_scaled)
            feature_names = [
                "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
                "compactness_mean", "concavity_mean", "concave_points_mean", "symmetry_mean", "fractal_dimension_mean",
                "radius_se", "texture_se", "perimeter_se", "area_se", "smoothness_se",
                "compactness_se", "concavity_se", "concave_points_se", "symmetry_se", "fractal_dimension_se",
                "radius_worst", "texture_worst", "perimeter_worst", "area_worst", "smoothness_worst",
                "compactness_worst", "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
            ]
            # Nếu là binary classification, shap_values là list, lấy class 1
            if isinstance(shap_values, list):
                shap_arr = shap_values[1][0]
            else:
                shap_arr = shap_values[0]
            # Get top 5 features by absolute SHAP value
            top_idx = np.argsort(np.abs(shap_arr))[::-1][:5]
            explanation = {feature_names[i]: float(shap_arr[i]) for i in top_idx}

            # Rule-based mapping for explanation text (Vietnamese)
            feature_rule_map = {
                "radius_mean": ("Bán kính trung bình", "Bán kính lớn hơn bình thường, tăng nguy cơ ác tính.", "Bán kính nhỏ hơn bình thường, giảm nguy cơ ác tính."),
                "texture_mean": ("Độ nhám trung bình", "Độ nhám cao, tăng nguy cơ ác tính.", "Độ nhám thấp, giảm nguy cơ ác tính."),
                "perimeter_mean": ("Chu vi trung bình", "Chu vi lớn, tăng nguy cơ ác tính.", "Chu vi nhỏ, giảm nguy cơ ác tính."),
                "area_mean": ("Diện tích trung bình", "Diện tích lớn, tăng nguy cơ ác tính.", "Diện tích nhỏ, giảm nguy cơ ác tính."),
                "smoothness_mean": ("Độ nhẵn trung bình", "Độ nhẵn cao, tăng nguy cơ ác tính.", "Độ nhẵn thấp, giảm nguy cơ ác tính."),
                "compactness_mean": ("Độ đặc trung bình", "Độ đặc cao, tăng nguy cơ ác tính.", "Độ đặc thấp, giảm nguy cơ ác tính."),
                "concavity_mean": ("Độ lõm trung bình", "Độ lõm cao, tăng nguy cơ ác tính.", "Độ lõm thấp, giảm nguy cơ ác tính."),
                "concave_points_mean": ("Số điểm lõm trung bình", "Nhiều điểm lõm, tăng nguy cơ ác tính.", "Ít điểm lõm, giảm nguy cơ ác tính."),
                "symmetry_mean": ("Độ đối xứng trung bình", "Đối xứng cao, tăng nguy cơ ác tính.", "Đối xứng thấp, giảm nguy cơ ác tính."),
                "fractal_dimension_mean": ("Chỉ số fractal trung bình", "Chỉ số fractal cao, tăng nguy cơ ác tính.", "Chỉ số fractal thấp, giảm nguy cơ ác tính."),
                # ... có thể bổ sung các đặc trưng khác tương tự ...
            }
            explanation_text = []
            for i in top_idx:
                fname = feature_names[i]
                shap_val = shap_arr[i]
                if fname in feature_rule_map:
                    label, pos_text, neg_text = feature_rule_map[fname]
                    if shap_val > 0:
                        explanation_text.append(f"{label}: {pos_text}")
                    else:
                        explanation_text.append(f"{label}: {neg_text}")
                else:
                    explanation_text.append(f"{fname}: {'Tác động tăng nguy cơ' if shap_val > 0 else 'Tác động giảm nguy cơ'}")
            # Trả về cả explanation và explanation_text
            explanation = {
                "values": {feature_names[i]: float(shap_arr[i]) for i in top_idx},
                "text": explanation_text
            }
        except Exception as e:
            explanation = {"error": f"Không thể sinh giải thích SHAP: {str(e)}"}
    else:
        # Placeholder model: simple heuristic using mean value
        score = float(np.clip(features.mean() / 30.0, 0.0, 1.0))
        prediction = "malignant" if score > 0.5 else "benign"
        explanation = None

    created_at = datetime.now(timezone.utc)
    history_id, record_code = store_history(
        current_user=current_user,
        diagnosis_type="biochemical",
        prediction=prediction,
        confidence=round(score, 4),
        input_data={"features": request.features},
        explanation=explanation,
        created_at=created_at,
    )

    return PredictionResponse(
        prediction=prediction,
        probability=round(score, 4),
        explanation=explanation,
        history_id=history_id,
        record_code=record_code,
        created_at=created_at.isoformat(),
    )

@app.post("/predict/image", response_model=ImagePredictionResponse)
async def predict_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Dự đoán ung thư vú từ ảnh mô học bằng EfficientNet-B0."""
    if current_user and current_user.get("role") == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản admin chỉ dùng để quản lý tài khoản bác sĩ.")

    try:
        # Đọc file ảnh
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Không thể đọc file ảnh. Hãy kiểm tra định dạng ảnh.")

    # Tiền xử lý ảnh
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    input_tensor = transform(img).unsqueeze(0)

    # Load EfficientNet-B0
    import os
    model_path = os.path.join(os.path.dirname(__file__), "models", "efficientnet_b0.pth")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    import torch.nn as nn
    model = models.efficientnet_b0(pretrained=False)
    # Sửa số lớp output cho đúng với checkpoint (2 lớp)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    state = torch.load(model_path, map_location=device)
    if isinstance(state, dict) and 'model_state_dict' in state:
        state = state['model_state_dict']
    model.load_state_dict(state)
    model.eval()
    model.to(device)

    # Dự đoán
    with torch.no_grad():
        input_tensor = input_tensor.to(device)
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
        pred_idx = int(np.argmax(probs))
        classes = ["benign", "malignant"]
        prediction = classes[pred_idx]
        confidence = float(probs[pred_idx])
        probabilities = {"benign": float(probs[0]), "malignant": float(probs[1])}

    # Không sinh Grad-CAM ở đây (có thể bổ sung sau)
    created_at = datetime.now(timezone.utc)
    history_id, record_code = store_history(
        current_user=current_user,
        diagnosis_type="image",
        prediction=prediction,
        confidence=confidence,
        input_data={"file_name": file.filename or "uploaded-image"},
        probabilities=probabilities,
        file_name=file.filename,
        created_at=created_at,
    )

    return ImagePredictionResponse(
        prediction=prediction,
        confidence=confidence,
        probabilities=probabilities,
        gradcam=None,
        history_id=history_id,
        record_code=record_code,
        created_at=created_at.isoformat(),
    )
