# 🏥 Hệ thống Chẩn Đoán Ung Thư Vú

## Mục tiêu
Xây dựng hệ thống chẩn đoán bệnh ung thư vú bằng chỉ số sinh hóa và hình ảnh mô học.

### 1. Chẩn đoán bằng Chỉ số Sinh hóa
- ✅ Model: XGBoost (98.67% accuracy)
- ✅ Input: 30 chỉ số sinh hóa (từ xét nghiệm FNA)
- ✅ Status: Production ready
- 📁 Model: model.joblib

### 2. Chẩn đoán bằng Hình ảnh Y khoa (Histopathology)
- ✅ Model: ResNet-18 (Transfer Learning, 85-90% accuracy)
- ✅ Input: Ảnh mô học (224x224, PNG/JPG)
- 🔄 Đang tối ưu hóa model deep learning
- 📁 Dataset: Breast cancer histopathology images (data/images/)

## 📋 Tình trạng hiện tại
- ✅ Hoàn thành:
  - Chức năng 1: Chẩn đoán bằng chỉ số sinh hóa (XGBoost 98.67%)
- 🔄 Đang phát triển:
  - Chức năng 2: Chẩn đoán bằng hình ảnh mô học (ResNet-18, đang tối ưu)
