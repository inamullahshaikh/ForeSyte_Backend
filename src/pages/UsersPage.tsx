import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { Search, Filter, Plus, Edit, Trash2, UserPlus, MoreVertical, X } from "lucide-react";
import { apiService } from "../services/api";
import { useNavigate } from "react-router-dom";

interface User {
  id: string;
  name: string;
  email: string;
  user_type: string;
  status?: string;
  created_at?: string;
  last_login?: string;
}

const UsersPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRole, setFilterRole] = useState<string>("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  useEffect(() => {
    // Get current user info
    const fetchCurrentUser = async () => {
      try {
        const response = await apiService.getCurrentUser();
        if (response.data) {
          setCurrentUserId(response.data.id);
        }
      } catch (error) {
        console.error("Error fetching current user:", error);
      }
    };
    
    fetchCurrentUser();
    fetchUsers();
  }, [currentPage, filterRole]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await apiService.getUsers({
        role: filterRole !== "all" ? filterRole : undefined,
        page: currentPage,
        limit: 20,
      });

      if (response.data) {
        setUsers(response.data.users || []);
        if (response.data.total && response.data.limit) {
          setTotalPages(Math.ceil(response.data.total / response.data.limit));
        }
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (userId: string, userType: string) => {
    // Prevent deleting admin users
    if (userType === "admin") {
      alert("You cannot delete admin users");
      return;
    }
    
    if (window.confirm("Are you sure you want to delete this user?")) {
      try {
        const response = await apiService.deleteUser(userId);
        if (!response.error) {
          fetchUsers();
        } else {
          alert(response.error);
        }
      } catch (error) {
        console.error("Error deleting user:", error);
        alert("Failed to delete user");
      }
    }
  };

  const handleStatusChange = async (userId: string, status: string, userType: string) => {
    // Prevent changing status of admin users
    if (userType === "admin") {
      alert("You cannot change the status of admin users");
      return;
    }
    
    try {
      const response = await apiService.updateUser(userId, { status: status as any });
      if (!response.error) {
        fetchUsers();
      } else {
        alert(response.error);
      }
    } catch (error) {
      console.error("Error updating user status:", error);
      alert("Failed to update user status");
    }
  };

  // Check if user can be edited (admins cannot edit other admins)
  const canEditUser = (user: User): boolean => {
    return user.user_type !== "admin";
  };

  // Check if user can be deleted (admins cannot delete other admins)
  const canDeleteUser = (user: User): boolean => {
    return user.user_type !== "admin";
  };

  const handleSaveUser = async (formData: any) => {
    try {
      if (editingUser) {
        // Prevent editing admin users
        if (editingUser.user_type === "admin") {
          alert("You cannot edit admin users");
          return;
        }
        
        // Update existing user
        const updateData: any = {
          name: formData.name,
          email: formData.email,
          status: formData.status,
        };
        
        // Only update password if provided
        if (formData.password && formData.password.trim() !== "") {
          updateData.password = formData.password;
        }
        
        const response = await apiService.updateUser(editingUser.id, updateData);
        if (!response.error) {
          setEditingUser(null);
          fetchUsers();
        } else {
          alert(response.error);
        }
      } else {
        // Create new user
        const createData = {
          name: formData.name,
          email: formData.email,
          user_type: formData.user_type,
          password: formData.password,
          status: formData.status || "active",
          username: formData.user_type === "admin" ? formData.username || formData.email : undefined,
          roll_number: formData.user_type === "student" ? formData.roll_number : undefined,
          designation: formData.user_type === "investigator" ? formData.designation : undefined,
        };
        
        const response = await apiService.createUser(createData);
        if (!response.error) {
          setShowAddModal(false);
          fetchUsers();
        } else {
          alert(response.error);
        }
      }
    } catch (error) {
      console.error("Error saving user:", error);
      alert("Failed to save user");
    }
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "suspended":
        return "bg-red-100 text-red-800";
      case "inactive":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-blue-100 text-blue-800";
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-purple-100 text-purple-800";
      case "investigator":
        return "bg-blue-100 text-blue-800";
      case "invigilator":
        return "bg-yellow-100 text-yellow-800";
      case "student":
        return "bg-green-100 text-green-800";
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
                  User Management
                </h1>
                <p className="text-gray-600">
                  Manage system users, roles, and permissions
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <UserPlus className="h-5 w-5" />
                <span>Add User</span>
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
                  placeholder="Search users by name, email, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <select
                  value={filterRole}
                  onChange={(e) => {
                    setFilterRole(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="investigator">Investigator</option>
                  <option value="invigilator">Invigilator</option>
                  <option value="student">Student</option>
                </select>
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-4 px-6">User</th>
                    <th className="pb-4 px-6">Email</th>
                    <th className="pb-4 px-6">Role</th>
                    <th className="pb-4 px-6">Status</th>
                    <th className="pb-4 px-6">Last Login</th>
                    <th className="pb-4 px-6">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-gray-500">
                        Loading users...
                      </td>
                    </tr>
                  ) : filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-gray-500">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((user) => (
                      <tr key={user.id} className="border-b hover:bg-gray-50">
                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                              <span className="text-white font-medium text-sm">
                                {user.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{user.name}</div>
                              <div className="text-sm text-gray-500">{user.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-gray-900">{user.email}</td>
                        <td className="py-4 px-6">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(user.user_type)}`}>
                            {user.user_type}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <select
                            value={user.status || "active"}
                            onChange={(e) => handleStatusChange(user.id, e.target.value, user.user_type)}
                            disabled={user.user_type === "admin"}
                            className={`px-3 py-1 rounded-full text-xs font-medium border-0 ${getStatusColor(user.status)} ${
                              user.user_type === "admin" ? "opacity-50 cursor-not-allowed" : ""
                            }`}
                            title={user.user_type === "admin" ? "Cannot change admin status" : "Change user status"}
                          >
                            <option value="active">Active</option>
                            <option value="suspended">Suspended</option>
                            <option value="inactive">Inactive</option>
                          </select>
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleDateString()
                            : "Never"}
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => {
                                if (user.user_type === "admin") {
                                  alert("You cannot edit admin users");
                                  return;
                                }
                                setShowAddModal(false);
                                setEditingUser(user);
                              }}
                              disabled={!canEditUser(user)}
                              className={`p-2 rounded-lg transition-colors ${
                                canEditUser(user)
                                  ? "hover:bg-gray-100 cursor-pointer"
                                  : "opacity-50 cursor-not-allowed"
                              }`}
                              title={canEditUser(user) ? "Edit user" : "Cannot edit admin users"}
                            >
                              <Edit className={`h-4 w-4 ${canEditUser(user) ? "text-gray-600" : "text-gray-400"}`} />
                            </button>
                            {canDeleteUser(user) ? (
                              <button
                                onClick={() => handleDelete(user.id, user.user_type)}
                                className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                                title="Delete"
                              >
                                <Trash2 className="h-4 w-4 text-red-600" />
                              </button>
                            ) : (
                              <button
                                disabled
                                className="p-2 opacity-50 cursor-not-allowed rounded-lg"
                                title="Cannot delete admin users"
                              >
                                <Trash2 className="h-4 w-4 text-gray-400" />
                              </button>
                            )}
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

      {/* Add/Edit User Modal */}
      {(showAddModal || editingUser) && (
        <UserModal
          user={editingUser}
          onClose={() => {
            setShowAddModal(false);
            setEditingUser(null);
          }}
          onSave={handleSaveUser}
        />
      )}
    </div>
  );
};

// User Modal Component
interface UserModalProps {
  user: User | null;
  onClose: () => void;
  onSave: (formData: any) => void;
}

const UserModal: React.FC<UserModalProps> = ({ user, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    user_type: user?.user_type || "student",
    password: "",
    status: user?.status || "active",
    username: "",
    roll_number: "",
    designation: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Update form data when user prop changes (for editing)
  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        user_type: user.user_type || "student",
        password: "",
        status: user.status || "active",
        username: "",
        roll_number: "",
        designation: "",
      });
    } else {
      // Reset form for new user
      setFormData({
        name: "",
        email: "",
        user_type: "student",
        password: "",
        status: "active",
        username: "",
        roll_number: "",
        designation: "",
      });
    }
  }, [user]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }
    if (!user && !formData.password.trim()) {
      newErrors.password = "Password is required";
    }
    if (formData.user_type === "admin" && !user && !formData.username.trim()) {
      newErrors.username = "Username is required for admin";
    }
    if (formData.user_type === "student" && !user && !formData.roll_number.trim()) {
      newErrors.roll_number = "Roll number is required for student";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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
            {user ? "Edit User" : "Add New User"}
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
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.name ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Enter full name"
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.email ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Enter email address"
            />
            {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role <span className="text-red-500">*</span>
              {user && (
                <span className="text-xs text-gray-500 ml-2 font-normal">(Cannot be changed)</span>
              )}
            </label>
            <select
              name="user_type"
              value={formData.user_type}
              onChange={handleChange}
              disabled={!!user} // Can't change role when editing
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="admin">Admin</option>
              <option value="investigator">Investigator</option>
              <option value="invigilator">Invigilator</option>
              <option value="student">Student</option>
            </select>
            {user && (
              <p className="text-xs text-gray-500 mt-1">
                Role cannot be changed after user creation for data integrity.
              </p>
            )}
          </div>

          {formData.user_type === "admin" && !user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                  errors.username ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Enter username"
              />
              {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username}</p>}
            </div>
          )}

          {formData.user_type === "student" && !user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Roll Number <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="roll_number"
                value={formData.roll_number}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                  errors.roll_number ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Enter roll number"
              />
              {errors.roll_number && <p className="text-red-500 text-sm mt-1">{errors.roll_number}</p>}
            </div>
          )}

          {formData.user_type === "investigator" && !user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Designation
              </label>
              <input
                type="text"
                name="designation"
                value={formData.designation}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter designation (optional)"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password {!user && <span className="text-red-500">*</span>}
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.password ? "border-red-500" : "border-gray-300"
              }`}
              placeholder={user ? "Leave blank to keep current password" : "Enter password"}
            />
            {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            {user && <p className="text-gray-500 text-sm mt-1">Leave blank to keep current password</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              {user ? "Update User" : "Create User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UsersPage;

