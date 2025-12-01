import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import { apiService } from "../services/api";
import {
  Upload,
  Video,
  Play,
  FileVideo,
  CheckCircle,
  Clock,
  AlertCircle,
  X,
  Download,
} from "lucide-react";

interface VideoStream {
  stream_id: string;
  exam_id: string;
  room_id: string;
  stream_type: "live" | "recorded";
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  completed_at?: string;
  source_url?: string;
}

interface ProcessingStatus {
  job_id: string;
  stream_id: string;
  status: string;
  progress: number;
  total_frames: number;
  processed_frames: number;
  detected_activities: number;
  detected_violations: number;
}

interface Exam {
  exam_id: string;
  name?: string;
  course_code?: string;
  scheduled_date?: string;
}

interface Room {
  room_id: string;
  room_number: string;
  block?: string;
  exam_id?: string;
  total_seats?: number;
}

const VideoProcessingPage = () => {
  const [streams, setStreams] = useState<VideoStream[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedExam, setSelectedExam] = useState("");
  const [examNames, setExamNames] = useState<Record<string, string>>({});
  const [roomNames, setRoomNames] = useState<Record<string, string>>({});
  const [selectedRoom, setSelectedRoom] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatuses, setProcessingStatuses] = useState<
    Record<string, ProcessingStatus>
  >({});
  
  // Exam and Room data
  const [exams, setExams] = useState<Exam[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [filteredRooms, setFilteredRooms] = useState<Room[]>([]);
  const [loadingExams, setLoadingExams] = useState(false);
  const [loadingRooms, setLoadingRooms] = useState(false);

  useEffect(() => {
    fetchStreams();
    fetchExams();
    fetchRooms();
    
    // Refresh streams list every 10 seconds to catch new uploads (reduced frequency to prevent reloads)
    const refreshInterval = setInterval(() => {
      // Only refresh if not currently uploading
      if (!uploading) {
        fetchStreams();
      }
    }, 10000); // Increased to 10 seconds
    
    return () => clearInterval(refreshInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll for processing status updates - fetch status for processing and completed streams
  useEffect(() => {
    const streamsToPoll = streams.filter(
      (s) => s.status === "processing" || s.status === "pending" || s.status === "completed"
    );

    if (streamsToPoll.length === 0) return;

    // Poll status for all streams (to get frame counts for completed ones too)
    const pollInterval = setInterval(() => {
      streamsToPoll.forEach((stream) => {
        fetchProcessingStatus(stream.stream_id);
      });
    }, 5000); // Poll every 5 seconds (reduced frequency)

    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streams.length, streams.map(s => `${s.stream_id}-${s.status}`).join(',')]);

  useEffect(() => {
    // Filter rooms based on selected exam
    if (selectedExam) {
      const filtered = rooms.filter(
        (room) => room.exam_id === selectedExam || !room.exam_id
      );
      setFilteredRooms(filtered);
      // Clear room selection if current room is not in filtered list
      if (selectedRoom && !filtered.find((r) => r.room_id === selectedRoom)) {
        setSelectedRoom("");
      }
    } else {
      setFilteredRooms(rooms);
    }
  }, [selectedExam, rooms, selectedRoom]);

  const fetchExams = async () => {
    setLoadingExams(true);
    try {
      const response = await apiService.getExams({ limit: 100 });
      if (response.data && (response.data as any).exams) {
        setExams(
          (response.data as any).exams.map((exam: any) => ({
            exam_id: exam.exam_id || exam.id,
            name: exam.name,
            course_code: exam.course_code,
            scheduled_date: exam.scheduled_date || exam.exam_date,
          }))
        );
      }
    } catch (error) {
      console.error("Error fetching exams:", error);
    } finally {
      setLoadingExams(false);
    }
  };

  const fetchRooms = async () => {
    setLoadingRooms(true);
    try {
      const response = await apiService.getRooms();
      if (response.data) {
        const roomsData = Array.isArray(response.data) ? response.data : [];
        setRooms(
          roomsData.map((room: any) => ({
            room_id: room.room_id || room.id,
            room_number: room.room_number,
            block: room.block,
            exam_id: room.exam_id,
            total_seats: room.total_seats,
          }))
        );
        setFilteredRooms(
          roomsData.map((room: any) => ({
            room_id: room.room_id || room.id,
            room_number: room.room_number,
            block: room.block,
            exam_id: room.exam_id,
            total_seats: room.total_seats,
          }))
        );
      }
    } catch (error) {
      console.error("Error fetching rooms:", error);
    } finally {
      setLoadingRooms(false);
    }
  };

  // Removed duplicate useEffect - already handled above

  const fetchStreams = async () => {
    setLoading(true);
    try {
      // Use API service to fetch all streams
      const response = await apiService.getVideoStreams();
      console.log("Fetch streams response:", response);
      
      if (response.data && (response.data as any).success) {
        const streamsData = (response.data as any).data?.streams || [];
        console.log(`Fetched ${streamsData.length} streams from server`);
        
        // Merge with existing streams (keep any that aren't in server response)
        setStreams((prevStreams) => {
          const serverStreamIds = new Set(streamsData.map((s: any) => s.stream_id));
          const localOnlyStreams = prevStreams.filter(
            (s) => !serverStreamIds.has(s.stream_id)
          );
          
          const allStreams = [
            ...streamsData.map((s: any) => ({
              stream_id: s.stream_id,
              exam_id: s.exam_id,
              room_id: s.room_id,
              stream_type: s.stream_type,
              status: s.status,
              created_at: s.created_at,
              completed_at: s.completed_at,
              source_url: s.source_url,
            })),
            ...localOnlyStreams,
          ];
          
          // Sort by created_at (newest first)
          return allStreams.sort((a, b) => {
            const dateA = new Date(a.created_at).getTime();
            const dateB = new Date(b.created_at).getTime();
            return dateB - dateA;
          });
        });

        // Fetch exam and room names for all unique IDs
        const examIds = streamsData.map((s: any) => s.exam_id).filter((id: any) => Boolean(id)) as string[];
        const roomIds = streamsData.map((s: any) => s.room_id).filter((id: any) => Boolean(id)) as string[];
        const uniqueExamIds: string[] = [...new Set(examIds)];
        const uniqueRoomIds: string[] = [...new Set(roomIds)];
        
        await fetchExamAndRoomNames(uniqueExamIds, uniqueRoomIds);
        
        // Fetch status for all streams (including completed ones) to show frame counts
        // Use setTimeout to avoid blocking the main thread
        setTimeout(() => {
          streamsData.forEach((s: any) => {
            if (s.stream_id) {
              fetchProcessingStatus(s.stream_id);
            }
          });
        }, 1000); // Small delay to avoid overwhelming the API
      } else {
        console.warn("No streams data in response:", response);
        // Check if database warning message
        if (response.data && (response.data as any).message) {
          const message = (response.data as any).message;
          if (message.includes("Database not available")) {
            console.error("⚠️ DATABASE NOT ENABLED! Videos will not persist.");
            console.error("⚠️ Set USE_DATABASE=true in backend .env file");
            // Show warning to user
            if (streams.length === 0) {
              // Only show once if no streams
              console.warn("Videos uploaded without database will disappear after page refresh or server restart.");
            }
          }
        }
        // Don't clear existing streams, just log warning
      }
    } catch (error) {
      console.error("Error fetching streams:", error);
      // Don't clear existing streams on error
    } finally {
      setLoading(false);
    }
  };

  const fetchExamAndRoomNames = async (examIds: string[], roomIds: string[]) => {
    try {
      // Fetch exam names
      const examNamesMap: Record<string, string> = {};
      for (const examId of examIds) {
        try {
          const examResponse = await apiService.getExamById(examId);
          if (examResponse.data) {
            const exam = examResponse.data as any;
            const examName = exam.name || exam.course || exam.course_code || examId;
            examNamesMap[examId] = examName;
          }
        } catch (error) {
          console.warn(`Failed to fetch exam ${examId}:`, error);
          examNamesMap[examId] = examId; // Fallback to ID
        }
      }
      setExamNames((prev) => ({ ...prev, ...examNamesMap }));

      // Fetch room names
      const roomNamesMap: Record<string, string> = {};
      for (const roomId of roomIds) {
        try {
          const roomResponse = await apiService.getRoomById(roomId);
          if (roomResponse.data) {
            const room = roomResponse.data as any;
            const roomName = room.block && room.room_number 
              ? `${room.block} ${room.room_number}`
              : room.room_number || roomId;
            roomNamesMap[roomId] = roomName;
          }
        } catch (error) {
          console.warn(`Failed to fetch room ${roomId}:`, error);
          roomNamesMap[roomId] = roomId; // Fallback to ID
        }
      }
      setRoomNames((prev) => ({ ...prev, ...roomNamesMap }));
    } catch (error) {
      console.error("Error fetching exam/room names:", error);
    }
  };

  const fetchProcessingStatus = async (streamId: string) => {
    try {
      // Use API service to get processing status
      const response = await apiService.getVideoProcessingStatus(streamId);
      if (response.data && (response.data as any).success && (response.data as any).data) {
        const statusData = (response.data as any).data;
        setProcessingStatuses((prev) => ({
          ...prev,
          [streamId]: statusData,
        }));

        // Update stream status if completed
        if (statusData.status === "completed") {
          setStreams((prev) =>
            prev.map((s) =>
              s.stream_id === streamId
                ? { ...s, status: "completed" as const }
                : s
            )
          );
        }
      }
    } catch (error) {
      console.error("Error fetching processing status:", error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Get file extension
      const fileName = file.name.toLowerCase();
      const fileExtension = fileName.substring(fileName.lastIndexOf("."));
      
      // Validate file type by extension (more reliable than MIME type)
      const validExtensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"];
      const validMimeTypes = [
        "video/mp4",
        "video/avi",
        "video/x-msvideo",
        "video/quicktime", // .mov files
        "video/mov",
        "video/x-matroska", // .mkv files
        "video/webm",
      ];
      
      const isValidExtension = validExtensions.includes(fileExtension);
      const isValidMimeType = validMimeTypes.includes(file.type);
      
      if (!isValidExtension && !isValidMimeType) {
        alert(
          `Please select a valid video file.\nAllowed formats: MP4, AVI, MOV, MKV, or WEBM\n\nSelected file: ${file.name}`
        );
        e.target.value = ""; // Clear the input
        return;
      }
      
      // Validate file size (500MB max)
      if (file.size > 500 * 1024 * 1024) {
        alert("File size must be less than 500MB");
        e.target.value = ""; // Clear the input
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedExam || !selectedRoom) {
      alert("Please select a file, exam, and room");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("video_file", selectedFile);
      formData.append("exam_id", selectedExam);
      formData.append("room_id", selectedRoom);

      // Use XMLHttpRequest for upload progress tracking
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setUploadProgress(percentComplete);
        }
      });

      xhr.addEventListener("load", async () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            if (response.success && response.data) {
              // Add the uploaded stream immediately to the list
              const newStream: VideoStream = {
                stream_id: response.data.stream_id,
                exam_id: response.data.exam_id,
                room_id: response.data.room_id,
                stream_type: response.data.stream_type || "recorded",
                status: response.data.status || "pending",
                created_at: response.data.created_at || new Date().toISOString(),
                completed_at: response.data.completed_at,
                source_url: response.data.source_url,
              };
              
              // Add to streams list immediately
              setStreams((prev) => [newStream, ...prev]);
              
              alert("Video uploaded successfully! Processing will begin shortly.");
              setShowUploadModal(false);
              setSelectedFile(null);
              setSelectedExam("");
              setSelectedRoom("");
              setUploadProgress(0);
              
              // Don't refresh immediately - let the polling handle it
              // This prevents page reload during upload
            } else {
              alert("Upload failed: " + (response.message || "Unknown error"));
            }
          } catch (e) {
            console.error("Error parsing upload response:", e);
            alert("Upload successful but failed to parse response");
            // Don't refresh immediately - let the polling handle it
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            alert("Upload failed: " + (errorData.detail || `HTTP ${xhr.status}`));
          } catch {
            alert("Upload failed: HTTP " + xhr.status);
          }
        }
        setUploading(false);
      });

      xhr.addEventListener("error", () => {
        alert("Upload failed: Network error");
        setUploading(false);
      });

      const token = sessionStorage.getItem("token");
      xhr.open("POST", "http://127.0.0.1:8000/api/video-streams/upload");
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      xhr.send(formData);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload failed: " + (error instanceof Error ? error.message : "Unknown error"));
      setUploading(false);
    }
  };

  const handleViewResults = async (streamId: string) => {
    try {
      // Use API service to get processing results
      const response = await apiService.getVideoProcessingResults(streamId);
      if (response.data && (response.data as any).success) {
        const results = (response.data as any).data;
        // Show results summary
        alert(
          `Processing Results:\n- Activities: ${results.activities_summary?.total_activities || 0}\n- Violations: ${results.violations_summary?.total_violations || 0}\n- Student Activities: ${results.activities_summary?.student_activities || 0}\n- Invigilator Issues: ${results.activities_summary?.invigilator_issues || 0}`
        );
        // TODO: Navigate to violations/activities page with filtered results
        // Or show detailed results in a modal
        console.log("Processing results:", results);
      } else {
        alert("Failed to fetch results: " + (response.error || "Unknown error"));
      }
    } catch (error) {
      console.error("Error fetching results:", error);
      alert("Error fetching processing results");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-blue-100 text-blue-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5" />;
      case "processing":
        return <Clock className="w-5 h-5" />;
      case "pending":
        return <Clock className="w-5 h-5" />;
      case "failed":
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <Video className="w-5 h-5" />;
    }
  };

  const formatDateTime = (dateString: string | undefined): string => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return dateString; // Fallback to raw string if invalid
      }
      
      // Format: DD/MM/YYYY, HH:MM:SS AM/PM (local timezone)
      return date.toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return dateString; // Fallback to raw string
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <InvestigatorSidebar />
        <div className="flex-1 flex flex-col overflow-hidden ml-64">
          <InvestigatorHeader />
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <InvestigatorSidebar />
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <InvestigatorHeader />
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Header Actions */}
          <div className="mb-6 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">
              Exam Footage Processing
            </h2>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-indigo-900 text-white px-6 py-3 rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 font-medium"
            >
              <Upload className="w-5 h-5" />
              Upload Video
            </button>
          </div>

          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Video className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900 mb-1">
                  Video Processing Information
                </h3>
                <p className="text-sm text-blue-700">
                  Upload recorded exam footage for AI analysis. The system will
                  automatically detect suspicious behaviors, violations, and
                  invigilator activities. Processing results will be available
                  in the Violations and Activities pages.
                </p>
              </div>
            </div>
          </div>

          {/* Video Streams List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Video Streams
              </h3>
            </div>

            <div className="divide-y divide-gray-200">
              {streams.length === 0 ? (
                <div className="p-12 text-center">
                  <FileVideo className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">No video streams found</p>
                  <p className="text-sm text-gray-500 mb-4">
                    Upload a video to begin processing
                  </p>
                  <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md mx-auto">
                    <p className="text-xs text-yellow-800">
                      <strong>Note:</strong> If videos disappear after closing the page, 
                      check that <code className="bg-yellow-100 px-1 rounded">USE_DATABASE=true</code> 
                      is set in the backend <code className="bg-yellow-100 px-1 rounded">.env</code> file.
                    </p>
                  </div>
                </div>
              ) : (
                streams.map((stream) => {
                  const status = processingStatuses[stream.stream_id];
                  return (
                    <div
                      key={stream.stream_id}
                      className="p-6 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            {getStatusIcon(stream.status)}
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {stream.stream_type === "live"
                                  ? "Live Stream"
                                  : "Recorded Video"}
                              </h4>
                              <p className="text-sm text-gray-500">
                                Stream ID: {stream.stream_id}
                              </p>
                            </div>
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                                stream.status
                              )}`}
                            >
                              {stream.status.toUpperCase()}
                            </span>
                          </div>

                          <div className="grid grid-cols-3 gap-4 mb-3">
                            <div>
                              <p className="text-xs text-gray-500">Exam</p>
                              <p className="text-sm font-medium">
                                {examNames[stream.exam_id] || stream.exam_id}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Room</p>
                              <p className="text-sm font-medium">
                                {roomNames[stream.room_id] || stream.room_id}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Uploaded</p>
                              <p className="text-sm font-medium">
                                {formatDateTime(stream.created_at)}
                              </p>
                            </div>
                          </div>

                          {/* Processing Progress */}
                          {(stream.status === "processing" || stream.status === "pending") && (
                            <div className="mt-4">
                              {status ? (
                                <>
                                  <div className="flex justify-between text-sm mb-2">
                                    <span className="text-gray-600">
                                      {status.total_frames > 0 ? (
                                        <>
                                          Extracting/Processing: {status.processed_frames} /{" "}
                                          {status.total_frames} frames
                                        </>
                                      ) : (
                                        "Initializing frame extraction..."
                                      )}
                                    </span>
                                    {status.progress > 0 && (
                                      <span className="text-gray-600">
                                        {status.progress.toFixed(1)}%
                                      </span>
                                    )}
                                  </div>
                                  {status.total_frames > 0 && (
                                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                      <div
                                        className="bg-indigo-900 h-2 rounded-full transition-all"
                                        style={{
                                          width: `${Math.max(status.progress, 1)}%`,
                                        }}
                                      ></div>
                                    </div>
                                  )}
                                  <div className="mt-2 text-xs text-gray-500 space-y-1">
                                    {status.total_frames > 0 && (
                                      <div>
                                        📸 Frames extracted: {status.processed_frames} / {status.total_frames}
                                      </div>
                                    )}
                                    {status.detected_activities > 0 && (
                                      <div>
                                        Detected: {status.detected_activities} activities
                                      </div>
                                    )}
                                    {status.detected_violations > 0 && (
                                      <div>
                                        ⚠️ Violations: {status.detected_violations}
                                      </div>
                                    )}
                                    {status.total_frames === 0 && (
                                      <div className="text-blue-600">
                                        ⏳ Starting frame extraction from video...
                                      </div>
                                    )}
                                  </div>
                                </>
                              ) : (
                                <div className="text-sm text-gray-500">
                                  <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 animate-spin" />
                                    <span>Waiting for processing to start...</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Completed Info */}
                          {stream.status === "completed" && (
                            <div className="mt-4 p-3 bg-green-50 rounded-lg space-y-2">
                              <p className="text-sm font-medium text-green-800">
                                ✓ Processing completed
                              </p>
                              {status && (
                                <>
                                  <div className="text-xs text-green-700 space-y-1">
                                    <div>
                                      📸 <strong>Frames extracted:</strong> {status.processed_frames} / {status.total_frames} frames
                                    </div>
                                    {status.detected_activities > 0 && (
                                      <div>
                                        <strong>Activities detected:</strong> {status.detected_activities}
                                      </div>
                                    )}
                                    {status.detected_violations > 0 && (
                                      <div>
                                        ⚠️ <strong>Violations detected:</strong> {status.detected_violations}
                                      </div>
                                    )}
                                    {status.detected_activities === 0 && status.detected_violations === 0 && (
                                      <div className="text-green-600">
                                        No suspicious activities detected
                                      </div>
                                    )}
                                  </div>
                                </>
                              )}
                              {!status && (
                                <p className="text-xs text-green-700">
                                  Processing completed successfully
                                </p>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2 ml-4">
                          {stream.status === "completed" && (
                            <button
                              onClick={() => handleViewResults(stream.stream_id)}
                              className="px-4 py-2 bg-indigo-900 text-white rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 text-sm"
                            >
                              <Play className="w-4 h-4" />
                              View Results
                            </button>
                          )}
                          {stream.source_url && (
                            <button
                              onClick={() => window.open(stream.source_url, "_blank")}
                              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm"
                            >
                              <Download className="w-4 h-4" />
                              Download
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  Upload Exam Video
                </h2>
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setSelectedFile(null);
                    setSelectedExam("");
                    setSelectedRoom("");
                    setUploadProgress(0);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* File Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Video File
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-900 transition-colors">
                  <input
                    type="file"
                    accept="video/mp4,video/avi,video/quicktime,video/x-msvideo,video/x-matroska,video/webm,.mp4,.avi,.mov,.mkv,.webm"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="video-upload"
                  />
                  <label
                    htmlFor="video-upload"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <Upload className="w-12 h-12 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">
                      {selectedFile
                        ? selectedFile.name
                        : "Click to select video file"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Supported formats: MP4, AVI, MOV, MKV, or WEBM (Max 500MB)
                    </p>
                  </label>
                </div>
                {selectedFile && (
                  <div className="mt-2 text-sm text-gray-600">
                    File size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </div>
                )}
              </div>

              {/* Exam Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Exam <span className="text-red-500">*</span>
                </label>
                {loadingExams ? (
                  <div className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
                    Loading exams...
                  </div>
                ) : (
                  <select
                    value={selectedExam}
                    onChange={(e) => setSelectedExam(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                  >
                    <option value="">-- Select an Exam --</option>
                    {exams.map((exam) => (
                      <option key={exam.exam_id} value={exam.exam_id}>
                        {exam.name || "Unnamed Exam"}
                        {exam.course_code ? ` (${exam.course_code})` : ""}
                        {exam.scheduled_date
                          ? ` - ${new Date(exam.scheduled_date).toLocaleDateString()}`
                          : ""}
                      </option>
                    ))}
                  </select>
                )}
                {exams.length === 0 && !loadingExams && (
                  <p className="text-xs text-gray-500 mt-1">
                    No exams available. Please create an exam first.
                  </p>
                )}
              </div>

              {/* Room Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Room <span className="text-red-500">*</span>
                </label>
                {loadingRooms ? (
                  <div className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
                    Loading rooms...
                  </div>
                ) : (
                  <select
                    value={selectedRoom}
                    onChange={(e) => setSelectedRoom(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                    disabled={!selectedExam}
                  >
                    <option value="">
                      {selectedExam
                        ? "-- Select a Room --"
                        : "-- Select an Exam first --"}
                    </option>
                    {filteredRooms.map((room) => (
                      <option key={room.room_id} value={room.room_id}>
                        {room.room_number}
                        {room.block ? ` - Block ${room.block}` : ""}
                        {room.total_seats
                          ? ` (${room.total_seats} seats)`
                          : ""}
                      </option>
                    ))}
                  </select>
                )}
                {filteredRooms.length === 0 && !loadingRooms && selectedExam && (
                  <p className="text-xs text-gray-500 mt-1">
                    No rooms available for this exam. Please create a room first.
                  </p>
                )}
                {!selectedExam && (
                  <p className="text-xs text-gray-500 mt-1">
                    Please select an exam first to see available rooms.
                  </p>
                )}
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Uploading...</span>
                    <span className="text-gray-600">
                      {uploadProgress.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-900 h-2 rounded-full transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setSelectedFile(null);
                    setSelectedExam("");
                    setSelectedRoom("");
                    setUploadProgress(0);
                  }}
                  disabled={uploading}
                  className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploading || !selectedFile || !selectedExam || !selectedRoom}
                  className="flex-1 bg-indigo-900 text-white px-6 py-3 rounded-lg hover:bg-indigo-800 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? "Uploading..." : "Upload & Process"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoProcessingPage;

