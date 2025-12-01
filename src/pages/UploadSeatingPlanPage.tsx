import React, { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, CheckCircle, Loader2 } from "lucide-react";
import Button from "../components/Button";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
interface ExtractedData {
  message: string;
  exam_date: string;
  exam_time: string;
  course: string;
  room_no: string;
  students_count: number;
  json_file?: string;
}

const MAX_FILE_SIZE_MB = 20;

const UploadSeatingPlanPage: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string>("");
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [roomNo, setRoomNo] = useState<string>("");
  const [timeSlot, setTimeSlot] = useState<string>("");
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const validateAndSet = useCallback((f: File) => {
    setError("");
    if (f.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      setFile(null);
      return;
    }
    const sizeMb = f.size / (1024 * 1024);
    if (sizeMb > MAX_FILE_SIZE_MB) {
      setError(`File is too large. Max ${MAX_FILE_SIZE_MB}MB allowed.`);
      setFile(null);
      return;
    }
    setFile(f);
  }, []);

  const onInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) validateAndSet(f);
  }, [validateAndSet]);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) validateAndSet(f);
  }, [validateAndSet]);

  const onDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const onSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF to upload.");
      return;
    }

    setLoading(true);
    setError("");
    setExtractedData(null);

    const formData = new FormData();
    formData.append('file', file);

    // Build URL with query parameters
    const params = new URLSearchParams();
    if (roomNo.trim()) {
      params.append('room_no', roomNo.trim());
    }
    if (timeSlot.trim()) {
      params.append('time_slot', timeSlot.trim());
    }

    const url = `http://127.0.0.1:8000/upload-seating-plan${params.toString() ? '?' + params.toString() : ''}`;

    try {
      console.log('Sending request to:', url);
      console.log('With data:', {
        file: file.name,
        room: roomNo,
        timeSlot
      });
      
      const token = sessionStorage.getItem('token');
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        let errorMessage: string;
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || `Server error: ${response.status}`;
        } catch {
          errorMessage = `Failed to parse error response: ${response.status}`;
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('Success response:', data);
      
      if (data.error) {
        setError(data.error);
      } else {
        setExtractedData(data);
        setUploadSuccess(true);
        // Redirect to seating plans page after 2 seconds, with state to force refresh
        setTimeout(() => {
          navigate('/seating-plans', { state: { refresh: true } });
        }, 2000);
      }
    } catch (err) {
      console.error('Upload error:', err);
      if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
        setError('Cannot connect to server. Please check if the server is running.');
      } else {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  }, [file, roomNo, timeSlot]);

  return (
    <div className="flex h-screen relative">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {/* Loading Overlay with Enhanced Animations */}
          {loading && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md" style={{ pointerEvents: 'auto' }}>
              {/* Animated Background Elements */}
              <div className="absolute inset-0 overflow-hidden">
                {/* Subtle Background */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50/50 to-blue-50/50"></div>
              </div>

              {/* Main Loading Card */}
              <div className="relative z-10 bg-white rounded-2xl p-8 shadow-lg max-w-md mx-4">
                {/* Minimal Icon */}
                <div className="flex justify-center mb-6">
                  <div className="relative">
                    {/* Single Subtle Ring */}
                    <div className="absolute -inset-3 border-2 border-purple-200 rounded-full animate-spin" style={{ animationDuration: '3s' }}></div>
                    
                    {/* Simple Icon */}
                    <div className="relative w-16 h-16 bg-purple-100 rounded-xl flex items-center justify-center">
                      <Upload className="w-8 h-8 text-purple-600" />
                    </div>
                  </div>
                </div>
                
                {/* Loading Text */}
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold mb-2 text-gray-800">
                    Processing Your Seating Plan
                  </h3>
                  <p className="text-gray-500 text-sm">Extracting data from PDF and saving to database...</p>
                </div>
                
                {/* Simple Progress Bar */}
                <div className="mb-6">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="h-full bg-purple-600 rounded-full animate-progress" style={{ width: '70%' }}></div>
                  </div>
                </div>
                
                {/* Status Steps */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-gray-600">File uploaded successfully</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                    <span className="text-gray-600">Extracting seating information...</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                    <span className="text-gray-400">Saving to database...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div className={`min-h-full p-8 transition-all duration-300 ${loading ? 'pointer-events-none opacity-30 blur-sm' : 'opacity-100'}`}>
            <div className="max-w-2xl mx-auto bg-white rounded-2xl p-8 border border-gray-200 shadow-lg mb-8">
              <h1 className="text-center text-gray-900 text-2xl font-semibold mb-6">
                Upload Seating Plan (PDF)
              </h1>

              <form className="space-y-6" onSubmit={onSubmit}>
                <div
                  onDrop={onDrop}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  className={`w-full border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    isDragging ? "border-purple-500 bg-purple-50" : "border-gray-300 bg-gray-50"
                  }`}
                >
                  <input
                    ref={inputRef}
                    id="pdf-input"
                    type="file"
                    accept="application/pdf"
                    onChange={onInputChange}
                    className="hidden"
                  />

                  <div className="text-gray-700">
                    <p className="mb-3">Drag and drop your PDF here</p>
                    <p className="text-sm text-gray-500">or</p>
                  </div>
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => inputRef.current?.click()}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                      Choose PDF
                    </button>
                  </div>

                  {file && (
                    <div className="mt-4 text-gray-900">
                      Selected: <span className="font-medium">{file.name}</span>
                    </div>
                  )}

                  {error && (
                    <div className="mt-3 text-red-600 text-sm">{error}</div>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="room-no" className="block text-sm font-medium text-gray-700">
                    Room Number (Optional)
                  </label>
                  <input
                    id="room-no"
                    type="text"
                    value={roomNo}
                    onChange={(e) => setRoomNo(e.target.value)}
                    placeholder="e.g. C-301"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="time-slot" className="block text-sm font-medium text-gray-700">
                    Time Slot (Optional)
                  </label>
                  <input
                    id="time-slot"
                    type="text"
                    value={timeSlot}
                    onChange={(e) => setTimeSlot(e.target.value)}
                    placeholder="e.g. 10:20 AM to 11:20 AM"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>

                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    {loading ? "Uploading..." : "Upload"}
                  </button>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => {
                      setFile(null);
                      setError("");
                      setRoomNo("");
                      setTimeSlot("");
                      setExtractedData(null);
                      if (inputRef.current) inputRef.current.value = "";
                    }}
                    className="flex-1 px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                  >
                    Clear
                  </button>
                </div>
              </form>

              {uploadSuccess && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-medium">✓ Seating plan uploaded successfully!</p>
                  <p className="text-green-700 text-sm mt-1">Redirecting to Seating Plans page...</p>
                </div>
              )}

              {extractedData && (
                <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">
                    Extracted Information
                  </h2>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Course</dt>
                      <dd className="mt-1 text-sm text-gray-900">{extractedData.course}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Room</dt>
                      <dd className="mt-1 text-sm text-gray-900">{extractedData.room_no}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Exam Date</dt>
                      <dd className="mt-1 text-sm text-gray-900">{extractedData.exam_date}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Exam Time</dt>
                      <dd className="mt-1 text-sm text-gray-900">{extractedData.exam_time}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Students Count</dt>
                      <dd className="mt-1 text-sm text-gray-900">{extractedData.students_count}</dd>
                    </div>
                  </dl>
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => navigate('/seating-plans')}
                      className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      View Seating Plans
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadSeatingPlanPage;