"""
@author: Viet Nguyen <nhviet1009@gmail.com>
Modified for better codec compatibility using moviepy
"""
import argparse
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageOps
import os
# import moviepy
from moviepy.editor import VideoFileClip

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
    font_size = int(10 * opt.scale)
    font_path = "fonts/DejaVuSansMono-Bold.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")
    font = ImageFont.truetype(font_path, size=font_size)

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
    
    # Validate inputs
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid video dimensions: width={width}, height={height}")
    if opt.num_cols <= 0:
        raise ValueError(f"Invalid num_cols: {opt.num_cols}")
    
    # Calculate ASCII art dimensions
    num_cols = opt.num_cols
    cell_width = width / num_cols
    cell_height = 2 * cell_width
    num_rows = int(height / cell_height)
    
    if num_cols > width or num_rows > height or num_cols <= 0 or num_rows <= 0:
        print("Too many columns or rows. Using default settings")
        cell_width = 6
        cell_height = 12
        num_cols = int(width / cell_width)
        num_rows = int(height / cell_height)
    
    left, top, right, bottom = font.getbbox("A")
    char_width, char_height = right - left, bottom - top
    out_width = char_width * num_cols
    out_height = 2 * char_height * num_rows
    
    # Temporary .avi output
    temp_avi_path = opt.output.replace('.mp4', '_temp.avi')
    fourcc = cv2.VideoWriter_fourcc(*opt.codec)
    out = cv2.VideoWriter(temp_avi_path, fourcc, fps, (out_width, out_height))
    if not out.isOpened():
        raise IOError("Could not initialize VideoWriter with codec: {}".format(opt.codec))

    # Process frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        print(f"Processing frame {frame_count}, shape: {frame.shape}")
        
        # Convert to ASCII
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ascii_image = Image.new("L", (out_width, out_height), bg_code)
        draw = ImageDraw.Draw(ascii_image)
        
        for i in range(num_rows):
            line = ""
            for j in range(num_cols):
                partial_image = gray[int(i * cell_height):min(int((i + 1) * cell_height), height),
                                    int(j * cell_width):min(int((j + 1) * cell_width), width)]
                if partial_image.size == 0:
                    char_idx = 0
                else:
                    mean_val = np.mean(partial_image)
                    if np.isnan(mean_val):
                        char_idx = 0
                    else:
                        char_idx = min(int(mean_val * num_chars / 255), num_chars - 1)
                line += CHAR_LIST[char_idx]
            line += "\n"
            draw.text((0, i * char_height), line, fill=255 - bg_code, font=font)
        
        # Convert to BGR for video output
        final_image = cv2.cvtColor(np.array(ascii_image), cv2.COLOR_GRAY2RGB)
        print(f"Final image shape: {final_image.shape}, min: {np.min(final_image)}, max: {np.max(final_image)}")
        
        # Add overlay if specified
        if opt.overlay_ratio > 0:
            h, w = final_image.shape[:2]
            overlay_h = int(h * opt.overlay_ratio)
            overlay_w = int(w * opt.overlay_ratio)
            overlay = cv2.resize(frame, (overlay_w, overlay_h))
            final_image[h - overlay_h:, w - overlay_w:] = overlay
        
        out.write(final_image)

    # Cleanup
    cap.release()
    out.release()

    # Convert .avi to .mp4 using moviepy
    try:
        video_clip = VideoFileClip(temp_avi_path)
        video_clip.write_videofile(opt.output, codec="libx264", audio_codec="aac", logger=None)
        video_clip.close()
        os.remove(temp_avi_path)  # Remove temporary .avi file
    except Exception as e:
        raise RuntimeError(f"Moviepy conversion failed: {e}")

    print(f"Video processing complete. Output saved to {opt.output}")


if __name__ == '__main__':
    opt = get_args()
    main(opt)