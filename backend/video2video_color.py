"""
@author: Viet Nguyen <nhviet1009@gmail.com>
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
    parser.add_argument("--mode", type=str, default="complex", choices=["simple", "complex"],
                        help="10 or 70 different characters")
    parser.add_argument("--background", type=str, default="black", choices=["black", "white"],
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
    
    # Set background color
    bg_code = (255, 255, 255) if opt.background == "white" else (0, 0, 0)
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
    num_cols = opt.num_cols

    # Get first frame to initialize dimensions
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Could not read first frame")
    
    initial_height, initial_width, _ = frame.shape
    if initial_width <= 0 or initial_height <= 0:
        raise ValueError(f"Invalid video dimensions: width={initial_width}, height={initial_height}")
    if num_cols <= 0:
        raise ValueError(f"Invalid num_cols: {num_cols}")
    
    cell_width = initial_width / num_cols
    cell_height = 2 * cell_width
    num_rows = int(initial_height / cell_height)
    
    if num_cols > initial_width or num_rows > initial_height or num_cols <= 0 or num_rows <= 0:
        print("Too many columns or rows. Using default settings")
        cell_width = 6
        cell_height = 12
        num_cols = int(initial_width / cell_width)
        num_rows = int(initial_height / cell_height)
    
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
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        print(f"Processing frame {frame_count}, frame shape: {frame.shape}")
        
        # Verify frame dimensions
        if frame.shape[:2] != (initial_height, initial_width):
            print(f"Warning: Frame {frame_count} shape {frame.shape} differs from initial {initial_height, initial_width}")
            frame = cv2.resize(frame, (initial_width, initial_height))
        
        # Create new ASCII art image for each frame
        out_image = Image.new("RGB", (out_width, out_height), bg_code)
        draw = ImageDraw.Draw(out_image)
        
        for i in range(num_rows):
            for j in range(num_cols):
                partial_image = frame[int(i * cell_height):min(int((i + 1) * cell_height), initial_height),
                                    int(j * cell_width):min(int((j + 1) * cell_width), initial_width), :]
                if partial_image.size == 0:
                    char = CHAR_LIST[0]
                    partial_avg_color = (255, 0, 0)  # Force red for visibility
                else:
                    partial_avg_color = np.sum(np.sum(partial_image, axis=0), axis=0) / (cell_height * cell_width)
                    if np.any(np.isnan(partial_avg_color)) or np.all(partial_avg_color == 0):
                        partial_avg_color = (255, 0, 0)  # Force red if invalid
                    else:
                        partial_avg_color = tuple(np.clip(partial_avg_color, 0, 255).astype(np.int32).tolist())
                    char_idx = min(int(np.mean(partial_image) * num_chars / 255), num_chars - 1)
                    char = CHAR_LIST[char_idx]
                draw.text((j * char_width, i * char_height), char, fill=partial_avg_color, font=font)

        # Convert to numpy array
        out_image_np = np.array(out_image)
        print(f"Output image shape: {out_image_np.shape}, min: {np.min(out_image_np)}, max: {np.max(out_image_np)}")
        
        # Add overlay if specified
        if opt.overlay_ratio:
            height, width, _ = out_image_np.shape
            target_width = max(1, min(int(width * opt.overlay_ratio), width - 10))  # Leave margin
            target_height = max(1, min(int(height * opt.overlay_ratio), height - 10))  # Leave margin
            print(f"Target overlay size: ({target_width}, {target_height})")
            if target_width > 0 and target_height > 0:
                overlay = cv2.resize(frame, (target_width, target_height))
                print(f"Overlay shape: {overlay.shape}")
                if overlay.shape[:2] == (target_height, target_width):
                    # Apply overlay with margin to avoid covering main content
                    out_image_np[height - target_height - 5:height - 5, width - target_width - 5:width - 5, :] = overlay
                else:
                    print(f"Warning: Overlay dimensions {overlay.shape} do not match expected ({target_height}, {target_width})")
            else:
                print(f"Warning: Invalid overlay size, skipping overlay")
        
        out.write(out_image_np)

    # Cleanup and flush
    out.release()
    cap.release()
    if os.path.exists(temp_avi_path):
        with open(temp_avi_path, 'rb') as f:
            f.flush()

    # Convert .avi to .mp4 using moviepy
    try:
        video_clip = VideoFileClip(temp_avi_path)
        print(f"Converting {temp_avi_path} to {opt.output}, duration: {video_clip.duration}")
        video_clip.write_videofile(opt.output, codec="libx264", audio_codec="aac", logger=None)
        video_clip.close()
        os.remove(temp_avi_path)
    except Exception as e:
        raise RuntimeError(f"Moviepy conversion failed: {e}")

    print(f"Video processing complete. Output saved to {opt.output}")


if __name__ == '__main__':
    opt = get_args()
    main(opt)