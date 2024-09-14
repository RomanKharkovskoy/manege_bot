import cv2
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array

model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

def extract_features(image):
    image = cv2.resize(image, (224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)

    features = model.predict(image)
    return features.flatten()

def check_image(ideal_image_path, uploaded_image_path):
    reference_image = cv2.imread(ideal_image_path)
    uploaded_image = cv2.imread(uploaded_image_path)
    
    if reference_image is None:
        print(f"Эталонное изображение {ideal_image_path} не найдено.")
        return False

    reference_features = extract_features(reference_image)
    uploaded_features = extract_features(uploaded_image)

    similarity = np.dot(reference_features, uploaded_features) / (
        np.linalg.norm(reference_features) * np.linalg.norm(uploaded_features)
    )

    threshold = 0.55 

    return similarity > threshold
