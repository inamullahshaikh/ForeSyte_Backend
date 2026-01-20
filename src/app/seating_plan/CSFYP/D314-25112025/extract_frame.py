import cv2
import os

def extract_frame_at_timestamp(video_path, minutes, seconds, output_path=None):
    """
    Extract a frame from a video at a specific timestamp.
    
    Args:
        video_path: Path to the video file
        minutes: Minutes component of timestamp
        seconds: Seconds component of timestamp
        output_path: Path to save the extracted frame (optional)
    """
    # Calculate total seconds
    timestamp_seconds = minutes * 60 + seconds
    
    # Open the video file
    video = cv2.VideoCapture(video_path)
    
    if not video.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return False
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps if fps > 0 else 0
    
    print(f"Video properties:")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
    print(f"  Requested timestamp: {minutes}m {seconds}s ({timestamp_seconds} seconds)")
    
    # Check if timestamp is within video duration
    if timestamp_seconds > duration_seconds:
        print(f"Warning: Requested timestamp ({timestamp_seconds}s) exceeds video duration ({duration_seconds:.2f}s)")
        print("Extracting frame from the end of the video instead")
        timestamp_seconds = duration_seconds - 1
    
    # Calculate frame number
    frame_number = int(timestamp_seconds * fps)
    
    # Set video position to the desired frame
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    # Read the frame
    success, frame = video.read()
    
    if not success:
        print(f"Error: Could not read frame at timestamp {minutes}:{seconds:02d}")
        video.release()
        return False
    
    # Generate output path if not provided
    if output_path is None:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_name}_frame_{minutes}m{seconds}s.jpg")
    
    # Save the frame
    cv2.imwrite(output_path, frame)
    print(f"Frame successfully extracted and saved to: {output_path}")
    
    # Release the video
    video.release()
    
    return True

if __name__ == "__main__":
    # Set the video path
    video_path = "D314.mp4"
    
    # Extract frame at 28 minutes 44 seconds
    minutes = 28
    seconds = 44
    
    print(f"Extracting frame from {video_path} at {minutes}:{seconds:02d}...")
    extract_frame_at_timestamp(video_path, minutes, seconds)

