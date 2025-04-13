import numpy as np
from PIL import Image


def floyd_steinberg_dithering(image, max_size, mode='RGB'):
    # 如果输入图像是RGBA，则转换为RGB
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # 计算新尺寸，保持长宽比
    aspect_ratio = image.width / image.height
    if aspect_ratio > 1:  # 宽图
        new_width = max_size
        new_height = int(max_size / aspect_ratio)
    else:  # 瘦图或正方形
        new_height = max_size
        new_width = int(max_size * aspect_ratio)

    # 调整输出尺寸
    image = np.array(image.resize((new_width, new_height), Image.NEAREST)) / 255.0
    height, width, _ = image.shape

    if mode == 'RGB':
        # 应用Floyd-Steinberg抖动（RGB模式）
        dithered_image = np.zeros((height, width, 3), dtype=np.uint8)  # 使用uint8类型
        for i in range(height):
            for j in range(width):
                for c in range(3):  # 处理每个颜色通道
                    gray_value = image[i, j, c]
                    new_value = 255 if gray_value > 0.5 else 0
                    dithered_image[i, j, c] = new_value

                    # 计算误差
                    error = gray_value - new_value / 255.0

                    # 传播误差到相邻像素
                    if j + 1 < width:
                        image[i, j + 1, c] += error * 7 / 16
                    if i + 1 < height:
                        if j > 0:
                            image[i + 1, j - 1, c] += error * 3 / 16
                        image[i + 1, j, c] += error * 5 / 16
                        if j + 1 < width:
                            image[i + 1, j + 1, c] += error * 1 / 16
        return dithered_image  # 返回RGB图像

    else:  # BW模式
        # 应用Floyd-Steinberg抖动（黑白模式）
        dithered_image = np.zeros((height, width), dtype=np.uint8)  # 使用uint8类型
        for i in range(height):
            for j in range(width):
                gray_value = np.mean(image[i, j])  # 计算灰度值
                new_value = 255 if gray_value > 0.5 else 0
                dithered_image[i, j] = new_value

                # 计算误差
                error = gray_value - new_value / 255.0

                # 传播误差到相邻像素
                if j + 1 < width:
                    image[i, j + 1] += error * 7 / 16
                if i + 1 < height:
                    if j > 0:
                        image[i + 1, j - 1] += error * 3 / 16
                    image[i + 1, j] += error * 5 / 16
                    if j + 1 < width:
                        image[i + 1, j + 1] += error * 1 / 16

        return np.stack([dithered_image] * 3, axis=-1)  # 返回三通道的黑白图像


# 使用示例
image = Image.open('9d4f0be562a28bb6c88c7e25980646aa.jpg')  # 从文件读取图像
output_image = floyd_steinberg_dithering(image, 256, mode='bw')  # 最大尺寸为1024，黑白模式

# 保存输出图像
Image.fromarray(output_image).save('output_image.png')
