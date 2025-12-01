import React, { useState, useEffect, useRef } from "react";
import { Video, Camera, X, Play, Square, AlertCircle } from "lucide-react";
import { apiService } from "../services/api";

interface PhoneCameraMonitorProps {
  examId?: string;
  roomId?: string;
  onClose?: () => void;
}

const PhoneCameraMonitor: React.FC<PhoneCameraMonitorProps> = ({
  examId,
  roomId,
  onClose,
}) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [usePhoneCamera, setUsePhoneCamera] = useState(true);
  const [streamUrl, setStreamUrl] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [framesCaptured, setFramesCaptured] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [latestFrameUrl, setLatestFrameUrl] = useState<string | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const frameObjectUrlsRef = useRef<string[]>([]); // Use ref to track URLs without causing re-renders
  const previousFrameUrlRef = useRef<string | null>(null); // Track previous URL for cleanup

  // Check for active monitoring on mount
  useEffect(() => {
    checkActiveMonitoring();
    
    // Cleanup on unmount
    return () => {
      // Stop intervals first
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
      
      // Clean up streams
      stopStream();
      
      // Clean up all object URLs after a delay (give time for any pending operations)
      setTimeout(() => {
        frameObjectUrlsRef.current.forEach(url => {
          if (url && url.startsWith('blob:')) {
            try {
              URL.revokeObjectURL(url);
            } catch (e) {
              // Ignore errors when revoking
            }
          }
        });
        frameObjectUrlsRef.current = [];
        
        if (previousFrameUrlRef.current && previousFrameUrlRef.current.startsWith('blob:')) {
          try {
            URL.revokeObjectURL(previousFrameUrlRef.current);
          } catch (e) {
            // Ignore errors when revoking
          }
        }
      }, 100);
    };
  }, []);

  const checkActiveMonitoring = async () => {
    try {
      const response = await apiService.getActiveMonitoring();
      if (response.data?.active_sessions?.length > 0) {
        const session = response.data.active_sessions[0];
        setSessionId(session.session_id);
        setIsStreaming(true);
        setFramesCaptured(session.frames_captured || 0);
        if (session.stream_url) {
          const normalizedUrl = normalizeStreamUrl(session.stream_url);
          setStreamUrl(normalizedUrl);
          setUsePhoneCamera(false);
          setIsStreaming(true); // Ensure streaming state is set
          startStatusPolling(session.session_id); // This will also start frame polling
        } else {
          startStatusPolling(session.session_id);
        }
      }
    } catch (error) {
      console.error("Error checking active monitoring:", error);
    }
  };

  const startStatusPolling = (sessionId: string) => {
    if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
    }
    statusIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.getMonitoringStatus(sessionId);
        if (response.data) {
          setFramesCaptured(response.data.frames_captured || 0);
          // Only stop if explicitly inactive and we're sure it's stopped
          if (!response.data.is_active && response.data.status === 'stopped') {
            console.log("Monitoring stopped, stopping polling");
            setIsStreaming(false);
            if (statusIntervalRef.current) {
              clearInterval(statusIntervalRef.current);
              statusIntervalRef.current = null;
            }
            if (frameIntervalRef.current) {
              clearInterval(frameIntervalRef.current);
              frameIntervalRef.current = null;
            }
          }
        }
      } catch (error) {
        console.error("Error polling status:", error);
        // Don't stop polling on error - might be temporary network issue
      }
    }, 2000);
    
    // Start fetching latest frames for display
    startFramePolling(sessionId);
  };

  const fetchLatestFrame = async (sessionId: string) => {
    try {
      const objectUrl = await apiService.getLatestFrame(sessionId);
      
      // Only update if we got a new URL
      if (objectUrl) {
        // Store previous URL before updating
        const prevUrl = previousFrameUrlRef.current;
        
        // Update the displayed URL
        setLatestFrameUrl(objectUrl);
        previousFrameUrlRef.current = objectUrl;
        
        // Track in ref for cleanup
        frameObjectUrlsRef.current.push(objectUrl);
        
        // Clean up old URLs after a delay (keep last 5)
        if (frameObjectUrlsRef.current.length > 5) {
          const urlsToClean = frameObjectUrlsRef.current.slice(0, -5);
          frameObjectUrlsRef.current = frameObjectUrlsRef.current.slice(-5);
          
          // Revoke old URLs after a delay to ensure new image has loaded
          setTimeout(() => {
            urlsToClean.forEach(url => {
              if (url.startsWith('blob:') && url !== objectUrl) {
                URL.revokeObjectURL(url);
              }
            });
          }, 1000); // 1 second delay
        }
        
        // Clean up previous URL after image has time to load
        if (prevUrl && prevUrl !== objectUrl && prevUrl.startsWith('blob:')) {
          setTimeout(() => {
            // Only revoke if it's not the current URL
            if (previousFrameUrlRef.current !== prevUrl) {
              URL.revokeObjectURL(prevUrl);
            }
          }, 500); // 500ms delay
        }
      }
    } catch (error: any) {
      // Don't show error if frames just aren't ready yet (404 is expected initially)
      if (error?.message && !error.message.includes('404') && !error.message.includes('not found')) {
        console.error("Error fetching frame:", error);
      }
    }
  };

  const startFramePolling = (sessionId: string) => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    
    // Fetch immediately
    if (sessionId) {
      fetchLatestFrame(sessionId);
    }
    
    // Poll for latest frame every 200ms for smooth display (~5fps)
    // Continue polling as long as we have a sessionId (don't check isStreaming)
    frameIntervalRef.current = setInterval(() => {
      if (sessionId) {
        fetchLatestFrame(sessionId);
      } else {
        // If no session ID, stop polling
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
        }
      }
    }, 200); // Update every 200ms (~5 fps)
  };

  const startPhoneCameraStream = async () => {
    try {
      setError(null);
      setLoading(true);
      
      // Check if getUserMedia is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          "Camera access not available. Please use HTTPS or localhost."
        );
      }

      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment", // Use back camera on phones
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;
      
      // Display stream in video element
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // For phone camera, we need to send frames to backend
      // For now, we'll use a placeholder URL approach
      // In production, you'd send frames via WebSocket or similar
      
      setIsStreaming(true);
      setLoading(false);
      
      // Note: Direct browser camera stream can't be accessed by backend
      // You'll need to either:
      // 1. Use a phone app (IP Webcam) and provide stream URL
      // 2. Send frames via WebSocket to backend
      setError(
        "Phone camera is active. For backend processing, use IP Webcam app and provide stream URL."
      );
      
    } catch (err: any) {
      console.error("Error accessing camera:", err);
      setError(err.message || "Failed to access camera");
      setLoading(false);
    }
  };

  const normalizeStreamUrl = (url: string): string => {
    // Ensure URL has proper path for IP Webcam
    let normalized = url.trim();
    
    // Remove trailing slashes
    normalized = normalized.replace(/\/+$/, '');
    
    // Check if URL already has a path after the port
    const urlMatch = normalized.match(/^https?:\/\/[^\/]+(:\d+)?(\/.*)?$/);
    if (urlMatch) {
      // URL has host and possibly port
      const path = urlMatch[2];
      // If no path or path is just '/', add /video.mjpeg
      if (!path || path === '/') {
        normalized += '/video.mjpeg';
      } else if (path === '/video' || path === '/videofeed') {
        // Common paths - convert to .mjpeg for better compatibility
        normalized = normalized.replace(/\/(video|videofeed)$/, '/video.mjpeg');
      }
    }
    
    return normalized;
  };

  const getProxiedStreamUrl = (url: string): string => {
    // Use backend proxy to avoid CORS issues
    const normalizedUrl = normalizeStreamUrl(url);
    const encodedUrl = encodeURIComponent(normalizedUrl);
    return `http://127.0.0.1:8000/stream-proxy/mjpeg?url=${encodedUrl}`;
  };

  const startStreamUrlMonitoring = async () => {
    if (!streamUrl.trim()) {
      setError("Please enter a stream URL");
      return;
    }

    try {
      setError(null);
      setLoading(true);

      // Normalize the stream URL to ensure it has proper path
      const normalizedUrl = normalizeStreamUrl(streamUrl);
      
      // Update the input field with normalized URL
      setStreamUrl(normalizedUrl);

      const response = await apiService.startPhoneMonitoring({
        stream_url: normalizedUrl,
        exam_id: examId,
        room_id: roomId,
        duration_seconds: 3600,
        process_every_n_frames: 30,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        setSessionId(response.data.session_id);
        setIsStreaming(true);
        setFramesCaptured(0);
        // Ensure streamUrl is updated with normalized URL for display
        setStreamUrl(normalizedUrl);
        // Start polling for status and frames
        startStatusPolling(response.data.session_id);
      }

      setLoading(false);
    } catch (err: any) {
      console.error("Error starting monitoring:", err);
      setError(err.message || "Failed to start monitoring");
      setLoading(false);
    }
  };

  const stopStream = async () => {
    // Stop local camera stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Stop backend monitoring if active
    if (sessionId) {
      try {
        await apiService.stopPhoneMonitoring(sessionId);
      } catch (error) {
        console.error("Error stopping monitoring:", error);
      }
    }

    if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }

    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current.src = "";
    }

    setIsStreaming(false);
    setSessionId(null);
    setFramesCaptured(0);
    // Don't clear latestFrameUrl immediately - keep it visible until cleanup
    // It will be cleaned up in the unmount effect
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <Camera className="h-6 w-6 mr-2 text-purple-600" />
          Phone Camera Monitoring
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        )}
      </div>

      {/* Video Display */}
      <div className="relative bg-gray-900 rounded-lg aspect-video mb-4 overflow-hidden">
        {/* Display latest frame from backend or direct stream */}
        {isStreaming && streamUrl && !usePhoneCamera ? (
          <>
            {/* Display latest saved frame from backend (most reliable) */}
            {latestFrameUrl && sessionId ? (
              <img
                key={`frame-${framesCaptured}`}
                src={latestFrameUrl}
                alt="Live Stream"
                className="w-full h-full object-contain"
                onError={(e) => {
                  console.error("Frame image error:", e);
                  // Don't set error immediately - frames might not be ready yet
                  // Only show error after frames have been captured
                  if (framesCaptured > 0) {
                    setError("Failed to load frame. Check backend logs.");
                  }
                }}
                onLoad={() => {
                  setError(null);
                }}
                style={{ 
                  display: 'block', 
                  width: '100%', 
                  height: '100%',
                  objectFit: 'contain',
                  backgroundColor: '#000'
                }}
              />
            ) : sessionId ? (
              // Show placeholder while waiting for frames
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Video className="h-16 w-16 text-gray-600 mx-auto mb-2 animate-pulse" />
                  <p className="text-gray-400">Waiting for frames...</p>
                  <p className="text-gray-500 text-sm mt-1">Backend is capturing frames ({framesCaptured} captured)</p>
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Video className="h-16 w-16 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">No active stream</p>
                </div>
              </div>
            )}
          </>
        ) : usePhoneCamera && isStreaming ? (
          <video
            ref={videoRef}
            className="w-full h-full object-contain"
            autoPlay
            playsInline
            muted
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Video className="h-16 w-16 text-gray-600 mx-auto mb-2" />
              <p className="text-gray-400">No active stream</p>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="space-y-4">
        {/* Mode Selection */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              setUsePhoneCamera(true);
              setError(null);
            }}
            className={`px-4 py-2 rounded-lg transition-colors ${
              usePhoneCamera
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Use Phone Camera
          </button>
          <button
            onClick={() => {
              setUsePhoneCamera(false);
              setError(null);
            }}
            className={`px-4 py-2 rounded-lg transition-colors ${
              !usePhoneCamera
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Stream URL (IP Webcam)
          </button>
        </div>

        {/* Phone Camera Mode */}
        {usePhoneCamera && (
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              Access your phone camera directly from the browser. For backend
              processing, use IP Webcam app mode instead.
            </p>
            <div className="flex space-x-2">
              {!isStreaming ? (
                <button
                  onClick={startPhoneCameraStream}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Play className="h-4 w-4" />
                  <span>Start Camera</span>
                </button>
              ) : (
                <button
                  onClick={stopStream}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  <Square className="h-4 w-4" />
                  <span>Stop Camera</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Stream URL Mode */}
        {!usePhoneCamera && (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Stream URL (e.g., http://192.168.1.100:8080/video)
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={streamUrl}
                onChange={(e) => setStreamUrl(e.target.value)}
                placeholder="http://phone-ip:port/video"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isStreaming}
              />
              {!isStreaming ? (
                <button
                  onClick={startStreamUrlMonitoring}
                  disabled={loading || !streamUrl.trim()}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Play className="h-4 w-4" />
                  <span>Start Monitoring</span>
                </button>
              ) : (
                <button
                  onClick={stopStream}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  <Square className="h-4 w-4" />
                  <span>Stop</span>
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Use IP Webcam app on your phone and enter the stream URL shown in
              the app
            </p>
          </div>
        )}

        {/* Status */}
        {isStreaming && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-700 font-medium">Monitoring Active</span>
              </div>
              <span className="text-sm text-gray-600">
                Frames: {framesCaptured}
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start space-x-2">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PhoneCameraMonitor;

