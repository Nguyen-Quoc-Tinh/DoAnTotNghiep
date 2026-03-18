# 🚀 Hướng dẫn Deploy lên Hugging Face Spaces

## Bước 1: Tạo Hugging Face Account
1. Đăng ký tài khoản tại [huggingface.co](https://huggingface.co)
2. Tạo Personal Access Token tại Settings → Access Tokens

---

## Bước 2: Tạo Spaces Repository

### Cách A: Tạo qua Web Interface
1. Vào https://huggingface.co/spaces
2. Click **"Create new Space"**
3. **Space name**: `breast-cancer-diagnosis`
4. **License**: MIT
5. **Space SDK**: Streamlit
6. Click **Create Space**

### Cách B: Tạo qua CLI
```bash
huggingface-cli repo create breast-cancer-diagnosis --type space --space-sdk streamlit
```

---

## Bước 3: Clone Spaces Repository

```bash
# Login vào Hugging Face (nếu chưa)
huggingface-cli login

# Clone Spaces repo
git clone https://huggingface.co/spaces/YOUR-USERNAME/breast-cancer-diagnosis
cd breast-cancer-diagnosis
```

**Thay thế `YOUR-USERNAME` bằng username Hugging Face của bạn**

---

## Bước 4: Copy Files từ GitHub

```bash
# Copy Streamlit app
cp ../DoAnTotNghiep/app_demo.py .

# Copy models
mkdir -p models
cp ../DoAnTotNghiep/backend/app/models/xgboost_biochem.joblib models/
cp ../DoAnTotNghiep/backend/app/models/efficientnet_b0.pth models/

# Copy requirements
cp ../DoAnTotNghiep/requirements.txt .
```

---

## Bước 5: Cấu hình Streamlit

Tạo file `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "minimal"

[logger]
level = "info"
```

---

## Bước 6: Push lên Hugging Face Spaces

```bash
git add .
git commit -m "Add breast cancer diagnosis Streamlit app"
git push
```

✅ **Spaces sẽ tự động build và deploy!** Chờ 2-3 phút.

---

## Bước 7: Xem kết quả

Truy cập: **https://huggingface.co/spaces/YOUR-USERNAME/breast-cancer-diagnosis**

---

## Troubleshooting

### ❌ Models not found
**Giải pháp**: Đảm bảo file `.pth` và `.joblib` nằm trong folder `models/`

### ❌ "ModuleNotFoundError: No module named 'torch'"
**Giải pháp**: Kiểm tra `requirements.txt` có đầy đủ dependencies không

### ❌ "Permission denied"
**Giải pháp**: 
```bash
huggingface-cli whoami
# Nếu chưa login
huggingface-cli login
```

### ❌ Large files (> 10GB)
**Giải pháp**: Dùng Git LFS
```bash
git lfs install
git lfs track "*.pth"
git add .gitattributes
```

---

## 📝 Cấu trúc folder Spaces

```
breast-cancer-diagnosis/
├── app_demo.py                 # Main Streamlit app
├── requirements.txt            # Dependencies
├── .streamlit/
│   └── config.toml            # Streamlit config
├── models/
│   ├── xgboost_biochem.joblib
│   └── efficientnet_b0.pth
└── README.md                  # (optional)
```

---

## 🎥 File Size Check

Trước khi push, kiểm tra kích thước:
```bash
ls -lh models/
# xgboost_biochem.joblib ~ 15 MB
# efficientnet_b0.pth ~ 21 MB
# Total: ~ 36 MB (OK, < 50GB GitHub limit)
```

---

## ✨ Tổng hợp các bước nhanh

```bash
# 1. Login
huggingface-cli login

# 2. Clone Spaces
git clone https://huggingface.co/spaces/YOUR-USERNAME/breast-cancer-diagnosis
cd breast-cancer-diagnosis

# 3. Copy files
cp ../DoAnTotNghiep/app_demo.py .
mkdir -p models
cp ../DoAnTotNghiep/backend/app/models/* models/
cp ../DoAnTotNghiep/requirements.txt .

# 4. Create Streamlit config
mkdir -p .streamlit
echo '[theme]
primaryColor = "#FF6B6B"' > .streamlit/config.toml

# 5. Push
git add .
git commit -m "Add breast cancer diagnosis app"
git push

# 6. ✅ Done! Chờ ~ 2-3 phút để deploy hoàn tất
```

---

## 📸 Demo URL

Sau khi deploy xong:
- **Share link**: https://huggingface.co/spaces/YOUR-USERNAME/breast-cancer-diagnosis
- **Người dùng có thể test trực tiếp mà không cần cài gì!**

---

## 💡 Tips

- **Models quá lớn?** Dùng model quantization để giảm kích thước
- **Muốn GPU?** Hugging Face Spaces có GPU options (Free tier: CPU only)
- **Muốn thêm file?** Push thêm sau, Spaces sẽ tự động rebuild

---

## 📞 Support

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Streamlit Documentation](https://docs.streamlit.io)
