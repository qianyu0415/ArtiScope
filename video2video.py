"""
@author: Viet Nguyen <nhviet1009@gmail.com>
Modified for better codec compatibility
"""
import argparse
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageOps


def get_args():
    parser = argparse.ArgumentParser("Image to ASCII")
    parser.add_argument("--input", type=str, default="data/input.mp4", help="Path to input video")
    parser.add_argument("--output", type=str, default="data/output.mp4", help="Path to output video")
    parser.add_argument("--mode", type=str, default="simple", choices=["simple", "complex"],
                        help="10 or 70 different characters")
    parser.add_argument("--background", type=str, default="white", choices=["black", "white"],
                        help="background's color")
    parser.add_argument("--num_cols", type=int, default=100, help="number of character for output's width")
    parser.add_argument("--scale", type=int, default=1, help="upsize output")
    parser.add_argument("--fps", type=int, default=0, help="frame per second")
    parser.add_argument("--overlay_ratio", type=float, default=0.2, help="Overlay width ratio")
    parser.add_argument("--codec", type=str, default="mp4v", help="Video codec (mp4v, avc1, XVID, etc)")
    args = parser.parse_args()
    return args


def main(opt):
    # Character set configuration
    CHAR_LIST = '@%#*+=-:. ' if opt.mode == "simple" else \
               "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    
    bg_code = 255 if opt.background == "white" else 0
    font = ImageFont.truetype("fonts/DejaVuSansMono-Bold.ttf", size=int(10 * opt.scale))

    # Video capture setup
    cap = cv2.VideoCapture(opt.input)
    if not cap.isOpened():
        raise IOError("Could not open video file")
    
    fps = opt.fps if opt.fps != 0 else int(cap.get(cv2.CAP_PROP_FPS))
    num_chars = len(CHAR_LIST)

    # Get first frame to initialize VideoWriter
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Could not read first frame")
    
    # Initialize VideoWriter with proper dimensions
    sample_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = sample_image.shape
    
    # Calculate ASCII art dimensions
    num_cols = opt.num_cols  # 确保num_cols被正确定义
    cell_width = width / opt.num_cols
    cell_height = 2 * cell_width
    num_rows = int(height / cell_height)
    
    if num_cols > width or num_rows > height:
        print("Too many columns or rows. Using default settings")
        cell_width = 6
        cell_height = 12
        num_cols = int(width / cell_width)
        num_rows = int(height / cell_height)
    
    char_width, char_height = font.getsize("A")
    out_width = char_width * num_cols
    out_height = 2 * char_height * num_rows
    
    # Initialize VideoWriter with compatible codec
    fourcc = cv2.VideoWriter_fourcc(*opt.codec)
    out = cv2.VideoWriter(opt.output, fourcc, fps, (out_width, out_height))
    if not out.isOpened():
        raise IOError("Could not initialize VideoWriter with codec: {}".format(opt.codec))

    # Process frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to ASCII
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ascii_image = Image.new("L", (out_width, out_height), bg_code)
        draw = ImageDraw.Draw(ascii_image)
        
        for i in range(num_rows):
            line = "".join([CHAR_LIST[min(int(np.mean(
                gray[int(i * cell_height):min(int((i + 1) * cell_height), height),
                     int(j * cell_width):min(int((j + 1) * cell_width), width)]) * num_chars / 255), 
                num_chars - 1)] for j in range(num_cols)]) + "\n"
            draw.text((0, i * char_height), line, fill=255 - bg_code, font=font)
        
        # Crop and convert
        # crop_box = ImageOps.invert(ascii_image).getbbox() if opt.background == "white" else ascii_image.getbbox()
        # final_image = cv2.cvtColor(np.array(ascii_image.crop(crop_box)), cv2.COLOR_GRAY2BGR)
        
        final_image = cv2.cvtColor(np.array(ascii_image), cv2.CoLOR_GRAY2RGR)
        # Add overlay if specified
        if opt.overlay_ratio > 0:
            h, w = final_image.shape[:2] # 现在 h=out_height, w=out_width
            overlay_h = int(h * opt.overlay_ratio)
            overlay_w = int(w * opt.overlay_ratio)
            overlay = cv2.resize(frame, (overlay_w, overlay_h))
            # 将叠加层放在完整帧的右下角
            final_image[h - overlay_h:, w - overlay_w:] = overlay
        out.write(final_image)

    # Cleanup
    cap.release()
    out.release()
    print(f"Video processing complete. Output saved to {opt.output}")


if __name__ == '__main__':
    opt = get_args()
    main(opt)
