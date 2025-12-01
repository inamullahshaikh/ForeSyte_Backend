import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { FileText, Download, Calendar, Filter, Search, Eye, X } from "lucide-react";
import { apiService } from "../services/api";

interface Report {
  id: string;
  title: string;
  type: "incident" | "exam" | "analytics";
  generatedAt: string;
  generatedBy: string;
  format: "pdf" | "csv" | "json";
  size: string;
  status: "completed" | "generating" | "failed";
}

interface Exam {
  id: string;
  name: string;
  course_code?: string;
  scheduled_date?: string;
  status?: string;
}

interface Incident {
  id: string;
  student_name: string;
  exam_name?: string;
  type: string;
  severity: string;
  timestamp: string;
  status: string;
}

const ReportsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [showExamModal, setShowExamModal] = useState(false);
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [exams, setExams] = useState<Exam[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedExam, setSelectedExam] = useState<string>("");
  const [selectedIncidents, setSelectedIncidents] = useState<string[]>([]);
  const [reportFormat, setReportFormat] = useState<"pdf" | "csv" | "json">("pdf");
  const [includeStatistics, setIncludeStatistics] = useState(true);
  const [includeVideoLinks, setIncludeVideoLinks] = useState(true);
  const [loadingExams, setLoadingExams] = useState(false);
  const [loadingIncidents, setLoadingIncidents] = useState(false);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await apiService.getReportHistory({ page: 1, limit: 50 });
      if (response.data?.reports) {
        const reportsData = response.data.reports.map((r: any) => ({
          id: r.id,
          title: r.title || r.name || `Report ${r.id}`,
          type: r.type || "incident",
          generatedAt: r.created_at || r.generated_at || new Date().toISOString(),
          generatedBy: r.generated_by || r.created_by || "System",
          format: r.format || "pdf",
          size: r.size || "0 KB",
          status: r.status || "completed",
        }));
        setReports(reportsData);
      }
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredReports = reports.filter(report => {
    const matchesSearch = 
      report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === "all" || report.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const getTypeColor = (type: string) => {
    switch (type) {
      case "incident": return "bg-red-100 text-red-800";
      case "exam": return "bg-blue-100 text-blue-800";
      case "analytics": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-100 text-green-800";
      case "generating": return "bg-yellow-100 text-yellow-800";
      case "failed": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const fetchExams = async () => {
    setLoadingExams(true);
    try {
      const response = await apiService.getExams({ page: 1, limit: 100 });
      if (response.data?.exams) {
        setExams(response.data.exams.map((exam: any) => ({
          id: exam.id || exam.exam_id,
          name: exam.name || exam.course || exam.course_code || "Unnamed Exam",
          course_code: exam.course_code || exam.course,
          scheduled_date: exam.scheduled_date || exam.exam_date,
          status: exam.status,
        })));
      }
    } catch (error) {
      console.error("Error fetching exams:", error);
      alert("Failed to load exams");
    } finally {
      setLoadingExams(false);
    }
  };

  const fetchIncidents = async () => {
    setLoadingIncidents(true);
    try {
      const response = await apiService.getIncidents({ page: 1, limit: 100 });
      if (response.data?.incidents) {
        setIncidents(response.data.incidents.map((inc: any) => ({
          id: inc.id,
          student_name: inc.student_name || "Unknown",
          exam_name: inc.exam_name,
          type: inc.type || "Unknown",
          severity: inc.severity || "low",
          timestamp: inc.timestamp,
          status: inc.status || "investigating",
        })));
      }
    } catch (error) {
      console.error("Error fetching incidents:", error);
      alert("Failed to load incidents");
    } finally {
      setLoadingIncidents(false);
    }
  };

  const handleOpenExamModal = () => {
    setSelectedExam("");
    setReportFormat("pdf");
    setIncludeStatistics(true);
    setShowExamModal(true);
    fetchExams();
  };

  const handleOpenIncidentModal = () => {
    setSelectedIncidents([]);
    setReportFormat("pdf");
    setIncludeVideoLinks(true);
    setShowIncidentModal(true);
    fetchIncidents();
  };

  const handleGenerateExamReport = async () => {
    if (!selectedExam) {
      alert("Please select an exam");
      return;
    }

    setGenerating("exam");
    setShowExamModal(false);
    
    try {
      const response = await apiService.generateExamReport(selectedExam, {
        format: reportFormat,
        include_statistics: includeStatistics,
      });

      if (!response.error) {
        alert("Report generation started. You'll be notified when it's ready.");
        fetchReports();
      } else {
        alert(response.error);
      }
    } catch (error) {
      console.error("Error generating exam report:", error);
      alert("Failed to generate report");
    } finally {
      setGenerating(null);
    }
  };

  const handleGenerateIncidentReport = async () => {
    if (selectedIncidents.length === 0) {
      alert("Please select at least one incident");
      return;
    }

    setGenerating("incident");
    setShowIncidentModal(false);
    
    try {
      const response = await apiService.generateIncidentReport({
        incident_ids: selectedIncidents,
        format: reportFormat,
        include_video_links: includeVideoLinks,
      });

      if (!response.error) {
        alert("Report generation started. You'll be notified when it's ready.");
        fetchReports();
      } else {
        alert(response.error);
      }
    } catch (error) {
      console.error("Error generating incident report:", error);
      alert("Failed to generate report");
    } finally {
      setGenerating(null);
    }
  };

  const toggleIncidentSelection = (incidentId: string) => {
    setSelectedIncidents((prev) =>
      prev.includes(incidentId)
        ? prev.filter((id) => id !== incidentId)
        : [...prev, incidentId]
    );
  };

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
                  Reports
                </h1>
                <p className="text-gray-600">
                  Generate and manage incident, exam, and analytics reports
                </p>
              </div>
            </div>
          </div>

          {/* Generate Report Section */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate New Report</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={handleOpenIncidentModal}
                disabled={generating === "incident"}
                className="flex items-center justify-center p-4 bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 transition-colors disabled:opacity-50"
              >
                {generating === "incident" ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-600 mr-2"></div>
                    <span className="font-medium text-gray-900">Generating...</span>
                  </>
                ) : (
                  <>
                    <FileText className="h-6 w-6 text-red-600 mr-2" />
                    <span className="font-medium text-gray-900">Incident Report</span>
                  </>
                )}
              </button>
              <button
                onClick={handleOpenExamModal}
                disabled={generating === "exam"}
                className="flex items-center justify-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors disabled:opacity-50"
              >
                {generating === "exam" ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2"></div>
                    <span className="font-medium text-gray-900">Generating...</span>
                  </>
                ) : (
                  <>
                    <FileText className="h-6 w-6 text-blue-600 mr-2" />
                    <span className="font-medium text-gray-900">Exam Report</span>
                  </>
                )}
              </button>
              <button
                onClick={() => handleGenerateReport("analytics")}
                disabled={generating === "analytics"}
                className="flex items-center justify-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
              >
                {generating === "analytics" ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600 mr-2"></div>
                    <span className="font-medium text-gray-900">Generating...</span>
                  </>
                ) : (
                  <>
                    <FileText className="h-6 w-6 text-purple-600 mr-2" />
                    <span className="font-medium text-gray-900">Analytics Report</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Search and Filter */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search reports..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Types</option>
                  <option value="incident">Incident</option>
                  <option value="exam">Exam</option>
                  <option value="analytics">Analytics</option>
                </select>
              </div>
            </div>
          </div>

          {/* Reports List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Report History</h2>
              
              <div className="space-y-3">
                {loading ? (
                  <div className="text-center py-8 text-gray-500">Loading reports...</div>
                ) : filteredReports.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No reports found</div>
                ) : (
                  filteredReports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="p-3 bg-white rounded-lg">
                        <FileText className="h-6 w-6 text-gray-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-1">
                          <h3 className="font-medium text-gray-900">{report.title}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(report.type)}`}>
                            {report.type}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                            {report.status}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {new Date(report.generatedAt).toLocaleString()}
                          </span>
                          <span>By: {report.generatedBy}</span>
                          <span>Format: {report.format.toUpperCase()}</span>
                          <span>Size: {report.size}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {report.status === "completed" && (
                        <>
                          <button className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
                            <Eye className="h-5 w-5 text-gray-600" />
                          </button>
                          <button className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
                            <Download className="h-5 w-5 text-gray-600" />
                          </button>
                        </>
                      )}
                      {report.status === "generating" && (
                        <div className="flex items-center text-yellow-600">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-2"></div>
                          <span className="text-sm">Generating...</span>
                        </div>
                      )}
                    </div>
                  </div>
                  ))
                )}
              </div>

              {filteredReports.length === 0 && (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No reports found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Exam Selection Modal */}
      {showExamModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Generate Exam Report</h2>
              <button
                onClick={() => setShowExamModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-600" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Exam <span className="text-red-500">*</span>
                </label>
                {loadingExams ? (
                  <div className="text-center py-4 text-gray-500">Loading exams...</div>
                ) : (
                  <select
                    value={selectedExam}
                    onChange={(e) => setSelectedExam(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">-- Select an exam --</option>
                    {exams.map((exam) => (
                      <option key={exam.id} value={exam.id}>
                        {exam.name} {exam.course_code ? `(${exam.course_code})` : ""} {exam.scheduled_date ? `- ${new Date(exam.scheduled_date).toLocaleDateString()}` : ""}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Format
                </label>
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as "pdf" | "csv" | "json")}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="pdf">PDF</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includeStatistics"
                  checked={includeStatistics}
                  onChange={(e) => setIncludeStatistics(e.target.checked)}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="includeStatistics" className="ml-2 text-sm text-gray-700">
                  Include statistics
                </label>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowExamModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateExamReport}
                  disabled={!selectedExam || generating === "exam"}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Incident Selection Modal */}
      {showIncidentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Generate Incident Report</h2>
              <button
                onClick={() => setShowIncidentModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-600" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Incidents <span className="text-red-500">*</span>
                  {selectedIncidents.length > 0 && (
                    <span className="ml-2 text-sm text-gray-500">
                      ({selectedIncidents.length} selected)
                    </span>
                  )}
                </label>
                {loadingIncidents ? (
                  <div className="text-center py-4 text-gray-500">Loading incidents...</div>
                ) : incidents.length === 0 ? (
                  <div className="text-center py-4 text-gray-500">No incidents found</div>
                ) : (
                  <div className="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
                    {incidents.map((incident) => (
                      <div
                        key={incident.id}
                        className={`p-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${
                          selectedIncidents.includes(incident.id) ? "bg-blue-50" : ""
                        }`}
                        onClick={() => toggleIncidentSelection(incident.id)}
                      >
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={selectedIncidents.includes(incident.id)}
                            onChange={() => toggleIncidentSelection(incident.id)}
                            className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded mr-3"
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900">{incident.student_name}</span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                incident.severity === "high" || incident.severity === "critical" 
                                  ? "bg-red-100 text-red-800"
                                  : incident.severity === "medium"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-green-100 text-green-800"
                              }`}>
                                {incident.severity}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {incident.type} {incident.exam_name && `• ${incident.exam_name}`}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {new Date(incident.timestamp).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Format
                </label>
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as "pdf" | "csv" | "json")}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="pdf">PDF</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includeVideoLinks"
                  checked={includeVideoLinks}
                  onChange={(e) => setIncludeVideoLinks(e.target.checked)}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="includeVideoLinks" className="ml-2 text-sm text-gray-700">
                  Include video links
                </label>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowIncidentModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateIncidentReport}
                  disabled={selectedIncidents.length === 0 || generating === "incident"}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;

