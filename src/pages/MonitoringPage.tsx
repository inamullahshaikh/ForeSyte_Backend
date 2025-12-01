import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { Video, Play, Pause, Maximize2, AlertCircle, Users, Eye, Camera } from "lucide-react";
import { apiService } from "../services/api";
import PhoneCameraMonitor from "../components/PhoneCameraMonitor";

interface CameraFeed {
  camera_id: string;
  id?: string;
  room_id: string;
  roomId?: string;
  room_name: string;
  roomName?: string;
  status: "active" | "inactive" | "error";
  students_monitored: number;
  studentsMonitored?: number;
  incidents?: number;
  stream_url?: string;
  streamUrl?: string;
}

const MonitoringPage: React.FC = () => {
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [cameraFeeds, setCameraFeeds] = useState<CameraFeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPhoneCamera, setShowPhoneCamera] = useState(false);

  useEffect(() => {
    fetchCameraFeeds();
    // Refresh feeds every 5 seconds
    const interval = setInterval(fetchCameraFeeds, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchCameraFeeds = async () => {
    try {
      const response = await apiService.getMonitoringFeeds();
      if (response.data?.feeds) {
        const feeds = response.data.feeds.map((feed: any) => ({
          camera_id: feed.camera_id,
          id: feed.camera_id,
          room_id: feed.room_id,
          roomId: feed.room_id,
          room_name: feed.room_name,
          roomName: feed.room_name,
          status: feed.status || "inactive",
          students_monitored: feed.students_monitored || 0,
          studentsMonitored: feed.students_monitored || 0,
          incidents: 0, // This would need to come from a separate API call
          stream_url: feed.stream_url,
          streamUrl: feed.stream_url,
        }));
        setCameraFeeds(feeds);
      }
    } catch (error) {
      console.error("Error fetching camera feeds:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-500";
      case "inactive": return "bg-gray-400";
      case "error": return "bg-red-500";
      default: return "bg-gray-400";
    }
  };

  const activeCameras = cameraFeeds.filter(cam => cam.status === "active").length;
  const totalStudents = cameraFeeds.reduce((sum, cam) => sum + (cam.studentsMonitored || cam.students_monitored || 0), 0);
  const totalIncidents = cameraFeeds.reduce((sum, cam) => sum + (cam.incidents || 0), 0);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
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
                <button
                  onClick={() => setShowPhoneCamera(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Camera className="h-5 w-5" />
                  <span>Start Phone Camera</span>
                </button>
                <div className="flex items-center bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-green-700 font-medium">Live</span>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm mb-1">Active Cameras</p>
                  <p className="text-2xl font-bold text-gray-900">{activeCameras}/{cameraFeeds.length}</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Video className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm mb-1">Students Monitored</p>
                  <p className="text-2xl font-bold text-gray-900">{totalStudents}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <Users className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm mb-1">Active Incidents</p>
                  <p className="text-2xl font-bold text-gray-900">{totalIncidents}</p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm mb-1">Examination Rooms</p>
                  <p className="text-2xl font-bold text-gray-900">{new Set(cameraFeeds.map(c => c.roomId)).size}</p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <Eye className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Phone Camera Monitor */}
          {showPhoneCamera && (
            <div className="mb-6">
              <PhoneCameraMonitor onClose={() => setShowPhoneCamera(false)} />
            </div>
          )}

          {/* Camera Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                Loading camera feeds...
              </div>
            ) : cameraFeeds.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                No camera feeds available
              </div>
            ) : (
              cameraFeeds.map((camera) => {
                const cameraId = camera.id || camera.camera_id;
                const roomName = camera.roomName || camera.room_name;
                const studentsMonitored = camera.studentsMonitored || camera.students_monitored || 0;
                const streamUrl = camera.streamUrl || camera.stream_url;
                
                return (
                  <div
                    key={cameraId}
                    className={`bg-white rounded-xl shadow-sm border-2 transition-all cursor-pointer ${
                      selectedCamera === cameraId
                        ? "border-purple-500 shadow-md"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => setSelectedCamera(cameraId)}
                  >
                {/* Video Feed Placeholder */}
                <div className="relative bg-gray-900 rounded-t-xl aspect-video overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    {streamUrl ? (
                      <video
                        src={streamUrl}
                        className="w-full h-full object-cover"
                        autoPlay
                        muted
                        playsInline
                      />
                    ) : (
                      <div className="text-center">
                        <Video className="h-16 w-16 text-gray-600 mx-auto mb-2" />
                        <p className="text-gray-400 text-sm">{cameraId}</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Status Indicator */}
                  <div className="absolute top-3 left-3 flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(camera.status)}`}></div>
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
                        // Handle fullscreen
                      }}
                      className="p-2 bg-black/50 rounded-lg hover:bg-black/70 transition-colors"
                    >
                      <Maximize2 className="h-4 w-4 text-white" />
                    </button>
                  </div>
                </div>

                {/* Camera Info */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{roomName}</h3>
                    <span className="text-xs text-gray-500">{cameraId}</span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center text-gray-600">
                      <Users className="h-4 w-4 mr-1" />
                      <span>{studentsMonitored} students</span>
                    </div>
                    {(camera.incidents || 0) > 0 && (
                      <div className="flex items-center text-red-600">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        <span>{camera.incidents} incidents</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
                );
              })
            )}
          </div>

          {/* Selected Camera Full View (Modal-like) */}
          {selectedCamera && (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8">
              <div className="bg-white rounded-xl w-full max-w-6xl">
                  <div className="relative bg-gray-900 rounded-t-xl aspect-video">
                  <div className="absolute inset-0 flex items-center justify-center">
                    {cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.streamUrl || 
                     cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.stream_url ? (
                      <video
                        src={cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.streamUrl || 
                             cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.stream_url}
                        className="w-full h-full object-cover"
                        autoPlay
                        muted
                        playsInline
                      />
                    ) : (
                      <Video className="h-32 w-32 text-gray-600" />
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedCamera(null)}
                    className="absolute top-4 right-4 p-2 bg-black/50 rounded-lg hover:bg-black/70 text-white"
                  >
                    ✕
                  </button>
                </div>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">
                    {cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.roomName || 
                     cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.room_name}
                  </h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-gray-600 text-sm">Camera ID</p>
                      <p className="font-medium">{selectedCamera}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Students</p>
                      <p className="font-medium">
                        {cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.studentsMonitored ||
                         cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.students_monitored || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Incidents</p>
                      <p className="font-medium text-red-600">
                        {cameraFeeds.find(c => (c.id || c.camera_id) === selectedCamera)?.incidents || 0}
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

export default MonitoringPage;

