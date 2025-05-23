import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from utils import get_data 
import io

# 默认 ASCII 处理选项
DEFAULT_ASCII_OPTIONS = {
    "language": "chinese",
    "mode": "standard",
    "background": "black",  
    "num_cols": 150,        
}

def convert_image_to_ascii_art(image_bytes_io, options=None):
    current_options = DEFAULT_ASCII_OPTIONS.copy()
    if options:
        current_options.update(options)

    try:
        bg_code = 255 if current_options["background"] == "white" else 0

        char_list, font, sample_character, scale = get_data(current_options["language"], current_options["mode"])
        num_chars = len(char_list)
        num_cols = current_options["num_cols"]

        image_bytes_io.seek(0)
        image_np_array = np.frombuffer(image_bytes_io.read(), np.uint8)
        # 先尝试以彩色模式解码，然后转灰度，以处理不同类型的输入图片
        cv_image = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)
        if cv_image is None:
            # 如果彩色解码失败，尝试灰度解码 (某些单通道图可能需要)
            cv_image = cv2.imdecode(image_np_array, cv2.IMREAD_GRAYSCALE)
            if cv_image is None:
                print("错误: OpenCV 无法从 BytesIO 解码图片。") # 应替换为 app.logger.error
                return None
        
        # 如果图像不是灰度图，则转换
        if len(cv_image.shape) == 3 and cv_image.shape[2] == 3: # BGR
            image_gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        elif len(cv_image.shape) == 3 and cv_image.shape[2] == 4: # BGRA
            image_gray = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2GRAY)
        elif len(cv_image.shape) == 2: # Already Grayscale
             image_gray = cv_image
        else:
            print(f"错误: 不支持的图片通道数: {cv_image.shape}")
            return None
            
        height, width = image_gray.shape

        if width == 0 or height == 0:
            print("错误: 图片宽度或高度为0。")
            return None

        cell_width = width / num_cols
        # 确保 cell_height > 0，scale 也不能是0
        if scale == 0: scale = 1 # 防止 scale 为0
        cell_height = scale * cell_width
        
        if cell_width <= 0 or cell_height <= 0:
            print(f"错误: 计算得到的 cell_width ({cell_width}) 或 cell_height ({cell_height}) 无效。")
            # 尝试调整 num_cols
            if width > 10: # 至少图片要有点宽度
                num_cols = width // 2 # 至少每个 cell 2个像素宽
                if num_cols == 0: num_cols = 1
                cell_width = width / num_cols
                cell_height = scale * cell_width
                if cell_width <= 0 or cell_height <= 0:
                    print("错误: 调整后 cell_width 或 cell_height 仍然无效。")
                    return None
            else:
                print("错误: 图片太小，无法进行有意义的 cell 划分。")
                return None


        num_rows = int(height / cell_height)

        if num_cols > width or num_rows > height or num_rows <= 0:
            print(f"警告: 列数({num_cols})或行数({num_rows})设置可能不合理。原始尺寸: {width}x{height}。")
            # 尝试基于宽度调整 num_cols
            if num_cols > width and width > 0 :
                num_cols = max(1, width // 2) # 保证 cell_width 至少为2，且 num_cols 至少为1
            
            cell_width = width / num_cols
            cell_height = scale * cell_width
            if cell_height <=0 :
                print("错误: 调整后 cell_height 仍然无效。")
                return None
            num_rows = int(height / cell_height)
            
            if num_rows <= 0 or num_cols <= 0:
                print(f"错误: 调整后无法确定有效的行数({num_rows})或列数({num_cols})。")
                return None
            print(f"调整后: num_cols={num_cols}, num_rows={num_rows}")
        
        # 获取字符尺寸 (现代 Pillow 使用 getbbox)
        try:
            # getbbox 返回 (left, top, right, bottom)
            bbox = font.getbbox(sample_character) 
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1] 
            if char_height <= 0 and hasattr(font, 'size'): # 某些字体getbbox可能返回(0,0,w,h)而bbox[1]不为0
                 char_height = font.size # 退回使用字体声明的size
            if char_width <= 0 and hasattr(font, 'size'):
                 char_width = font.size // 2 # 粗略估计
        except AttributeError: # 兼容旧版 Pillow 或自定义字体对象
            if hasattr(font, 'getsize'):
                char_width, char_height = font.getsize(sample_character)
            else:
                print("错误: 无法从字体对象获取字符尺寸。")
                return None
        
        if char_width <= 0 or char_height <= 0:
            print(f"错误: 字符宽度({char_width})或高度({char_height})无效。")
            return None

        out_width = char_width * num_cols
        out_height = char_height * num_rows # 每个字符高 char_height, 共 num_rows 行

        if out_width <= 0 or out_height <= 0:
            print(f"错误: 计算得到的输出图像宽度({out_width})或高度({out_height})无效。")
            return None

        out_image_pil = Image.new("L", (int(out_width), int(out_height)), bg_code)
        draw = ImageDraw.Draw(out_image_pil)

        for i in range(num_rows):
            y_start = int(i * cell_height)
            y_end = min(int((i + 1) * cell_height), height)
            if y_start >= y_end: continue

            character_line = []
            for j in range(num_cols):
                x_start = int(j * cell_width)
                x_end = min(int((j + 1) * cell_width), width)
                if x_start >= x_end: continue
                
                image_cell_slice = image_gray[y_start:y_end, x_start:x_end]
                
                if image_cell_slice.size == 0:
                    char_to_add = char_list[0] if bg_code == 0 else char_list[num_chars - 1]
                else:
                    avg_intensity = np.mean(image_cell_slice)
                    char_idx = min(int((avg_intensity / 255.0) * num_chars), num_chars - 1)
                    char_to_add = char_list[char_idx]
                character_line.append(char_to_add)
            
            line_text = "".join(character_line)
            draw.text((0, i * char_height), line_text, fill=(255 - bg_code), font=font)

        # 裁剪
        bbox = None
        if current_options["background"] == "white":
            # 背景白(255)，文字黑(0)。反色后文字变白(255)，背景变黑(0)，getbbox才能正常工作
            try:
                inverted_for_bbox = ImageOps.invert(out_image_pil.convert("L"))
                bbox = inverted_for_bbox.getbbox()
            except ValueError as ve: # 有时全白图片反色再getbbox会出问题
                print(f"裁剪时发生Value Error (可能图片全白/黑): {ve}")
                bbox = None # 无法裁剪，返回原图
        else: # 背景黑(0)，文字白(255)
            bbox = out_image_pil.getbbox()

        if bbox:
            out_image_pil = out_image_pil.crop(bbox)
        
        return out_image_pil

    except FileNotFoundError as fnfe: # 特别处理 utils.get_data 可能引发的字体文件等找不到的问题
        print(f"文件未找到错误 (可能在 get_data 中): {fnfe}") # 应替换为 app.logger.error
        raise # 重新抛出，让上层Flask路由捕获并返回合适的错误信息
    except Exception as e:
        print(f"ASCII 艺术转换过程中发生错误: {e}") # 应替换为 app.logger.error
        import traceback
        traceback.print_exc()
        return None