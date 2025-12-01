import React, { useState } from "react";
import { 
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Eye,
} from "lucide-react";
import StudentHeader from "../components/Header";
import StudentSidebar from "../components/Sidebar";

type RecordStatus = "resolved" | "closed" | "active" | "pending";
type RecordSeverity = "high" | "medium" | "low";

interface DisciplinaryRecord {
  id: number;
  type: string;
  title: string;
  date: string;
  description: string;
  severity: RecordSeverity;
  status: RecordStatus;
  details: string;
  resolution: string;
}

interface StatsData {
  total: number;
  active: number;
  resolved: number;
}

const StudentDisciplinaryRecordsPage: React.FC = () => {
  const [expandedRecord, setExpandedRecord] = useState<number | null>(null);

  const records: DisciplinaryRecord[] = [
    {
      id: 1,
      type: "warning",
      title: "Minor Warning",
      date: "Sep 15, 2024",
      description: "Low background noise detection during exam",
      severity: "low",
      status: "resolved",
      details: "The system detected some background noise during your exam session. This is just a warning and does not affect your exam score.",
      resolution: "No action required. Please ensure a quiet environment for future exams."
    },
    {
      id: 2,
      type: "case",
      title: "Investigation Closed",
      date: "Aug 20, 2024",
      description: "Suspected abnormal pattern in response time",
      severity: "medium",
      status: "closed",
      details: "Your exam patterns were analyzed and found to be within normal ranges. The investigation has been closed.",
      resolution: "No violations found. Your academic standing remains excellent."
    }
  ];

  const stats: StatsData = {
    total: records.length,
    active: records.filter(r => r.status === "active").length,
    resolved: records.filter(r => r.status === "resolved" || r.status === "closed").length
  };

  const getSeverityColor = (severity: RecordSeverity): string => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-700 border-red-300";
      case "medium":
        return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case "low":
        return "bg-blue-100 text-blue-700 border-blue-300";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  const getStatusIcon = (status: RecordStatus): React.ReactNode => {
    switch (status) {
      case "resolved":
      case "closed":
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case "active":
        return <AlertCircle className="h-6 w-6 text-red-600" />;
      case "pending":
        return <Clock className="h-6 w-6 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: RecordStatus): string => {
    switch (status) {
      case "resolved":
      case "closed":
        return "bg-green-50 border-green-200";
      case "active":
        return "bg-red-50 border-red-200";
      case "pending":
        return "bg-yellow-50 border-yellow-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <StudentSidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <StudentHeader />
        
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Disciplinary Records</h1>
            <p className="text-gray-600">Your academic integrity and exam conduct records</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <p className="text-gray-600 text-sm mb-2">Total Records</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <p className="text-gray-600 text-sm mb-2">Active Cases</p>
              <div className="flex items-center space-x-2">
                <p className="text-3xl font-bold text-red-600">{stats.active}</p>
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <p className="text-gray-600 text-sm mb-2">Resolved</p>
              <div className="flex items-center space-x-2">
                <p className="text-3xl font-bold text-green-600">{stats.resolved}</p>
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          {stats.active === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-green-900">Clean Record</p>
                  <p className="text-sm text-green-700">You have no active disciplinary cases. Keep maintaining academic integrity!</p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {records.length === 0 ? (
              <div className="bg-white rounded-xl p-12 shadow-sm border border-gray-200 text-center">
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                <p className="text-gray-600 text-lg">No records on file</p>
              </div>
            ) : (
              records.map((record) => (
                <div
                  key={record.id}
                  className={`bg-white rounded-xl border-2 transition-all ${getStatusColor(record.status)}`}
                >
                  <div
                    className="p-6 cursor-pointer"
                    onClick={() => setExpandedRecord(expandedRecord === record.id ? null : record.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4 flex-1">
                        <div className="pt-1">
                          {getStatusIcon(record.status)}
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="font-semibold text-gray-900">{record.title}</h3>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(record.severity)}`}>
                              {record.severity.charAt(0).toUpperCase() + record.severity.slice(1)}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              record.status === "resolved" || record.status === "closed"
                                ? "bg-green-100 text-green-700"
                                : record.status === "active"
                                ? "bg-red-100 text-red-700"
                                : "bg-yellow-100 text-yellow-700"
                            }`}>
                              {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                            </span>
                          </div>
                          <p className="text-gray-600 text-sm mb-2">{record.description}</p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>{record.date}</span>
                            <span>•</span>
                            <span className="flex items-center space-x-1">
                              <FileText className="h-3 w-3" />
                              <span>Case ID: #{record.id}</span>
                            </span>
                          </div>
                        </div>
                      </div>

                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Eye className={`h-5 w-5 text-gray-400 transition-transform ${expandedRecord === record.id ? "rotate-180" : ""}`} />
                      </button>
                    </div>
                  </div>

                  {expandedRecord === record.id && (
                    <div className="border-t px-6 py-4 bg-gray-50">
                      <div className="space-y-4">
                        <div>
                          <p className="text-sm font-semibold text-gray-900 mb-2">Details</p>
                          <p className="text-sm text-gray-600">{record.details}</p>
                        </div>

                        <div>
                          <p className="text-sm font-semibold text-gray-900 mb-2">Resolution</p>
                          <p className="text-sm text-gray-600">{record.resolution}</p>
                        </div>

                        <div className="pt-2 border-t border-gray-200">
                          <button className="text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors">
                            Appeal This Record →
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-3">Need Help?</h3>
            <p className="text-sm text-blue-700 mb-4">
              If you believe there's an error in your record or wish to appeal a disciplinary decision, please contact our support team.
            </p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm">
              Contact Support
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDisciplinaryRecordsPage;