import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import {
  Filter,
  Search,
  Eye,
  Calendar,
  User,
  MapPin,
  Activity,
} from "lucide-react";
import { apiService } from "../services/api";

interface StudentActivity {
  activity_id: string;
  student_id: string;
  exam_id: string;
  timestamp: string;
  activity_type: string;
  severity?: string;
  confidence?: number;
  evidence_url?: string;
  student_name?: string;
  seat_number?: string;
  room?: string;
  exam_name?: string;
}

const StudentActivitiesPage = () => {
  const [activities, setActivities] = useState<StudentActivity[]>([]);
  const [filteredActivities, setFilteredActivities] = useState<StudentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState<StudentActivity | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    const loadActivities = async () => {
      setLoading(true);
      try {
        const response = await apiService.getStudentActivities();
        if (response.data && Array.isArray(response.data)) {
          const apiActivities = response.data as any[];
          const mapped: StudentActivity[] = apiActivities.map((a) => ({
            activity_id: a.activity_id,
            student_id: a.student_id,
            exam_id: a.exam_id,
            timestamp: a.timestamp,
            activity_type: a.activity_type,
            severity: a.severity,
            confidence: a.confidence,
            evidence_url: a.evidence_url,
            // Friendly fields like names/room/seat aren't provided yet
            student_name: a.student_name,
            seat_number: a.seat_number,
            room: a.room,
            exam_name: a.exam_name,
          }));
          setActivities(mapped);
          setFilteredActivities(mapped);
        } else {
          setActivities([]);
          setFilteredActivities([]);
        }
      } catch (error) {
        console.error("Error fetching activities:", error);
      } finally {
        setLoading(false);
      }
    };

    loadActivities();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, severityFilter, typeFilter, activities]);

  const applyFilters = () => {
    let filtered = [...activities];

    if (searchTerm) {
      filtered = filtered.filter(
        (a) =>
          a.student_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.student_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.seat_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.activity_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (severityFilter !== "all") {
      filtered = filtered.filter((a) => a.severity === severityFilter);
    }

    if (typeFilter !== "all") {
      filtered = filtered.filter((a) => a.activity_type === typeFilter);
    }

    setFilteredActivities(filtered);
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const activityTypes = Array.from(new Set(activities.map((a) => a.activity_type)));

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
          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Activity Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                >
                  <option value="all">All Types</option>
                  {activityTypes.map((type) => (
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
              Showing {filteredActivities.length} of {activities.length} activities
            </p>
          </div>

          {/* Activities Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Student
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Activity Type
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
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredActivities.map((activity) => (
                    <tr key={activity.activity_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center">
                            <User className="w-5 h-5 text-indigo-900" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {activity.student_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {activity.student_id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-900">
                          <Activity className="w-4 h-4 mr-2 text-gray-500" />
                          {activity.activity_type}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <MapPin className="w-4 h-4 mr-1" />
                          {activity.room} - {activity.seat_number}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(activity.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getSeverityColor(
                            activity.severity
                          )}`}
                        >
                          {activity.severity?.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {activity.confidence
                          ? `${(activity.confidence * 100).toFixed(0)}%`
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => {
                            setSelectedActivity(activity);
                            setShowDetailsModal(true);
                          }}
                          className="text-indigo-900 hover:text-indigo-700 flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedActivity && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Activity Details</h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Student Name</p>
                  <p className="font-medium">{selectedActivity.student_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Student ID</p>
                  <p className="font-medium">{selectedActivity.student_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Activity Type</p>
                  <p className="font-medium">{selectedActivity.activity_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Severity</p>
                  <span
                    className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getSeverityColor(
                      selectedActivity.severity
                    )}`}
                  >
                    {selectedActivity.severity?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Location</p>
                  <p className="font-medium">
                    {selectedActivity.room} - {selectedActivity.seat_number}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Confidence</p>
                  <p className="font-medium">
                    {selectedActivity.confidence
                      ? `${(selectedActivity.confidence * 100).toFixed(0)}%`
                      : "N/A"}
                  </p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">Timestamp</p>
                  <p className="font-medium">
                    {new Date(selectedActivity.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>

              {selectedActivity.evidence_url && (
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600 mb-2">Evidence</p>
                  <p className="text-sm text-indigo-900">{selectedActivity.evidence_url}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentActivitiesPage;

