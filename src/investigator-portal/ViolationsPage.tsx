import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import {
  Filter,
  Search,
  Eye,
  CheckCircle,
  XCircle,
  Download,
  Calendar,
  User,
  MapPin,
} from "lucide-react";
import { apiService } from "../services/api";

interface Violation {
  violation_id: string;
  activity_id: string;
  violation_type: string;
  timestamp: string;
  severity: number;
  status: string;
  evidence_url?: string;
  student_id?: string;
  student_name?: string;
  seat_number?: string;
  room?: string;
  exam?: string;
}

const ViolationsPage = () => {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [filteredViolations, setFilteredViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    const loadViolations = async () => {
      setLoading(true);
      try {
        const response = await apiService.getViolations();
        if (response.data && Array.isArray(response.data)) {
          const apiViolations = response.data as any[];
          const mapped: Violation[] = apiViolations.map((v) => ({
            violation_id: v.violation_id,
            activity_id: v.activity_id,
            violation_type: v.violation_type,
            timestamp: v.timestamp,
            severity: v.severity,
            status: v.status,
            evidence_url: v.evidence_url,
            // Enriched fields (student/room) are not part of this API yet
            student_id: v.student_id,
            student_name: v.student_name,
            seat_number: v.seat_number,
            room: v.room,
            exam: v.exam,
          }));
          setViolations(mapped);
          setFilteredViolations(mapped);
        } else {
          setViolations([]);
          setFilteredViolations([]);
        }
      } catch (error) {
        console.error("Error fetching violations:", error);
      } finally {
        setLoading(false);
      }
    };

    loadViolations();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, statusFilter, severityFilter, typeFilter, violations]);

  const applyFilters = () => {
    let filtered = [...violations];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (v) =>
          v.student_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          v.student_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          v.seat_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          v.violation_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((v) => v.status === statusFilter);
    }

    // Severity filter
    if (severityFilter !== "all") {
      filtered = filtered.filter((v) => v.severity === parseInt(severityFilter));
    }

    // Type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter((v) => v.violation_type === typeFilter);
    }

    setFilteredViolations(filtered);
  };

  const handleConfirmViolation = async (violationId: string) => {
    try {
      await apiService.confirmViolation(violationId);

      // Update local state
      setViolations(
        violations.map((v) =>
          v.violation_id === violationId ? { ...v, status: "confirmed" } : v
        )
      );
      setShowDetailsModal(false);
    } catch (error) {
      console.error("Error confirming violation:", error);
    }
  };

  const handleDismissViolation = async (violationId: string) => {
    try {
      await apiService.dismissViolation(violationId);

      // Update local state
      setViolations(
        violations.map((v) =>
          v.violation_id === violationId ? { ...v, status: "dismissed" } : v
        )
      );
      setShowDetailsModal(false);
    } catch (error) {
      console.error("Error dismissing violation:", error);
    }
  };

  const handleViewDetails = (violation: Violation) => {
    setSelectedViolation(violation);
    setShowDetailsModal(true);
  };

  const getSeverityLabel = (severity: number) => {
    switch (severity) {
      case 3:
        return { label: "High", color: "bg-red-100 text-red-800" };
      case 2:
        return { label: "Medium", color: "bg-yellow-100 text-yellow-800" };
      case 1:
        return { label: "Low", color: "bg-blue-100 text-blue-800" };
      default:
        return { label: "Unknown", color: "bg-gray-100 text-gray-800" };
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "pending":
        return { label: "Pending", color: "bg-orange-100 text-orange-800" };
      case "confirmed":
        return { label: "Confirmed", color: "bg-green-100 text-green-800" };
      case "dismissed":
        return { label: "Dismissed", color: "bg-gray-100 text-gray-800" };
      default:
        return { label: status, color: "bg-gray-100 text-gray-800" };
    }
  };

  const violationTypes = Array.from(
    new Set(violations.map((v) => v.violation_type))
  );

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
          {/* Filters Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Student ID, Name, Seat..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="dismissed">Dismissed</option>
                </select>
              </div>

              {/* Severity Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity
                </label>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="all">All Severity</option>
                  <option value="3">High</option>
                  <option value="2">Medium</option>
                  <option value="1">Low</option>
                </select>
              </div>

              {/* Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Violation Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="all">All Types</option>
                  {violationTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Showing {filteredViolations.length} of {violations.length} violations
            </p>
          </div>

          {/* Violations Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Student Info
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Violation Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Severity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredViolations.map((violation) => {
                    const severityInfo = getSeverityLabel(violation.severity);
                    const statusInfo = getStatusLabel(violation.status);

                    return (
                      <tr key={violation.violation_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center">
                              <User className="w-5 h-5 text-indigo-900" />
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {violation.student_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                ID: {violation.student_id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {violation.violation_type}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center text-sm text-gray-500">
                            <MapPin className="w-4 h-4 mr-1" />
                            {violation.room} - {violation.seat_number}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center text-sm text-gray-500">
                            <Calendar className="w-4 h-4 mr-1" />
                            {new Date(violation.timestamp).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${severityInfo.color}`}
                          >
                            {severityInfo.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${statusInfo.color}`}
                          >
                            {statusInfo.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleViewDetails(violation)}
                            className="text-indigo-900 hover:text-indigo-700 flex items-center gap-1"
                          >
                            <Eye className="w-4 h-4" />
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedViolation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  Violation Details
                </h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Student Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Student Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Name</p>
                    <p className="font-medium">{selectedViolation.student_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Student ID</p>
                    <p className="font-medium">{selectedViolation.student_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Seat Number</p>
                    <p className="font-medium">{selectedViolation.seat_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Room</p>
                    <p className="font-medium">{selectedViolation.room}</p>
                  </div>
                </div>
              </div>

              {/* Violation Info */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Violation Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Type</p>
                    <p className="font-medium">{selectedViolation.violation_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Timestamp</p>
                    <p className="font-medium">
                      {new Date(selectedViolation.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Severity</p>
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        getSeverityLabel(selectedViolation.severity).color
                      }`}
                    >
                      {getSeverityLabel(selectedViolation.severity).label}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Status</p>
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        getStatusLabel(selectedViolation.status).color
                      }`}
                    >
                      {getStatusLabel(selectedViolation.status).label}
                    </span>
                  </div>
                </div>
              </div>

              {/* Evidence */}
              {selectedViolation.evidence_url && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Evidence</h3>
                  <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center">
                    <div className="text-center">
                      <Download className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600 mb-2">
                        Evidence: {selectedViolation.evidence_url}
                      </p>
                      <button className="text-indigo-900 hover:text-indigo-700 text-sm font-medium">
                        Download Evidence
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              {selectedViolation.status === "pending" && (
                <div className="flex gap-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleConfirmViolation(selectedViolation.violation_id)}
                    className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Confirm Violation
                  </button>
                  <button
                    onClick={() => handleDismissViolation(selectedViolation.violation_id)}
                    className="flex-1 bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <XCircle className="w-5 h-5" />
                    Dismiss Violation
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ViolationsPage;

