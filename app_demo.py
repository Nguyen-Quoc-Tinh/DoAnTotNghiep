"""
Streamlit Demo - Hệ thống chẩn đoán ung thư vú
Chạy: streamlit run app_demo.py
"""

import streamlit as st
import numpy as np
from PIL import Image
import torch
from torchvision import models, transforms
import joblib
import os
from pathlib import Path

# Config Streamlit
st.set_page_config(
    page_title="🏥 Chẩn đoán ung thư vú",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Hệ thống hỗ trợ chẩn đoán ung thư vú")
st.markdown("**Multi-Modal AI System** - Dự đoán từ dữ liệu sinh hóa & ảnh mô học")

# Set device
device = torch.device("cpu")

# Load models
@st.cache_resource
def load_models():
    """Load XGBoost và EfficientNet models"""
    try:
        # Load XGBoost
        xgboost_path = "backend/app/models/xgboost_biochem.joblib"
        xgboost_model = joblib.load(xgboost_path)
        
        # Load EfficientNet
        efficientnet_path = "backend/app/models/efficientnet_b0.pth"
        efficientnet = models.efficientnet_b0(pretrained=False)
        efficientnet.classifier[1] = torch.nn.Linear(1280, 2)
        
        state_dict = torch.load(efficientnet_path, map_location=device)
        if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
            state_dict = state_dict['model_state_dict']
        efficientnet.load_state_dict(state_dict)
        efficientnet.eval()
        efficientnet.to(device)
        
        return xgboost_model, efficientnet
    except Exception as e:
        st.error(f"❌ Lỗi tải models: {str(e)}")
        return None, None

xgboost_model, efficientnet = load_models()

if xgboost_model is None or efficientnet is None:
    st.error("⚠️ Không thể tải models. Vui lòng kiểm tra đường dẫn file.")
    st.stop()

# Sidebar - Info
with st.sidebar:
    st.header("ℹ️ Thông tin")
    st.markdown("""
    ### Mô hình sử dụng:
    - **XGBoost**: 30 chỉ số sinh hóa → Dự đoán lành/ác tính
    - **EfficientNet-B0**: Ảnh mô học → Dự đoán lành/ác tính
    
    ### Độ chính xác:
    - XGBoost: **98.67%** trên WDBC dataset
    - EfficientNet-B0: **~92%** trên ảnh mô học
    """)
    
    st.markdown("---")
    st.markdown("""
    **📢 Lưu ý:**
    - Đây là hệ thống hỗ trợ, không phải thay thế chẩn đoán lâm sàng
    - Cần xác nhận bởi bác sĩ chuyên môn
    - Dùng cho mục đích giáo dục/nghiên cứu
    """)

# Main tabs
tab1, tab2, tab3 = st.tabs(["📊 Chẩn đoán sinh hóa", "🖼️ Chẩn đoán ảnh", "📈 Thông tin hệ thống"])

# ============ TAB 1: XGBoost - Dữ liệu sinh hóa ============
with tab1:
    st.subheader("Chẩn đoán từ 30 chỉ số sinh hóa")
    st.info("**Hướng dẫn**: Nhập các giá trị chỉ số sinh hóa từ kết quả xét nghiệm FNA (Fine Needle Aspiration)")
    
    feature_names = [
        "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
        "compactness_mean", "concavity_mean", "concave_points_mean", "symmetry_mean", "fractal_dimension_mean",
        "radius_se", "texture_se", "perimeter_se", "area_se", "smoothness_se",
        "compactness_se", "concavity_se", "concave_points_se", "symmetry_se", "fractal_dimension_se",
        "radius_worst", "texture_worst", "perimeter_worst", "area_worst", "smoothness_worst",
        "compactness_worst", "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
    ]
    
    # Input form
    st.subheader("📝 Nhập dữ liệu")
    col1, col2, col3 = st.columns(3)
    features = []
    
    for i, name in enumerate(feature_names):
        col = [col1, col2, col3][i % 3]
        with col:
            value = st.number_input(
                name.replace("_", " ").title(),
                value=0.0,
                format="%.2f",
                key=f"biochem_{i}"
            )
            features.append(value)
    
    # Prediction
    col_pred, col_clear = st.columns(2)
    
    with col_pred:
        if st.button("🔍 Dự đoán", key="predict_biochem", use_container_width=True):
            features_array = np.array(features).reshape(1, -1)
            
            try:
                scaler = xgboost_model['scaler']
                model = xgboost_model['model']
                
                features_scaled = scaler.transform(features_array)
                proba_malignant = model.predict_proba(features_scaled)[0, 1]
                
                prediction = "Ác tính ⚠️" if proba_malignant >= 0.5 else "Lành tính ✅"
                confidence = max(proba_malignant, 1 - proba_malignant)
                
                st.success(f"### Kết quả: **{prediction}**")
                st.metric("Xác suất ác tính", f"{proba_malignant:.2%}", 
                         f"Độ tin cậy: {confidence:.2%}")
                
                # Visual result
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Xác suất từng lớp:**")
                    st.bar_chart({
                        "Lành tính": 1 - proba_malignant,
                        "Ác tính": proba_malignant
                    })
                
                with col_b:
                    st.write("**Kết luận:**")
                    if proba_malignant >= 0.7:
                        st.error("🔴 **Nguy cơ cao** - Cần tư vấn bác sĩ ngay")
                    elif proba_malignant >= 0.3:
                        st.warning("🟡 **Nguy cơ trung bình** - Nên theo dõi")
                    else:
                        st.success("🟢 **Nguy cơ thấp** - Tiếp tục theo dõi định kỳ")
                        
            except Exception as e:
                st.error(f"❌ Lỗi dự đoán: {str(e)}")
    
    with col_clear:
        if st.button("🔄 Làm mới", key="clear_biochem", use_container_width=True):
            st.rerun()


# ============ TAB 2: EfficientNet - Ảnh mô học ============
with tab2:
    st.subheader("Chẩn đoán từ ảnh mô học")
    st.info("**Hướng dẫn**: Tải ảnh mô học (histopathology) để hệ thống phân tích")
    
    uploaded_file = st.file_uploader(
        "📁 Chọn ảnh",
        type=["jpg", "jpeg", "png"],
        key="image_upload"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file).convert("RGB")
        
        col_img, col_info = st.columns([2, 1])
        
        with col_img:
            st.image(image, caption="Ảnh được tải lên", width=400)
        
        with col_info:
            st.write("**Thông tin ảnh:**")
            st.write(f"- Kích thước: {image.size}")
            st.write(f"- Format: {image.format}")
        
        # Prediction
        col_pred, col_clear = st.columns(2)
        
        with col_pred:
            if st.button("🔍 Phân tích ảnh", key="predict_image", use_container_width=True):
                try:
                    # Preprocess
                    transform = transforms.Compose([
                        transforms.Resize((224, 224)),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            [0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225]
                        )
                    ])
                    
                    input_tensor = transform(image).unsqueeze(0).to(device)
                    
                    # Inference
                    with torch.no_grad():
                        output = efficientnet(input_tensor)
                        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
                    
                    pred_idx = np.argmax(probs)
                    pred_label = ["Lành tính ✅", "Ác tính ⚠️"][pred_idx]
                    confidence = probs[pred_idx]
                    
                    st.success(f"### Kết quả: **{pred_label}**")
                    st.metric("Độ tin cậy", f"{confidence:.2%}")
                    
                    # Visual
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write("**Xác suất từng lớp:**")
                        chart_data = {
                            "Lành tính": probs[0],
                            "Ác tính": probs[1]
                        }
                        st.bar_chart(chart_data)
                    
                    with col_b:
                        st.write("**Kết luận:**")
                        if probs[1] >= 0.7:
                            st.error("🔴 **Nguy cơ cao** - Cần tư vấn bác sĩ ngay")
                        elif probs[1] >= 0.3:
                            st.warning("🟡 **Nguy cơ trung bình** - Nên theo dõi")
                        else:
                            st.success("🟢 **Nguy cơ thấp** - Tiếp tục theo dõi định kỳ")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi phân tích: {str(e)}")
        
        with col_clear:
            if st.button("🔄 Làm mới", key="clear_image", use_container_width=True):
                st.rerun()


