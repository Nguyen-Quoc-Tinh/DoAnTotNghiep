# 🏥 Hệ thống Chẩn Đoán Ung Thư Vú

## Mục tiêu
Xây dựng hệ thống chẩn đoán bệnh ung thư vú bằng chỉ số sinh hóa và hình ảnh mô học.

### 1. Chẩn đoán bằng Chỉ số Sinh hóa
- ✅ Model: XGBoost (98.67% accuracy)
- ✅ Input: 30 chỉ số sinh hóa (từ xét nghiệm FNA)
- ✅ Status: Production ready
- 📁 Model: model.joblib

### 2. Chẩn đoán bằng Hình ảnh Y khoa (Histopathology)
 - ✅ Model: EfficientNet-B0 (Transfer Learning, 92.54% val accuracy)
 - ✅ Input: Ảnh mô học (224x224, PNG/JPG)
 - 🔄 Đang tối ưu hóa model deep learning
 - 📁 Dataset: Breast cancer histopathology images (data/images/)

## 📋 Tình trạng hiện tại
 - ✅ Hoàn thành:
   - Chức năng 1: Chẩn đoán bằng chỉ số sinh hóa (XGBoost 98.67%)
   - 🔍 Giải thích mô hình
   -SHAP: Đã có script explain_xgboost.py (scripts/) để giải thích đặc trưng mô hình XGBoost.
 
- Chức năng 2: Chẩn đoán bằng hình ảnh mô học EfficientNet-B0
  -Grad-CAM: Đã có script gradcam_efficientnet_b0.py (scripts/) để tạo Grad-CAM cho mô hình deep learning (EfficientNet-B0/ResNet-18).

#Độ chính xác của từng mô hình trong dự án như sau:

-XGBoost (chỉ số sinh hóa): 98.67% (rất cao, đã kiểm chứng trên bộ dữ liệu WDBC, giá trị này là chính xác, không phải ước lượng).


-EfficientNet-B0 (hình ảnh mô học): 92.54% (độ chính xác trên tập validation, giá trị này cũng là kết quả thực tế sau huấn luyện).


#Data :
-Dữ liệu chỉ số sinh hóa (biochemical):
-Tên file: wdbc.csv
-Nguồn: Wisconsin Diagnostic Breast Cancer (WDBC) dataset
-Nội dung: 569 mẫu, mỗi mẫu gồm 30 chỉ số sinh hóa (từ xét nghiệm FNA) và nhãn (benign/malignant).
-Dữ liệu hình ảnh mô học (histopathology images):
-Thư mục: data/images/
-Nguồn: Breast cancer histopathology images dataset
-Nội dung: Các thư mục con chứa ảnh mô học (định dạng PNG/JPG), đã chia thành các folder theo ID bệnh nhân hoặc theo train/val.

-Dữ liệu chỉ số sinh hóa (WDBC):
-Có thể tải từ Kaggle:
https://archive.ics.uci.edu/ml/datasets/Breast+Cancer+Wisconsin+(Diagnostic)
Script download_dataset.py sẽ tự động tải về và lưu thành data/wdbc.csv.](https://www.kaggle.com/datasets/uciml/breast-cancer-wisconsin-data)


-Dữ liệu hình ảnh mô học:
Nguồn phổ biến:
https://www.kaggle.com/datasets/paultimothymooney/breast-histopathology-images
Script scripts/download_image_dataset.py (hoặc hướng dẫn trong đó) sẽ giúp bạn tải về và giải nén vào data/images/.
