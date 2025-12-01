import React, { useState, useRef } from "react";
import { 
  Upload, 
  X, 
  FileText, 
  Image,
  CheckCircle,
  Clock,
  AlertCircle
} from "lucide-react";
import StudentHeader from "../components/Header";
import StudentSidebar from "../components/Sidebar";

type FileStatus = "verified" | "pending" | "rejected";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  type: "image" | "pdf";
  uploadedAt: string;
  status: FileStatus;
}

const StudentUploadPage: React.FC = () => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [files, setFiles] = useState<UploadedFile[]>([
    {
      id: "1",
      name: "exam_identification.jpg",
      size: "2.4",
      type: "image",
      uploadedAt: "2 days ago",
      status: "verified"
    },
    {
      id: "2",
      name: "degree_certificate.pdf",
      size: "1.8",
      type: "pdf",
      uploadedAt: "5 days ago",
      status: "verified"
    },
    {
      id: "3",
      name: "room_setup.jpg",
      size: "3.2",
      type: "image",
      uploadedAt: "1 week ago",
      status: "pending"
    }
  ]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      handleFiles(droppedFiles);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList: FileList): void => {
    const maxSize = 10 * 1024 * 1024;
    const validTypes = ["image/jpeg", "image/png", "application/pdf"];

    Array.from(fileList).forEach((file) => {
      if (file.size > maxSize) {
        alert(`File ${file.name} exceeds 10MB limit`);
        return;
      }

      if (!validTypes.includes(file.type)) {
        alert(`File type not supported for ${file.name}`);
        return;
      }

      const newFile: UploadedFile = {
        id: Date.now().toString(),
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(2),
        type: file.type.includes("pdf") ? "pdf" : "image",
        uploadedAt: "Just now",
        status: "pending"
      };

      setFiles([newFile, ...files]);
    });
  };

  const removeFile = (id: string): void => {
    setFiles(files.filter(f => f.id !== id));
  };

  const getStatusIcon = (status: FileStatus): React.ReactNode => {
    switch (status) {
      case "verified":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case "rejected":
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: FileStatus): string => {
    switch (status) {
      case "verified":
        return "bg-green-100 text-green-700";
      case "pending":
        return "bg-yellow-100 text-yellow-700";
      case "rejected":
        return "bg-red-100 text-red-700";
      default:
        return "";
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <StudentSidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <StudentHeader />
        
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Documents</h1>
            <p className="text-gray-600">Upload identification, certificates, and proof of setup</p>
          </div>

          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-200 mb-8">
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                dragActive
                  ? "border-purple-500 bg-purple-50"
                  : "border-gray-300 hover:border-purple-400"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload className="h-8 w-8 text-purple-600" />
                </div>
                <p className="text-gray-900 font-semibold mb-1">Drag your files here</p>
                <p className="text-gray-500 text-sm mb-4">or</p>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  Browse Files
                </button>
                <p className="text-gray-400 text-xs mt-4">
                  Supported: JPG, PNG, PDF (Max 10MB each)
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".jpg,.jpeg,.png,.pdf"
                onChange={handleChange}
                className="hidden"
              />
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                <span className="font-semibold">💡 Tip:</span> Upload high-quality images of your ID, exam setup, and any required documents. Verification typically completes within 24 hours.
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">My Uploads ({files.length})</h2>

            {files.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-100"
                  >
                    <div className="flex items-center space-x-4 flex-1">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        file.type === "pdf" ? "bg-red-100" : "bg-blue-100"
                      }`}>
                        {file.type === "pdf" ? (
                          <FileText className={`h-6 w-6 ${file.type === "pdf" ? "text-red-600" : "text-blue-600"}`} />
                        ) : (
                          <Image className="h-6 w-6 text-blue-600" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">{file.size} MB • {file.uploadedAt}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(file.status)}`}>
                        {getStatusIcon(file.status)}
                        <span className="capitalize">{file.status}</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => removeFile(file.id)}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        <X className="h-5 w-5 text-red-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentUploadPage;