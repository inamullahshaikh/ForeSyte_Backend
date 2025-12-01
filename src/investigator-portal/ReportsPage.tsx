import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import {
  FileText,
  Download,
  Filter,
  Search,
  Calendar,
  Eye,
  Plus,
} from "lucide-react";
import { apiService } from "../services/api";

interface Report {
  report_id: string;
  report_type: string;
  generated_date: string;
  file_path: string;
  violation_count?: number;
  exam_name?: string;
  generated_by?: string;
}

const ReportsPage = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [filteredReports, setFilteredReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  // Generate Report Form
  const [reportType, setReportType] = useState<"incident" | "exam">("incident");
  const [selectedIncidents, setSelectedIncidents] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<"pdf" | "excel" | "csv">("pdf");
  const [includeVideoLinks, setIncludeVideoLinks] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, typeFilter, reports]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await apiService.getReports({ page: 1, limit: 50 });
      if (response.data && (response.data as any).reports) {
        const { reports: apiReports } = response.data as any;
        const mapped: Report[] = apiReports.map((r: any) => ({
          report_id: r.report_id || r.id,
          report_type: r.report_type,
          generated_date: r.generated_date,
          file_path: r.file_path,
          // Backend currently doesn’t expose violation_count/exam_name/generated_by directly
          violation_count: r.violation_count,
          exam_name: r.exam_name,
          generated_by: r.generated_by_name || r.generated_by,
        }));
        setReports(mapped);
        setFilteredReports(mapped);
      } else {
        setReports([]);
        setFilteredReports([]);
      }
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...reports];

    if (searchTerm) {
      filtered = filtered.filter(
        (r) =>
          r.exam_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          r.report_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
          r.generated_by?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== "all") {
      filtered = filtered.filter((r) => r.report_type === typeFilter);
    }

    setFilteredReports(filtered);
  };

  const handleDownloadReport = async (report: Report) => {
    try {
      // Get the auth token for the download request
      const token = sessionStorage.getItem('token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      const downloadUrl = `${API_BASE_URL}/reports/${report.report_id}/download`;
      
      // Fetch the file with authorization header
      const response = await fetch(downloadUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Download failed: ${response.status}`);
      }
      
      // Get the blob and trigger download
      const blob = await response.blob();
      
      // Verify blob is not empty
      if (blob.size === 0) {
        throw new Error('Downloaded file is empty');
      }
      
      // Get filename from Content-Disposition header or use report file path
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = report.file_path.split('/').pop() || `report_${report.report_id}.pdf`;
      if (contentDisposition) {
        // Try to extract filename from Content-Disposition header
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '').trim();
        }
      }
      
      // Ensure filename has .pdf extension
      if (!filename.toLowerCase().endsWith('.pdf')) {
        filename += '.pdf';
      }
      
      // Create blob URL and download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename; // This forces download instead of opening
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Clean up after a short delay to ensure download starts
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 200);
    } catch (error) {
      console.error("Error downloading report:", error);
      alert(`Failed to download report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleViewReport = async (report: Report) => {
    try {
      // Get the auth token for the view request
      const token = sessionStorage.getItem('token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      // Use the view endpoint which serves with inline disposition
      const viewUrl = `${API_BASE_URL}/reports/${report.report_id}/view`;
      
      // Fetch the content
      const response = await fetch(viewUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Failed to view report: ${response.status}`);
      }
      
      // Check content type
      const contentType = response.headers.get('content-type') || '';
      
      if (contentType.includes('text/html')) {
        // For HTML responses, get text and open in new window
        const htmlContent = await response.text();
        const newWindow = window.open('', '_blank');
        if (newWindow) {
          newWindow.document.write(htmlContent);
          newWindow.document.close();
        } else {
          alert('Popup blocked. Please allow popups for this site.');
        }
      } else {
        // For PDFs and other files, create blob URL
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
          // Popup blocked, try alternative method
          const link = document.createElement('a');
          link.href = url;
          link.target = '_blank';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    } catch (error) {
      console.error("Error viewing report:", error);
      alert(`Failed to view report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleGenerateReport = async () => {
    try {
      if (reportType === "incident") {
        await apiService.generateIncidentReport({
          incident_ids: selectedIncidents,
          // Map UI formats to backend supported ones
          format: exportFormat === "excel" ? "csv" : "pdf",
          include_video_links: includeVideoLinks,
        });
      } else {
        // For exam report we’ll need an exam id – for now call with a placeholder or extend UI later
        // Here we simply skip if no exam is chosen
        alert("Exam report generation requires selecting an exam. Please extend UI to choose an exam.");
      }

      alert("Report generation started. You will be notified when it's ready.");
      setShowGenerateModal(false);
      
      // Refresh reports list
      fetchReports();
    } catch (error) {
      console.error("Error generating report:", error);
    }
  };

  const getReportTypeLabel = (type: string) => {
    switch (type) {
      case "incident":
        return { label: "Incident Report", color: "bg-orange-100 text-orange-800" };
      case "exam":
        return { label: "Exam Report", color: "bg-blue-100 text-blue-800" };
      default:
        return { label: type, color: "bg-gray-100 text-gray-800" };
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
            <h2 className="text-2xl font-bold text-gray-900">Generated Reports</h2>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="bg-indigo-900 text-white px-6 py-3 rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 font-medium"
            >
              <Plus className="w-5 h-5" />
              Generate New Report
            </button>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Exam Name, Type, Author..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="all">All Types</option>
                  <option value="incident">Incident Reports</option>
                  <option value="exam">Exam Reports</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Showing {filteredReports.length} of {reports.length} reports
            </p>
          </div>

          {/* Reports Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredReports.map((report) => {
              const typeInfo = getReportTypeLabel(report.report_type);
              return (
                <div
                  key={report.report_id}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-indigo-100 rounded-lg">
                      <FileText className="w-8 h-8 text-indigo-900" />
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${typeInfo.color}`}
                    >
                      {typeInfo.label}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {report.exam_name}
                  </h3>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      {new Date(report.generated_date).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Violations:</span>{" "}
                      {report.violation_count}
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Generated by:</span>{" "}
                      {report.generated_by}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDownloadReport(report)}
                      className="flex-1 bg-indigo-900 text-white px-4 py-2 rounded-lg hover:bg-indigo-800 transition-colors flex items-center justify-center gap-2 text-sm font-medium"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                    <button 
                      onClick={() => handleViewReport(report)}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                      title="View Report"
                    >
                      <Eye className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  Generate New Report
                </h2>
                <button
                  onClick={() => setShowGenerateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Report Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Type
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as "incident" | "exam")}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="incident">Incident Report</option>
                  <option value="exam">Exam Report</option>
                </select>
              </div>

              {/* Export Format */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {["pdf", "excel", "csv"].map((format) => (
                    <button
                      key={format}
                      onClick={() => setExportFormat(format as "pdf" | "excel" | "csv")}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        exportFormat === format
                          ? "bg-indigo-900 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Options */}
              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeVideoLinks}
                    onChange={(e) => setIncludeVideoLinks(e.target.checked)}
                    className="w-4 h-4 text-indigo-900 border-gray-300 rounded focus:ring-indigo-900"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Include video evidence links
                  </span>
                </label>
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    To Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setShowGenerateModal(false)}
                  className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateReport}
                  className="flex-1 bg-indigo-900 text-white px-6 py-3 rounded-lg hover:bg-indigo-800 transition-colors font-medium"
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

