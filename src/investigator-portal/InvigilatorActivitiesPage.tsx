import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import { Filter, Search, Eye, Calendar, Users, MapPin } from "lucide-react";
import { apiService } from "../services/api";

interface InvigilatorActivity {
  activity_id: string;
  invigilator_id: string;
  room_id: string;
  timestamp: string;
  activity_type: string;
  notes?: string;
  invigilator_name?: string;
  room_number?: string;
}

const InvigilatorActivitiesPage = () => {
  const [activities, setActivities] = useState<InvigilatorActivity[]>([]);
  const [filteredActivities, setFilteredActivities] = useState<InvigilatorActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState<InvigilatorActivity | null>(
    null
  );
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    const loadActivities = async () => {
      setLoading(true);
      try {
        const response = await apiService.getInvigilatorActivities();
        if (response.data && Array.isArray(response.data)) {
          const apiActivities = response.data as any[];
          const mapped: InvigilatorActivity[] = apiActivities.map((a) => ({
            activity_id: a.activity_id,
            invigilator_id: a.invigilator_id,
            room_id: a.room_id,
            timestamp: a.timestamp,
            activity_type: a.activity_type,
            notes: a.notes,
            // Friendly fields are not returned by the API yet; fall back to IDs
            invigilator_name: a.invigilator_name,
            room_number: a.room_number,
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
  }, [searchTerm, typeFilter, activities]);

  const applyFilters = () => {
    let filtered = [...activities];

    if (searchTerm) {
      filtered = filtered.filter(
        (a) =>
          a.invigilator_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.room_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.activity_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== "all") {
      filtered = filtered.filter((a) => a.activity_type === typeFilter);
    }

    setFilteredActivities(filtered);
  };

  const getActivityTypeColor = (type: string) => {
    switch (type) {
      case "Phone Usage":
      case "Absent from Zone":
      case "Idle Period":
        return "bg-red-100 text-red-800";
      case "Walking Around":
      case "Entered Room":
        return "bg-green-100 text-green-800";
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Invigilator Name, Room..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
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
                      Invigilator
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Activity Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Room
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Notes
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
                          <div className="flex-shrink-0 h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                            <Users className="w-5 h-5 text-purple-900" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {activity.invigilator_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {activity.invigilator_id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getActivityTypeColor(
                            activity.activity_type
                          )}`}
                        >
                          {activity.activity_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <MapPin className="w-4 h-4 mr-1" />
                          {activity.room_number}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(activity.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-500 max-w-xs truncate">
                          {activity.notes || "No notes"}
                        </div>
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
                <h2 className="text-2xl font-bold text-gray-900">
                  Invigilator Activity Details
                </h2>
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
                  <p className="text-sm text-gray-600">Invigilator Name</p>
                  <p className="font-medium">{selectedActivity.invigilator_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Invigilator ID</p>
                  <p className="font-medium">{selectedActivity.invigilator_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Activity Type</p>
                  <span
                    className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getActivityTypeColor(
                      selectedActivity.activity_type
                    )}`}
                  >
                    {selectedActivity.activity_type}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Room</p>
                  <p className="font-medium">{selectedActivity.room_number}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">Timestamp</p>
                  <p className="font-medium">
                    {new Date(selectedActivity.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">Notes</p>
                  <p className="font-medium">{selectedActivity.notes || "No notes available"}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvigilatorActivitiesPage;

