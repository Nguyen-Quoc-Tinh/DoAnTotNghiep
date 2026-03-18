# 📖 Hướng dẫn cài đặt và chạy hệ thống

## 🖥️ Yêu cầu hệ thống

- **Python**: 3.10+
- **Node.js**: 16+ (cho frontend)
- **MongoDB**: 4.0+ (local hoặc MongoDB Atlas)
- **RAM**: 8GB+
- **Disk**: 2GB+ (cho models)

---

## 📦 Bước 1: Cài đặt môi trường

### 1.1 Clone repository
```bash
git clone https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep.git
cd DoAnTotNghiep
```

### 1.2 Tạo Python virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Cài dependencies backend
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 1.4 Cài dependencies frontend
```bash
cd frontend
npm install
cd ..
```

---

## 🗄️ Bước 2: Cấu hình MongoDB

### Option A: MongoDB Atlas (Cloud) - Khuyến nghị
1. Tạo tài khoản tại [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Tạo Cluster
3. Lấy Connection String (format: `mongodb+srv://user:pass@cluster.mongodb.net/mydb`)
4. Tạo file `backend/.env`:
```
MONGODB_URL=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=breast_cancer_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@1234
SECRET_KEY=your-secret-key-here
```

### Option B: MongoDB Local
1. Cài MongoDB từ [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. Chạy MongoDB:
```bash
# Windows (nếu cài qua MSI)
mongod

# macOS/Linux
brew services start mongodb-community
```
3. Tạo `backend/.env`:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=breast_cancer_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@1234
SECRET_KEY=your-secret-key-here
```

### Option C: Docker MongoDB
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

---

## 🚀 Bước 3: Chạy ứng dụng

### Cách 1: Chạy Full Stack (Frontend + Backend)

**Terminal 1 - Backend API (cổng 8000):**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend (cổng 5173):**
```bash
cd frontend
npm run dev
```

**Truy cập:**
- 🌐 Web: http://localhost:5173
- 📚 API Docs: http://localhost:8000/docs
- 🏥 Swagger UI: http://localhost:8000/redoc

---

### Cách 2: Chạy Streamlit Demo (Nhanh nhất)

```bash
pip install streamlit
streamlit run app_demo.py
```

**Truy cập:**
- 🎨 Web: http://localhost:8501

---

## 🧪 Bước 4: Kiểm tra hệ thống

### 4.1 Kiểm tra API health
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### 4.2 Đăng nhập mặc định
- **Username**: admin
- **Password**: Admin@1234

### 4.3 Test prediction API
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"features": [1,2,3,...,30]}'
```

---

## 📊 Bước 5: Build production

### Frontend
```bash
cd frontend
npm run build
# Output: dist/
```

### Backend
```bash
# Chuẩn bị .env production
# Chạy: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🐳 Bước 6: Deploy với Docker

### Build image
```bash
docker build -t breast-cancer-diagnosis .
```

### Chạy container
```bash
docker run -p 8000:8000 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  -e DATABASE_NAME=breast_cancer_db \
  breast-cancer-diagnosis
```

---

## 🌐 Bước 7: Deploy lên cloud

### Railway.app (Khuyến nghị)
1. Push code lên GitHub
2. Đăng ký tài khoản tại [railway.app](https://railway.app)
3. Connect GitHub repo
4. Railway tự động detect và deploy

### Hugging Face Spaces (Demo)
```bash
# Xem file: DEPLOY_HUGGINGFACE.md
```

### AWS / Azure / DigitalOcean
- Xem hướng dẫn deploy trong tài liệu từng platform

---

## 🔍 Troubleshooting

### ❌ "ModuleNotFoundError"
```bash
# Đảm bảo virtual environment được activate
which python  # hoặc: where python (Windows)
# Cài lại dependencies
pip install -r backend/requirements.txt
```

### ❌ MongoDB connection error
```bash
# Kiểm tra MongoDB chạy không
mongosh  # hoặc: mongo (phiên bản cũ)
# Nếu kết nối Atlas, kiểm tra IP whitelist
```

### ❌ Port đang được sử dụng
```bash
# Tìm process dùng port
lsof -i :8000  # Linux/Mac
# Hoặc dùng port khác
uvicorn app.main:app --port 8001
```

### ❌ Frontend không kết nối được backend
```bash
# Kiểm tra CORS settings trong backend/app/main.py
# Đảm bảo frontend URL nằm trong allow_origins
```

### ❌ Large file download
```bash
# Models files có thể lớn, chờ download hoàn tất
# Hoặc download riêng từ GitHub Release
```

---

## 📋 Checklist khi setup

- [ ] Clone repository
- [ ] Tạo virtual environment
- [ ] Cài Python dependencies
- [ ] Cài Node.js dependencies
- [ ] Cấu hình MongoDB
- [ ] Tạo file `.env`
- [ ] Chạy backend API
- [ ] Chạy frontend
- [ ] Truy cập http://localhost:5173
- [ ] Đăng nhập bằng admin/Admin@1234
- [ ] Test chức năng chính

---

## 🎓 Lệnh thường dùng

```bash
# Activate environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Chạy backend
cd backend && uvicorn app.main:app --reload

# Chạy frontend
cd frontend && npm run dev

# Chạy Streamlit
streamlit run app_demo.py

# Build frontend
cd frontend && npm run build

# Cài package mới
pip install package-name
npm install package-name

# Deactivate environment
deactivate
```

---

## 📞 Có vấn đề?

1. **Kiểm tra logs**: Xem output terminal để tìm errors
2. **Tìm kiếm issue**: Xem [GitHub Issues](https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep/issues)
3. **Tạo issue mới**: Mô tả chi tiết error + steps to reproduce

---

## 📚 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [MongoDB Documentation](https://docs.mongodb.com)
- [Streamlit Documentation](https://docs.streamlit.io)

---

**Happy coding! 🚀**
