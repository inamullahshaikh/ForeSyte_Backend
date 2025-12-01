import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { Search, Filter, Plus, Edit, Trash2, Calendar, Clock, Users, X } from "lucide-react";
import { apiService } from "../services/api";
import { useNavigate } from "react-router-dom";

interface Exam {
  id: string;
  name: string;
  course_code: string;
  instructor_id: string;
  scheduled_date: string;
  duration_minutes: number;
  status?: string;
  seating_plan_id?: string;
  description?: string;
}

const ExamsPage: React.FC = () => {
  const navigate = useNavigate();
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchExams();
  }, [currentPage, filterStatus]);

  const fetchExams = async () => {
    setLoading(true);
    try {
      const response = await apiService.getExams({
        status: filterStatus !== "all" ? filterStatus : undefined,
        page: currentPage,
        limit: 20,
      });

      if (response.data) {
        setExams(response.data.exams || []);
        if (response.data.total && response.data.limit) {
          setTotalPages(Math.ceil(response.data.total / response.data.limit));
        }
      }
    } catch (error) {
      console.error("Error fetching exams:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (examId: string) => {
    if (window.confirm("Are you sure you want to delete this exam?")) {
      try {
        const response = await apiService.deleteExam(examId);
        if (!response.error) {
          fetchExams();
        } else {
          alert(response.error);
        }
      } catch (error) {
        console.error("Error deleting exam:", error);
        alert("Failed to delete exam");
      }
    }
  };

  const filteredExams = exams.filter((exam) => {
    const matchesSearch =
      exam.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      exam.course_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      exam.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "completed":
        return "bg-blue-100 text-blue-800";
      case "scheduled":
        return "bg-yellow-100 text-yellow-800";
      case "cancelled":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const handleSaveExam = async (formData: any) => {
    try {
      if (editingExam) {
        // Update existing exam
        const updateData: any = {
          name: formData.name,
          course_code: formData.course_code,
        };

        if (formData.scheduled_date) {
          updateData.scheduled_date = new Date(formData.scheduled_date).toISOString();
        }
        if (formData.duration_minutes) {
          updateData.duration_minutes = parseInt(formData.duration_minutes);
        }

        const response = await apiService.updateExam(editingExam.id, updateData);
        if (!response.error) {
          setEditingExam(null);
          fetchExams();
        } else {
          alert(response.error || "Failed to update exam");
        }
      } else {
        // Create new exam
        const examData: any = {
          name: formData.name,
          course_code: formData.course_code,
          scheduled_date: new Date(formData.scheduled_date).toISOString(),
          duration_minutes: parseInt(formData.duration_minutes),
        };

        // Only include instructor_id if provided (backend may not require it)
        if (formData.instructor_id) {
          examData.instructor_id = formData.instructor_id;
        }

        const response = await apiService.createExam(examData);
        if (!response.error) {
          setShowAddModal(false);
          fetchExams();
        } else {
          alert(response.error || "Failed to create exam");
        }
      }
    } catch (error) {
      console.error("Error saving exam:", error);
      alert("Failed to save exam");
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
                  Exam Management
                </h1>
                <p className="text-gray-600">
                  Create, manage, and monitor examination schedules
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
                <span>Create Exam</span>
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
                  placeholder="Search exams by name, course code, or ID..."
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
                  <option value="scheduled">Scheduled</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>
          </div>

          {/* Exams Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                Loading exams...
              </div>
            ) : filteredExams.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-gray-500">
                No exams found
              </div>
            ) : (
              filteredExams.map((exam) => (
                <div
                  key={exam.id}
                  className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {exam.name}
                      </h3>
                      <p className="text-sm text-gray-600">{exam.course_code}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(exam.status)}`}>
                      {exam.status || "scheduled"}
                    </span>
                  </div>

                  <div className="space-y-3 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      <span>{formatDate(exam.scheduled_date)}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="h-4 w-4 mr-2 text-gray-400" />
                      <span>Duration: {formatDuration(exam.duration_minutes)}</span>
                    </div>
                    {exam.description && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {exam.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <span className="text-xs text-gray-500">ID: {exam.id}</span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setEditingExam(exam)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Edit"
                      >
                        <Edit className="h-4 w-4 text-gray-600" />
                      </button>
                      <button
                        onClick={() => handleDelete(exam.id)}
                        className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 px-6 py-4 bg-white rounded-xl shadow-sm border border-gray-200">
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

      {/* Exam Modal */}
      {(showAddModal || editingExam) && (
        <ExamModal
          exam={editingExam}
          onClose={() => {
            setShowAddModal(false);
            setEditingExam(null);
          }}
          onSave={handleSaveExam}
        />
      )}
    </div>
  );
};

interface ExamModalProps {
  exam: Exam | null;
  onClose: () => void;
  onSave: (formData: any) => void;
}

const ExamModal: React.FC<ExamModalProps> = ({ exam, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: exam?.name || "",
    course_code: exam?.course_code || "",
    instructor_id: exam?.instructor_id || "",
    scheduled_date: exam?.scheduled_date 
      ? new Date(exam.scheduled_date).toISOString().slice(0, 16)
      : "",
    duration_minutes: exam?.duration_minutes?.toString() || "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [users, setUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  useEffect(() => {
    // Fetch invigilators only
    const fetchInvigilators = async () => {
      setLoadingUsers(true);
      try {
        const response = await apiService.getUsers({ role: 'invigilator', limit: 100 });
        if (response.data) {
          const data = response.data as any;
          if (data.users) {
            setUsers(data.users);
          }
        }
      } catch (error) {
        console.error("Error fetching invigilators:", error);
      } finally {
        setLoadingUsers(false);
      }
    };

    fetchInvigilators();

    // Update form data when exam prop changes
    if (exam) {
      setFormData({
        name: exam.name || "",
        course_code: exam.course_code || "",
        instructor_id: exam.instructor_id || "",
        scheduled_date: exam.scheduled_date 
          ? new Date(exam.scheduled_date).toISOString().slice(0, 16)
          : "",
        duration_minutes: exam.duration_minutes?.toString() || "",
      });
    }
  }, [exam]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Exam name is required";
    }
    if (!formData.course_code.trim()) {
      newErrors.course_code = "Course code is required";
    }
    if (!formData.scheduled_date) {
      newErrors.scheduled_date = "Scheduled date is required";
    }
    if (!formData.duration_minutes) {
      newErrors.duration_minutes = "Duration is required";
    } else if (parseInt(formData.duration_minutes) <= 0) {
      newErrors.duration_minutes = "Duration must be greater than 0";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            {exam ? "Edit Exam" : "Create New Exam"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Exam Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.name ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Enter exam name"
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Course Code <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="course_code"
              value={formData.course_code}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.course_code ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Enter course code"
            />
            {errors.course_code && <p className="text-red-500 text-sm mt-1">{errors.course_code}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Invigilator (Optional)
            </label>
            {loadingUsers ? (
              <div className="text-sm text-gray-500 py-2">Loading users...</div>
            ) : (
              <>
                <input
                  type="text"
                  name="instructor_id"
                  value={formData.instructor_id}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                    errors.instructor_id ? "border-red-500" : "border-gray-300"
                  }`}
                  placeholder="Enter invigilator ID (optional)"
                  disabled={!!exam}
                />
                {!exam && users.length > 0 && (
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        setFormData((prev) => ({ ...prev, instructor_id: e.target.value }));
                        if (errors.instructor_id) {
                          setErrors((prev) => ({ ...prev, instructor_id: "" }));
                        }
                      }
                    }}
                    className="w-full mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">-- Or select from list --</option>
                    {users.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.name} - {user.email}
                        </option>
                      ))}
                  </select>
                )}
              </>
            )}
            {errors.instructor_id && <p className="text-red-500 text-sm mt-1">{errors.instructor_id}</p>}
            {exam && <p className="text-xs text-gray-500 mt-1">Invigilator cannot be changed after creation.</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scheduled Date & Time <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              name="scheduled_date"
              value={formData.scheduled_date}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.scheduled_date ? "border-red-500" : "border-gray-300"
              }`}
            />
            {errors.scheduled_date && <p className="text-red-500 text-sm mt-1">{errors.scheduled_date}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Duration (minutes) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="duration_minutes"
              value={formData.duration_minutes}
              onChange={handleChange}
              min="1"
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.duration_minutes ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Enter duration in minutes"
            />
            {errors.duration_minutes && <p className="text-red-500 text-sm mt-1">{errors.duration_minutes}</p>}
          </div>


          <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              {exam ? "Update Exam" : "Create Exam"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExamsPage;