# ============ TAB 3: Thông tin hệ thống ============
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Model XGBoost")
        st.markdown("""
        **Đặc điểm:**
        - Input: 30 chỉ số sinh hóa từ FNA test
        - Algorithm: XGBoost Classifier
        - Preprocessing: StandardScaler
        
        **Hiệu suất:**
        - Accuracy: **98.67%**
        - ROC AUC: **0.9986**
        - Dataset: WDBC (569 samples)
        
        **Chỉ số được sử dụng:**
        - Radius, Texture, Perimeter, Area
        - Smoothness, Compactness, Concavity
        - Concave Points, Symmetry, Fractal Dimension
        - (Mỗi chỉ số có 3 biến: mean, se, worst)
        """)
        
    with col2:
        st.subheader("🖼️ Model EfficientNet-B0")
        st.markdown("""
        **Đặc điểm:**
        - Input: Ảnh mô học 224×224 RGB
        - Architecture: EfficientNet-B0
        - Transfer Learning: ImageNet pretrained
        - Output: 2 classes (Benign/Malignant)
        
        **Hiệu suất:**
        - Validation Accuracy: **~92%**
        - Framework: PyTorch
        - Optimized: RTX 3050 4GB VRAM
        
        **Tiền xử lý:**
        - Resize: 224×224
        - Normalize: ImageNet stats
        - Data Augmentation: Trong training
        """)
    
    st.markdown("---")
    
    st.subheader("📊 Stack Công nghệ")
    tech_cols = st.columns(3)
    
    with tech_cols[0]:
        st.markdown("""
        **Backend:**
        - FastAPI
        - MongoDB
        - PyTorch
        - scikit-learn
        """)
    
    with tech_cols[1]:
        st.markdown("""
        **Frontend:**
        - React + TypeScript
        - Vite
        - Responsive UI
        """)
    
    with tech_cols[2]:
        st.markdown("""
        **ML Libraries:**
        - XGBoost
        - EfficientNet
        - SHAP (Explainability)
        """)
    
    st.markdown("---")
    st.markdown("""
    ## 📞 Liên hệ & Thông tin
    
    - **GitHub**: [Nguyen-Quoc-Tinh/DoAnTotNghiep](https://github.com/Nguyen-Quoc-Tinh/DoAnTotNghiep)
    - **Mục đích**: Hỗ trợ chẩn đoán ung thư vú - Công cụ giáo dục
    - **Lưu ý**: Cần xác nhận lâm sàng bởi bác sĩ chuyên môn
    
    **Đơn vị phát triển**: Công nghệ thông tin y tế
    """)
