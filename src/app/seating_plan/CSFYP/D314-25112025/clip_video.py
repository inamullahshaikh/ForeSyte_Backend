"""
Clip a video between two timestamps.
Uses ffmpeg when available (fast, no re-encode), falls back to OpenCV.
"""

import subprocess
import sys
import os


def parse_timestamp(ts):
    """
    Parse timestamp string to seconds.
    Supports: "MM:SS", "HH:MM:SS", or plain seconds (e.g. "125" or 125).
    """
    if isinstance(ts, (int, float)):
        return float(ts)
    s = str(ts).strip()
    parts = s.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp: {ts}")


def secs_to_hhmmss(secs):
    """Convert seconds to HH:MM:SS.mmm format for ffmpeg."""
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def clip_with_ffmpeg(input_path, output_path, start_sec, end_sec):
    """Clip using ffmpeg (stream copy, no re-encode)."""
    start_str = secs_to_hhmmss(start_sec)
    duration = end_sec - start_sec
    cmd = [
        "ffmpeg",
        "-y",  # overwrite
        "-ss", start_str,  # seek before input
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",  # no re-encode
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr if result.returncode != 0 else ""


def clip_with_opencv(input_path, output_path, start_sec, end_sec):
    """Clip using OpenCV (reads/writes frame-by-frame, re-encodes)."""
    import cv2

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return False, "Could not open video"

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    if fourcc == 0:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    if not out.isOpened():
        cap.release()
        return False, "Could not create output"

    frame_idx = start_frame
    while frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    return True, ""


def clip_video(input_path, start_ts, end_ts, output_path=None):
    """
    Clip video between two timestamps.

    Args:
        input_path: Path to input video (e.g. D314.mp4)
        start_ts: Start timestamp - "MM:SS", "HH:MM:SS", or seconds
        end_ts: End timestamp - same format
        output_path: Output file path (default: input_clip_Start_End.mp4)

    Returns:
        (success: bool, output_path: str)
    """
    start_sec = parse_timestamp(start_ts)
    end_sec = parse_timestamp(end_ts)

    if start_sec >= end_sec:
        return False, f"Start ({start_sec}s) must be before end ({end_sec}s)"

    if not os.path.isfile(input_path):
        return False, f"Input file not found: {input_path}"

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clip_{start_sec:.0f}s_to_{end_sec:.0f}s{ext}"

    # Try ffmpeg first
    try:
        ok, err = clip_with_ffmpeg(input_path, output_path, start_sec, end_sec)
        if ok:
            return True, output_path
        # ffmpeg failed; try OpenCV
    except FileNotFoundError:
        pass

    ok, err = clip_with_opencv(input_path, output_path, start_sec, end_sec)
    if ok:
        return True, output_path
    return False, err or "Clip failed"


def main():
    # Example: clip D314.mp4 from 28m44s to 30m00s
    input_path = "D314.mp4"
    start_ts = "28:44"
    end_ts = "30:00"

    if len(sys.argv) >= 4:
        input_path = sys.argv[1]
        start_ts = sys.argv[2]
        end_ts = sys.argv[3]

    output_path = sys.argv[4] if len(sys.argv) >= 5 else None

    print(f"Clipping: {input_path}")
    print(f"  From: {start_ts}  To: {end_ts}")

    success, result = clip_video(input_path, start_ts, end_ts, output_path)

    if success:
        print(f"Saved: {result}")
    else:
        print(f"Error: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
