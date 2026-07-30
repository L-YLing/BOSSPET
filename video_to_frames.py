import cv2
import os
import numpy as np
from rembg import remove
from PIL import Image

def process_video(video_path, out_dir, target_frame_count=6):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    
    # 清空旧图片
    for f in os.listdir(out_dir):
        if f.endswith('.png'):
            os.remove(os.path.join(out_dir, f))
            
    if not os.path.exists(video_path):
        print(f"Error: 视频未找到 {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[{video_path}] 总帧数: {total_frames}")
    
    if total_frames > 0:
        indices = np.linspace(0, total_frames - 1, target_frame_count, dtype=int)
    else:
        indices = range(target_frame_count)
        
    frames_extracted = []
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx in indices:
            frames_extracted.append(frame)
        frame_idx += 1
    cap.release()
    
    print(f"开始去背并保存 {len(frames_extracted)} 帧到 {out_dir}...")
    for i, frame in enumerate(frames_extracted):
        # 将 OpenCV 的 BGR 转为 RGB 给 PIL 用
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        
        # 使用 rembg 去除背景
        out_img = remove(pil_img)
        
        # 保存 (使用 PIL 兼容所有的中文路径)
        out_path = os.path.join(out_dir, f"{i+1}.png")
        out_img.save(out_path)
        print(f"  -> 已保存: {out_path}")

if __name__ == "__main__":
    # 示例用法，用户可以自行修改路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 可以通过修改此处的路径来处理不同的 MP4 文件
    videos_to_process = [
        # (视频文件路径, 输出到的目录路径)
        # (r"path\to\idle.mp4", os.path.join(base_dir, "assets", "idle_frames")),
        # (r"path\to\spanking.mp4", os.path.join(base_dir, "assets", "spanking_frames")),
    ]
    
    for vid, out in videos_to_process:
        process_video(vid, out, target_frame_count=6)
