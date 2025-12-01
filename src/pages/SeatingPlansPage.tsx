import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { Search, Filter, Upload, Eye, Trash2, FileText, Calendar, Users, RefreshCw } from "lucide-react";
import { apiService } from "../services/api";
import { useNavigate, useLocation } from "react-router-dom";

interface SeatInfo {
  seat_number: string;
  row?: string;
  column?: string;
  assigned_student_id?: string;
  assigned_student_name?: string;
}

interface RoomInfo {
  room_id: string;
  room_name: string;
  capacity: number;
  seats: SeatInfo[];
}

interface SeatingPlan {
  id: string;
  filename: string;
  uploaded_by: string;
  uploaded_at: string;
  status: string;
  total_seats?: number;
  rooms?: RoomInfo[];
}

const SeatingPlansPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [plans, setPlans] = useState<SeatingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [selectedPlan, setSelectedPlan] = useState<SeatingPlan | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Reset to first page when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filterStatus]);

  // Main fetch effect
  useEffect(() => {
    fetchPlans();
  }, [currentPage, filterStatus]);

  // Refresh when navigating from upload page
  useEffect(() => {
    if (location.state?.refresh) {
      // Clear the refresh flag
      navigate(location.pathname, { replace: true, state: {} });
      // Small delay to ensure backend has committed the data, then refresh
      setTimeout(() => {
        setCurrentPage(1);
        setFilterStatus("all");
        fetchPlans();
      }, 1000);
    }
  }, [location.state]);

  const fetchPlans = async () => {
    setLoading(true);
    try {
      const response = await apiService.getSeatingPlans({
        status: filterStatus !== "all" ? filterStatus : undefined,
        page: currentPage,
        limit: 20,
      });

      console.log("Seating plans response:", response);

      if (response.data) {
        const plansData = response.data.plans || [];
        console.log("Plans data:", plansData);
        setPlans(plansData);
        if (response.data.total && response.data.limit) {
          setTotalPages(Math.ceil(response.data.total / response.data.limit));
        } else {
          setTotalPages(1);
        }
      } else if (response.error) {
        console.error("API Error:", response.error);
        alert(`Error loading seating plans: ${response.error}`);
      }
    } catch (error) {
      console.error("Error fetching seating plans:", error);
      alert("Failed to load seating plans. Please refresh the page.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (planId: string) => {
    if (window.confirm("Are you sure you want to delete this seating plan?")) {
      try {
        const response = await apiService.deleteSeatingPlan(planId);
        if (!response.error) {
          fetchPlans();
        } else {
          alert(response.error);
        }
      } catch (error) {
        console.error("Error deleting seating plan:", error);
        alert("Failed to delete seating plan");
      }
    }
  };

  const handleViewDetails = async (planId: string) => {
    try {
      const response = await apiService.getSeatingPlanById(planId);
      if (response.data) {
        setSelectedPlan(response.data);
      } else {
        alert(response.error || "Failed to load plan details");
      }
    } catch (error) {
      console.error("Error fetching plan details:", error);
      alert("Failed to load plan details");
    }
  };

  const filteredPlans = plans.filter((plan) => {
    const matchesSearch =
      plan.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plan.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (plan.uploaded_by && plan.uploaded_by.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
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
                  Seating Plans
                </h1>
                <p className="text-gray-600">
                  View and manage uploaded seating plan documents
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    setCurrentPage(1);
                    setFilterStatus("all");
                    setSearchQuery("");
                    fetchPlans();
                  }}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  title="Refresh seating plans"
                >
                  <RefreshCw className="h-5 w-5" />
                  <span>Refresh</span>
                </button>
                <button
                  onClick={() => navigate("/upload-seating-plan")}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Upload className="h-5 w-5" />
                  <span>Upload Plan</span>
                </button>
              </div>
            </div>
          </div>

          {/* Search and Filter */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-6">
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search plans by filename, ID, or uploader..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <select
                  value={filterStatus}
                  onChange={(e) => {
                    setFilterStatus(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="processing">Processing</option>
                </select>
              </div>
            </div>
          </div>

          {/* Plans List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-4 px-6">Plan Details</th>
                    <th className="pb-4 px-6">Status</th>
                    <th className="pb-4 px-6">Total Seats</th>
                    <th className="pb-4 px-6">Rooms</th>
                    <th className="pb-4 px-6">Uploaded</th>
                    <th className="pb-4 px-6">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-gray-500">
                        Loading seating plans...
                      </td>
                    </tr>
                  ) : filteredPlans.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-gray-500">
                        No seating plans found
                      </td>
                    </tr>
                  ) : (
                    filteredPlans.map((plan) => (
                      <tr 
                        key={plan.id} 
                        className="border-b hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleViewDetails(plan.id)}
                      >
                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-purple-50 rounded-lg">
                              <FileText className="h-5 w-5 text-purple-600" />
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{plan.filename}</div>
                              <div className="text-sm text-gray-500">
                                ID: {plan.id} • By: {plan.uploaded_by}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(plan.status)}`}>
                            {plan.status}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-gray-900">
                          {plan.total_seats || "N/A"}
                        </td>
                        <td className="py-4 px-6 text-gray-900">
                          {plan.rooms ? plan.rooms.length : "N/A"}
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          {formatDate(plan.uploaded_at)}
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewDetails(plan.id);
                              }}
                              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              title="View Details"
                            >
                              <Eye className="h-4 w-4 text-gray-600" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(plan.id);
                              }}
                              className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Plan Details Modal */}
      {selectedPlan && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-8">
          <div className="bg-white rounded-xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
              <h2 className="text-xl font-semibold text-gray-900">Complete Seating Plan</h2>
              <button
                onClick={() => setSelectedPlan(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              {/* Plan Info Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 pb-6 border-b border-gray-200">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Filename</p>
                  <p className="font-medium text-gray-900 text-sm">{selectedPlan.filename}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Status</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedPlan.status)}`}>
                    {selectedPlan.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Total Seats</p>
                  <p className="font-medium text-gray-900">{selectedPlan.total_seats || "N/A"}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Uploaded At</p>
                  <p className="font-medium text-gray-900 text-sm">{formatDate(selectedPlan.uploaded_at)}</p>
                </div>
              </div>

              {/* Complete Seating Plan */}
              {selectedPlan.rooms && selectedPlan.rooms.length > 0 ? (
                <div className="space-y-6">
                  {selectedPlan.rooms.map((room, roomIndex) => (
                    <div key={room.room_id} className="border border-gray-200 rounded-lg overflow-hidden">
                      {/* Room Header */}
                      <div className="bg-purple-50 px-6 py-4 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900">{room.room_name}</h3>
                            <p className="text-sm text-gray-500">Room ID: {room.room_id}</p>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <div className="flex items-center">
                              <Users className="h-4 w-4 mr-1" />
                              <span>Capacity: {room.capacity}</span>
                            </div>
                            <div className="flex items-center">
                              <FileText className="h-4 w-4 mr-1" />
                              <span>Seats: {room.seats?.length || 0}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Seating Arrangement */}
                      <div className="p-6">
                        {room.seats && room.seats.length > 0 ? (
                          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                            {room.seats.map((seat, seatIndex) => (
                              <div
                                key={seatIndex}
                                className={`p-3 rounded-lg border-2 ${
                                  seat.assigned_student_id
                                    ? "bg-green-50 border-green-300"
                                    : "bg-gray-50 border-gray-200"
                                }`}
                              >
                                <div className="text-xs font-semibold text-gray-500 mb-1">
                                  Seat {seat.seat_number}
                                </div>
                                {seat.assigned_student_id ? (
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">
                                      {seat.assigned_student_name || seat.assigned_student_id}
                                    </div>
                                    {seat.assigned_student_name && (
                                      <div className="text-xs text-gray-500 mt-0.5">
                                        ID: {seat.assigned_student_id}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="text-xs text-gray-400 italic">Unassigned</div>
                                )}
                                {seat.row && seat.column && (
                                  <div className="text-xs text-gray-400 mt-1">
                                    Row {seat.row}, Col {seat.column}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            No seats assigned to this room
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No room information available for this seating plan</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SeatingPlansPage;

