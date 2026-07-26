import cv2
import torch
import torch.nn.functional as F
import numpy as np
from transformers import pipeline
from PIL import Image
import os
import subprocess
import shutil

def predict_seamless_360_depth(depth_pipe, frame_bgr, pad_percent=0.15):
    """
    Pads equirectangular image horizontally in a circular wrap before running AI depth inference.
    This ensures the AI sees continuous border context and eliminates the 0°/360° seam in VR.
    """
    rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, c = rgb_frame.shape
    pad_w = int(w * pad_percent)

    # Horizontally circular-wrap the frame (left <-> right)
    padded_np = np.pad(rgb_frame, ((0, 0), (pad_w, pad_w), (0, 0)), mode='wrap')
    padded_pil = Image.fromarray(padded_np)

    # Run Depth Anything V2 Inference
    result = depth_pipe(padded_pil)
    depth_padded = np.array(result["depth"])

    # Crop off the circular padding to restore exact original width
    depth_cropped = depth_padded[:, pad_w:-pad_w]
    return depth_cropped

def synthesize_right_eye_360(frame_bgr, depth_map, disparity_factor=0.018, device="cuda"):
    """
    Synthesizes a stereoscopic Right Eye 360 view from the Left Eye (original) frame and Depth Map
    using GPU-accelerated Depth-Based Image Rendering (DIBR) with seamless 360 circular wrapping.
    """
    h, w, c = frame_bgr.shape
    
    # Smooth depth map slightly to eliminate sharp mesh-tearing artifacts at edges
    depth_blurred = cv2.GaussianBlur(depth_map.astype(np.float32), (7, 7), 0)
    
    # Normalize depth map to range [0.0, 1.0] (1.0 = near, 0.0 = far)
    depth_min, depth_max = depth_blurred.min(), depth_blurred.max()
    if depth_max > depth_min:
        depth_norm = (depth_blurred - depth_min) / (depth_max - depth_min)
    else:
        depth_norm = np.zeros_like(depth_blurred)
        
    # Convert RGB image and Depth map to PyTorch CUDA tensors
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img_tensor = torch.from_numpy(frame_rgb).permute(2, 0, 1).unsqueeze(0).float().to(device) / 255.0
    depth_tensor = torch.from_numpy(depth_norm).unsqueeze(0).unsqueeze(0).float().to(device)
    
    # Calculate pixel shift per pixel (closer objects shift more to simulate Inter-Ocular Distance)
    max_shift_px = w * disparity_factor
    shift_x = depth_tensor * max_shift_px
    
    # Generate target coordinate grid for PyTorch grid_sample
    grid_y, grid_x = torch.meshgrid(
        torch.arange(h, device=device, dtype=torch.float32),
        torch.arange(w, device=device, dtype=torch.float32),
        indexing='ij'
    )
    
    # Calculate Right Eye source pixel positions with 360 degree circular horizontal wrapping
    src_x = torch.remainder(grid_x + shift_x.squeeze(), w)
    
    # Normalize pixel coordinates to range [-1, 1] for grid_sample
    norm_x = (src_x / (w - 1.0)) * 2.0 - 1.0
    norm_y = (grid_y / (h - 1.0)) * 2.0 - 1.0
    
    grid = torch.stack((norm_x, norm_y), dim=-1).unsqueeze(0)
    
    # Sample right eye view using GPU bilinear interpolation
    right_eye_tensor = F.grid_sample(img_tensor, grid, mode='bilinear', padding_mode='border', align_corners=True)
    
    # Convert PyTorch tensor back to OpenCV BGR frame
    right_eye_np = (right_eye_tensor.squeeze().permute(1, 2, 0).cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
    right_eye_bgr = cv2.cvtColor(right_eye_np, cv2.COLOR_RGB2BGR)
    return right_eye_bgr

def create_lossless_ffmpeg_writer(output_path, width, height, fps):
    """
    Spawns an FFmpeg pipe to write near-lossless H.264 video directly from raw frame streams.
    Redirects stderr to DEVNULL to prevent Windows pipe deadlocks.
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',                           # Overwrite output file
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'bgr24',            # OpenCV raw BGR input format
        '-r', str(fps),
        '-i', '-',                      # Read from stdin pipe
        '-c:v', 'libx264',              # H.264 Codec
        '-crf', '15',                   # High Quality VR Player Compatible
        '-preset', 'medium',
        '-pix_fmt', 'yuv420p',          # Standard VR player compatible pixel format
        output_path
    ]
    
    try:
        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return process, "ffmpeg"
    except Exception as e:
        print(f"Notice: FFmpeg CLI not found ({e}). Falling back to OpenCV VideoWriter.")
        return None, "opencv"

def process_360_video(input_path, output_path, disparity_strength=0.018):
    print("Loading AI Depth Model (Depth Anything V2 - Base)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using Compute Device: {device.upper()}")
    
    try:
        depth_pipe = pipeline(
            task="depth-estimation", 
            model="depth-anything/Depth-Anything-V2-Base-hf", 
            device=device
        )
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # VR 3D 360 Top/Bottom (Over/Under) Format: 
    # Top = Left Eye 360 RGB (Original)
    # Bottom = Right Eye 360 RGB (Synthesized via AI DIBR)
    out_width = width
    out_height = height * 2

    print(f"Processing 360° Stereoscopic VR Video ({total_frames} frames).")
    print(f"Output Resolution (Top/Bottom 3D 360): {out_width}x{out_height}")

    ffmpeg_available = shutil.which('ffmpeg') is not None
    ffmpeg_process = None
    cv2_writer = None

    if ffmpeg_available:
        print("Using FFmpeg Lossless Pipeline...")
        ffmpeg_process, mode = create_lossless_ffmpeg_writer(output_path, out_width, out_height, fps)
    else:
        mode = "opencv"

    if mode == "opencv":
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        cv2_writer = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Predict seamless 360 depth using circular horizontal wrapping
        depth_map = predict_seamless_360_depth(depth_pipe, frame)

        # 2. Synthesize stereoscopic Right Eye 360 view using GPU DIBR
        right_eye_bgr = synthesize_right_eye_360(frame, depth_map, disparity_factor=disparity_strength, device=device)

        # 3. Stitch Top/Bottom 3D VR Layout: [ Top: Left Eye (Original) | Bottom: Right Eye (Synthesized) ]
        top_bottom_3d = np.vstack((frame, right_eye_bgr))

        # Write frame to video pipe
        if mode == "ffmpeg" and ffmpeg_process:
            ffmpeg_process.stdin.write(top_bottom_3d.tobytes())
        elif cv2_writer:
            cv2_writer.write(top_bottom_3d)

        frame_count += 1
        if frame_count % 10 == 0 or frame_count == total_frames:
            print(f"Processed {frame_count}/{total_frames} frames...")

    cap.release()

    if mode == "ffmpeg" and ffmpeg_process:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
    elif cv2_writer:
        cv2_writer.release()

    print(f"\nSuccessfully generated 360° Stereoscopic 3D VR Video: {output_path}")

if __name__ == "__main__":
    INPUT_360_VIDEO = "input_360.mp4"   
    OUTPUT_360_VIDEO = "output_360_stereoscopic_3d.mp4"
    
    # DISPARITY_STRENGTH controls the depth effect intensity in VR:
    # 0.015 - 0.020 is ideal for natural, comfortable 3D on Meta Quest / VR headsets.
    DISPARITY_STRENGTH = 0.018
    
    if os.path.exists(INPUT_360_VIDEO):
        process_360_video(INPUT_360_VIDEO, OUTPUT_360_VIDEO, disparity_strength=DISPARITY_STRENGTH)
    else:
        print(f"Please place your 360 equirectangular video named '{INPUT_360_VIDEO}' in this directory.")