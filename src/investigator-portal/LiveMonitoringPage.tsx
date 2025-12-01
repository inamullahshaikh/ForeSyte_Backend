import React, { useState, useEffect } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import { Video, Play, Pause, Maximize2, Users, Eye, X, Activity, AlertTriangle } from "lucide-react";
import { apiService } from "../services/api";
import { useNavigate } from "react-router-dom";

interface CameraFeed {
  camera_id: string;
  room_id: string;
  room_name: string;
  status: "active" | "inactive" | "error";
  students_monitored: number;
  stream_url?: string;
}

interface Exam {
  exam_id: string;
  name: string;
  course_code: string;
  scheduled_date?: string;
}

const LiveMonitoringPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [cameraFeeds, setCameraFeeds] = useState<CameraFeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedExam, setSelectedExam] = useState<string>("");
  const [exams, setExams] = useState<Exam[]>([]);
  const [loadingExams, setLoadingExams] = useState(false);

  useEffect(() => {
    fetchExams();
    fetchCameraFeeds();
    // Refresh feeds every 5 seconds
    const interval = setInterval(fetchCameraFeeds, 5000);
    return () => clearInterval(interval);
  }, [selectedExam]);

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

  const fetchCameraFeeds = async () => {
    try {
      const response = await apiService.getMonitoringFeeds(selectedExam || undefined);
      if (response.data && (response.data as any).feeds) {
        setCameraFeeds((response.data as any).feeds);
      }
    } catch (error) {
      console.error("Error fetching camera feeds:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "inactive":
        return "bg-gray-400";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-400";
    }
  };

  // Get proxied stream URL to avoid CORS issues with IP Webcam
  const getProxiedStreamUrl = (url: string | undefined): string | undefined => {
    if (!url) return undefined;
    
    // If URL is already proxied, return as is
    if (url.includes('/stream-proxy/')) {
      return url;
    }
    
    // If it's an MJPEG stream (IP Webcam), use proxy
    if (url.includes('/video.mjpeg') || url.includes('/videofeed') || url.includes(':8080/')) {
      const encodedUrl = encodeURIComponent(url);
      return `http://127.0.0.1:8000/stream-proxy/mjpeg?url=${encodedUrl}`;
    }
    
    // For other stream types, return as is
    return url;
  };

  const activeCameras = cameraFeeds.filter((cam) => cam.status === "active").length;
  const totalStudents = cameraFeeds.reduce(
    (sum, cam) => sum + cam.students_monitored,
    0
  );
  const uniqueRooms = new Set(cameraFeeds.map((c) => c.room_id)).size;

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <InvestigatorSidebar />
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <InvestigatorHeader />

        <div className="flex-1 p-6 overflow-y-auto">
          {/* Header Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Live Monitoring
                </h1>
                <p className="text-gray-600">
                  Monitor exam sessions in real-time across all examination halls
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-green-700 font-medium">Live</span>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-xs mb-1">Active Cameras</p>
                  <p className="text-xl font-bold text-gray-900">
                    {activeCameras}/{cameraFeeds.length}
                  </p>
                </div>
                <div className="p-2 bg-blue-50 rounded-lg">
                  <Video className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-xs mb-1">Students Monitored</p>
                  <p className="text-xl font-bold text-gray-900">{totalStudents}</p>
                </div>
                <div className="p-2 bg-green-50 rounded-lg">
                  <Users className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-xs mb-1">Examination Rooms</p>
                  <p className="text-xl font-bold text-gray-900">{uniqueRooms}</p>
                </div>
                <div className="p-2 bg-purple-50 rounded-lg">
                  <Eye className="h-5 w-5 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-xs mb-1">Total Feeds</p>
                  <p className="text-xl font-bold text-gray-900">
                    {cameraFeeds.length}
                  </p>
                </div>
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <Video className="h-5 w-5 text-indigo-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Filter Section */}
          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200 mb-4">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Filter by Exam:
              </label>
              <select
                value={selectedExam}
                onChange={(e) => setSelectedExam(e.target.value)}
                disabled={loadingExams}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">
                  {loadingExams ? "Loading exams..." : "-- All Exams --"}
                </option>
                {exams.map((exam) => (
                  <option key={exam.exam_id} value={exam.exam_id}>
                    {exam.name} {exam.course_code ? `(${exam.course_code})` : ""}
                    {exam.scheduled_date
                      ? ` - ${new Date(exam.scheduled_date).toLocaleDateString()}`
                      : ""}
                  </option>
                ))}
              </select>
              {selectedExam && (
                <button
                  onClick={() => setSelectedExam("")}
                  className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors whitespace-nowrap"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Camera Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                Loading camera feeds...
              </div>
            ) : cameraFeeds.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                <Video className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium">No camera feeds available</p>
                <p className="text-sm text-gray-500 mt-2">
                  Camera feeds will appear here when exams are active
                </p>
              </div>
            ) : (
              cameraFeeds.map((camera) => {
                return (
                  <div
                    key={camera.camera_id}
                    className={`bg-white rounded-lg shadow-sm border transition-all cursor-pointer ${
                      selectedCamera === camera.camera_id
                        ? "border-purple-500 shadow-md"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => setSelectedCamera(camera.camera_id)}
                  >
                    {/* Video Feed Placeholder */}
                    <div className="relative bg-gray-900 rounded-t-lg overflow-hidden" style={{ height: '200px' }}>
                      <div className="absolute inset-0 flex items-center justify-center">
                        {camera.stream_url ? (
                          // Use img tag for MJPEG streams (IP Webcam), video tag for other formats
                          camera.stream_url.includes('.mjpeg') || camera.stream_url.includes(':8080/') ? (
                            <img
                              src={getProxiedStreamUrl(camera.stream_url)}
                              alt={`Camera ${camera.camera_id}`}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                console.error("Failed to load stream:", camera.stream_url);
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          ) : (
                            <video
                              src={getProxiedStreamUrl(camera.stream_url)}
                              className="w-full h-full object-cover"
                              autoPlay
                              muted
                              playsInline
                              onError={() => {
                                console.error("Failed to load video stream:", camera.stream_url);
                              }}
                            />
                          )
                        ) : (
                          <div className="text-center p-4">
                            <Video className="h-12 w-12 text-gray-500 mx-auto mb-2" />
                            <p className="text-gray-400 text-xs font-medium">{camera.camera_id}</p>
                            <p className="text-gray-500 text-xs mt-1">No stream URL configured</p>
                          </div>
                        )}
                      </div>

                      {/* Status Indicator */}
                      <div className="absolute top-3 left-3 flex items-center space-x-2">
                        <div
                          className={`w-3 h-3 rounded-full ${getStatusColor(
                            camera.status
                          )}`}
                        ></div>
                        <span className="text-white text-xs font-medium bg-black/50 px-2 py-1 rounded">
                          {camera.status.toUpperCase()}
                        </span>
                      </div>

                      {/* Controls */}
                      <div className="absolute bottom-3 right-3 flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsPlaying(!isPlaying);
                          }}
                          className="p-2 bg-black/50 rounded-lg hover:bg-black/70 transition-colors"
                        >
                          {isPlaying ? (
                            <Pause className="h-4 w-4 text-white" />
                          ) : (
                            <Play className="h-4 w-4 text-white" />
                          )}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCamera(camera.camera_id);
                          }}
                          className="p-2 bg-black/50 rounded-lg hover:bg-black/70 transition-colors"
                        >
                          <Maximize2 className="h-4 w-4 text-white" />
                        </button>
                      </div>
                    </div>

                    {/* Camera Info */}
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-sm text-gray-900 truncate">
                          {camera.room_name}
                        </h3>
                        <span className="text-xs text-gray-500 truncate ml-2">
                          {camera.camera_id}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs mb-2">
                        <div className="flex items-center text-gray-600">
                          <Users className="h-3 w-3 mr-1" />
                          <span>{camera.students_monitored} students</span>
                        </div>
                        {camera.status === "active" && (
                          <div className="flex items-center text-green-600">
                            <Activity className="h-3 w-3 mr-1" />
                            <span>Active</span>
                          </div>
                        )}
                      </div>
                      
                      {/* View Violations Button */}
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/investigator/violations?room_id=${camera.room_id}`);
                          }}
                          className="w-full flex items-center justify-center text-xs text-purple-600 hover:text-purple-800 hover:bg-purple-50 py-1 rounded transition-colors"
                        >
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          View Violations
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Selected Camera Full View (Modal) */}
          {selectedCamera && (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8">
              <div className="bg-white rounded-lg w-full max-w-6xl">
                  <div className="relative bg-gray-900 rounded-t-lg" style={{ height: '500px' }}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    {(() => {
                      const selectedFeed = cameraFeeds.find((c) => c.camera_id === selectedCamera);
                      const streamUrl = selectedFeed?.stream_url;
                      
                      if (streamUrl) {
                        // Use img tag for MJPEG streams (IP Webcam), video tag for other formats
                        if (streamUrl.includes('.mjpeg') || streamUrl.includes(':8080/')) {
                          return (
                            <img
                              src={getProxiedStreamUrl(streamUrl)}
                              alt={`Camera ${selectedCamera}`}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                console.error("Failed to load stream:", streamUrl);
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          );
                        } else {
                          return (
                            <video
                              src={getProxiedStreamUrl(streamUrl)}
                              className="w-full h-full object-cover"
                              autoPlay
                              muted
                              playsInline
                              onError={() => {
                                console.error("Failed to load video stream:", streamUrl);
                              }}
                            />
                          );
                        }
                      } else {
                        return <Video className="h-32 w-32 text-gray-600" />;
                      }
                    })()}
                  </div>
                  <button
                    onClick={() => setSelectedCamera(null)}
                    className="absolute top-4 right-4 p-2 bg-black/50 rounded-lg hover:bg-black/70 text-white"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">
                    {
                      cameraFeeds.find((c) => c.camera_id === selectedCamera)
                        ?.room_name
                    }
                  </h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-gray-600 text-sm">Camera ID</p>
                      <p className="font-medium">{selectedCamera}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Students Monitored</p>
                      <p className="font-medium">
                        {
                          cameraFeeds.find((c) => c.camera_id === selectedCamera)
                            ?.students_monitored || 0
                        }
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Status</p>
                      <p className="font-medium">
                        {
                          cameraFeeds.find((c) => c.camera_id === selectedCamera)
                            ?.status || "unknown"
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoringPage;

