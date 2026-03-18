# 🏥 Hệ thống hỗ trợ chẩn đoán ung thư vú

[![GitHub](https://img.shields.io/badge/GitHub-DoAnTotNghiep-blue)](https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep)
[![Streamlit](https://img.shields.io/badge/Streamlit-Demo-red)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)

## 📋 Mô tả dự án

Hệ thống **AI đa phương thức** để hỗ trợ chẩn đoán ung thư vú sử dụng hai loại dữ liệu:
- **Dữ liệu sinh hóa**: 30 chỉ số từ xét nghiệm FNA → XGBoost (98.67% accuracy)
- **Ảnh mô học**: Histopathology images → EfficientNet-B0 (92% accuracy)

### ✨ Tính năng chính
- ✅ Dự đoán từ chỉ số sinh hóa có giải thích SHAP
- ✅ Phân tích ảnh mô học với EfficientNet-B0
- ✅ Quản lý lịch sử chẩn đoán (MongoDB)
- ✅ Xuất báo cáo PDF
- ✅ Giao diện web thân thiện (React + TypeScript)
- ✅ API RESTful (FastAPI)
- ✅ Quản lý người dùng & phân quyền

---

## 🎯 Nhanh chóng bắt đầu

### Cách khuyến nghị (không cần cài Python/Node/MongoDB)

Chỉ cần cài Docker Desktop, sau đó chạy:

```bash
git clone https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep.git
cd DoAnTotNghiep
docker compose up --build
```

Sau khi chạy xong:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Lưu ý:
- Tài khoản mặc định: admin / Admin@1234
- Mô hình runtime đã có sẵn trong `backend/app/models` để chạy ngay sau khi clone.

---

### 1️⃣ Clone và cài đặt

```bash
# Clone repo
git clone https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep.git
cd DoAnTotNghiep

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Cài dependencies backend
cd backend
pip install -r requirements.txt

# Cài dependencies frontend
cd ../frontend
npm install
```

### 2️⃣ Cấu hình MongoDB

```bash
# Thêm .env trong backend/
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=breast_cancer_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@1234
```

### 3️⃣ Chạy hệ thống

**Terminal 1 - Backend (cổng 8000):**
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend (cổng 5173):**
```bash
cd frontend
npm run dev
```

**Hoặc - Streamlit Demo (nhanh nhất):**
```bash
streamlit run app_demo.py
```

### 4️⃣ Truy cập hệ thống

- **Web**: http://localhost:5173
- **API**: http://localhost:8000
- **Docs API**: http://localhost:8000/docs
- **Streamlit**: http://localhost:8501

---

## 📁 Cấu trúc dự án

```
DoAnTotNghiep/
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── main.py            # Main API endpoints
│   │   ├── model.py           # XGBoost model wrapper
│   │   ├── image_model.py     # EfficientNet wrapper
│   │   ├── auth.py            # JWT authentication
│   │   ├── db.py              # MongoDB connection
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── pdf_utils.py       # PDF generation
│   │   └── models/            # Model files
│   │       ├── xgboost_biochem.joblib
│   │       └── efficientnet_b0.pth
│   └── requirements.txt
│
├── frontend/                   # Frontend React + TypeScript
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
│
├── data/                       # Dataset
│   ├── wdbc.csv              # Wisconsin dataset
│   └── images/               # Histopathology images
│
├── scripts/                    # Training scripts
│   ├── train_model.py
│   ├── train_image_model.py
│   └── download_dataset.py
│
├── app_demo.py                # Streamlit demo
├── Dockerfile                 # For deployment
├── requirements.txt           # Python dependencies (top-level)
└── README.md                  # This file
```

---

## 🚀 Deployment

### Option 1: Hugging Face Spaces (Demo)
```bash
# 1. Tạo Spaces repo trên https://huggingface.co/spaces
# 2. Clone spaces repo
git clone https://huggingface.co/spaces/YOUR-USERNAME/breast-cancer-diagnosis

# 3. Copy files và push
cp app_demo.py breast-cancer-diagnosis/
cp -r backend/app/models/ breast-cancer-diagnosis/
cp requirements.txt breast-cancer-diagnosis/
cd breast-cancer-diagnosis
git add .
git commit -m "Add breast cancer diagnosis system"
git push
```

### Option 2: Railway.app (Full Stack)
```bash
# Deploy từ GitHub repo này
# Railroad sẽ tự động detect Python + Node projects
# Config environment variables trong dashboard
```

### Option 3: Docker
```bash
docker build -t breast-cancer-diagnosis .
docker run -p 8000:8000 breast-cancer-diagnosis
```

---

## 📊 Hiệu suất Models

### XGBoost (Dữ liệu sinh hóa)
| Metric | Value |
|--------|-------|
| Accuracy | 98.67% |
| Precision | 0.9868 |
| Recall | 0.9843 |
| ROC AUC | 0.9986 |
| Dataset | WDBC (569 samples) |

### EfficientNet-B0 (Ảnh mô học)
| Metric | Value |
|--------|-------|
| Val Accuracy | 92.54% |
| Train Accuracy | 95%+ |
| Model Size | ~21 MB |
| Inference Time | ~100ms (CPU) |

---

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Đăng ký tài khoản
- `POST /auth/login` - Đăng nhập
- `GET /auth/me` - Lấy info người dùng hiện tại

### Prediction
- `POST /predict` - Dự đoán từ dữ liệu sinh hóa (XGBoost)
- `POST /predict/image` - Dự đoán từ ảnh (EfficientNet-B0)

### History
- `GET /history` - List lịch sử chẩn đoán
- `GET /history/search?record_code=...` - Tìm theo mã hồ sơ
- `GET /history/{id}/pdf` - Download báo cáo PDF

### Admin
- `GET /admin/users` - List người dùng
- `PATCH /admin/users/{id}` - Cập nhật người dùng
- `DELETE /admin/users/{id}` - Xóa người dùng

---

## 📚 Công nghệ sử dụng

### Backend
- **FastAPI** - Framework API hiện đại
- **PyTorch** - Deep learning framework
- **XGBoost** - Gradient boosting
- **MongoDB** - NoSQL database
- **Pydantic** - Data validation
- **SHAP** - Model explainability
- **ReportLab** - PDF generation

### Frontend
- **React 18** - UI library
- **TypeScript** - Static typing
- **Vite** - Build tool
- **Axios** - HTTP client

### ML/Data
- **scikit-learn** - ML tools
- **NumPy & Pandas** - Data processing
- **Pillow** - Image processing
- **torchvision** - Computer vision

---

## 👥 Thông tin dự án

- **Tác giả**: Nguyễn Quốc Tính
- **Dự án**: Đồ án tốt nghiệp
- **Mục đích**: Hỗ trợ chẩn đoán ung thư vú - AI Công cụ giáo dục
- **Repository**: [GitHub](https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep)

### ⚠️ Lưu ý quan trọng
- ✅ Đây là **công cụ hỗ trợ**, không thay thế chẩn đoán lâm sàng
- ✅ **Luôn cần xác nhận** bởi bác sĩ chuyên môn
- ✅ Dùng cho **mục đích giáo dục & nghiên cứu**
- ✅ **Không sử dụng** trong lâm sàng thực tế mà không kiểm chứng

---

## 📞 Support

Có câu hỏi? Hãy:
1. Kiểm tra [GitHub Issues](https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep/issues)
2. Tạo Issue mới với chi tiết cụ thể
3. Liên hệ qua email (tìm trong GitHub profile)

---

## 📄 License

MIT License - Xem file LICENSE

---

**Made with ❤️ for Breast Cancer Diagnosis Support**
Nguồn phổ biến:
https://www.kaggle.com/datasets/paultimothymooney/breast-histopathology-images
Script scripts/download_image_dataset.py (hoặc hướng dẫn trong đó) sẽ giúp bạn tải về và giải nén vào data/images/.
