"""
Extract one frame every N seconds from a video and save to a new folder.
"""
import cv2
import os
import argparse


def parse_time(s):
    """Parse 'MM:SS' or 'HH:MM:SS' to total seconds."""
    parts = [int(x) for x in s.strip().split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Invalid time format: {s} (use MM:SS or HH:MM:SS)")


def extract_frames_every_n_seconds(video_path, interval_seconds=5, output_dir=None, start_seconds=None, end_seconds=None):
    """
    Extract one frame every N seconds from a video and save to a folder.

    Args:
        video_path: Path to the video file
        interval_seconds: Extract one frame every this many seconds (default: 2)
        output_dir: Folder to save frames (default: <video_name>_frames_2s in same directory)
        start_seconds: Start time in seconds (None = from start)
        end_seconds: End time in seconds (None = to end)
    """
    video_path = os.path.abspath(video_path)
    if not os.path.isfile(video_path):
        print(f"Error: Video file not found: {video_path}")
        return

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps if fps > 0 else 0

    t_start = 0.0 if start_seconds is None else max(0, float(start_seconds))
    t_end = duration_seconds if end_seconds is None else min(duration_seconds, float(end_seconds))

    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    if output_dir is None:
        output_dir = os.path.join(video_dir, f"{video_name}_frames_{interval_seconds}s")
    output_dir = os.path.abspath(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Video: {video_path}")
    print(f"  FPS: {fps:.2f}, Duration: {duration_seconds:.2f}s, Frames: {total_frames}")
    print(f"  Range: {t_start:.1f}s - {t_end:.1f}s, 1 frame every {interval_seconds}s -> {output_dir}")

    count = 0
    t_sec = t_start
    while t_sec <= t_end:
        frame_idx = int(t_sec * fps)
        if frame_idx >= total_frames:
            break
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = video.read()
        if not success:
            break
        # Filename with timestamp (e.g. frame_000_00m00s.jpg, frame_001_00m02s.jpg)
        m = int(t_sec) // 60
        s = int(t_sec) % 60
        filename = f"frame_{count:04d}_{m:02d}m{s:02d}s.jpg"
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, frame)
        count += 1
        t_sec += interval_seconds

    video.release()
    print(f"Saved {count} frames to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract 1 frame every N seconds from a video")
    parser.add_argument(
        "video",
        nargs="?",
        default=os.path.join(os.path.dirname(__file__), "D314.mp4"),
        help="Path to video file (default: D314.mp4 in this folder)",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=5,
        help="Interval in seconds between extracted frames (default: 5)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output folder for frames (default: <video_name>_frames_<interval>s)",
    )
    parser.add_argument(
        "-s", "--start",
        default="14:10",
        metavar="MM:SS",
        help="Start time (default: 14:10)",
    )
    parser.add_argument(
        "-e", "--end",
        default="31:06",
        metavar="MM:SS",
        help="End time (default: 31:06)",
    )
    args = parser.parse_args()

    start_sec = parse_time(args.start)
    end_sec = parse_time(args.end)
    extract_frames_every_n_seconds(args.video, args.interval, args.output, start_sec, end_sec)
