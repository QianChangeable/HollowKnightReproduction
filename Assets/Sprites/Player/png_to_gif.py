import argparse
import os
from PIL import Image

def create_gif(input_folder, output_file, duration=200):
    # 获取文件夹中所有PNG文件并按文件名排序
    png_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.png')])
    
    if not png_files:
        print("错误：未找到PNG图片文件")
        return

    images = []
    try:
        # 打开并存储所有图片
        for file in png_files:
            img_path = os.path.join(input_folder, file)
            with Image.open(img_path) as img:
                # 确保图片转换为RGB模式（兼容GIF格式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img.copy())
    except Exception as e:
        print(f"打开图片时发生错误：{str(e)}")
        return

    # 保存为GIF
    try:
        images[0].save(
            output_file,
            save_all=True,
            append_images=images[1:],
            optimize=False,
            duration=duration,
            loop=0
        )
        print(f"成功生成GIF文件：{output_file}")
    except Exception as e:
        print(f"保存GIF时发生错误：{str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将PNG图片合并为GIF动画')
    parser.add_argument('input_folder', help='输入文件夹路径')
    parser.add_argument('output_file', help='输出GIF文件路径')
    parser.add_argument('--duration', type=int, default=200, 
                       help='每帧持续时间（毫秒），默认200ms')
    
    args = parser.parse_args()

    # 检查输入文件夹是否存在
    if not os.path.isdir(args.input_folder):
        print(f"错误：输入路径 {args.input_folder} 不是有效文件夹")
        exit(1)

    create_gif(args.input_folder, args.output_file, args.duration)