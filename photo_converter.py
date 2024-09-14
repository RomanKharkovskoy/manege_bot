import os
from PIL import Image

folders_to_convert = ['ideal_images', 'quest_images']

def convert_images_to_jpg(base_folder):
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.lower().endswith('.jfif'):
                file_path = os.path.join(root, file)
                new_file_path = os.path.splitext(file_path)[0] + '.jpg'  
                try:
                    with Image.open(file_path) as img:
                        img = img.convert('RGB')  
                        img.save(new_file_path, 'JPEG')
                    print(f'Конвертировано: {file_path} -> {new_file_path}')

                    os.remove(file_path)
                except Exception as e:
                    print(f'Ошибка при конвертации {file_path}: {e}')

for folder in folders_to_convert:
    convert_images_to_jpg(folder)
