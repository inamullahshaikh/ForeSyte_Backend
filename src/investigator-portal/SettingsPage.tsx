import { useState, useEffect } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import { User, Lock, Bell, Save } from "lucide-react";
import { apiService } from "../services/api";

interface InvestigatorProfile {
  investigator_id: string;
  name: string;
  email: string;
  designation: string;
}

const SettingsPage = () => {
  const [profile, setProfile] = useState<InvestigatorProfile>({
    investigator_id: "",
    name: "",
    email: "",
    designation: "",
  });

  const [passwords, setPasswords] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    violationAlerts: true,
    reportReady: true,
    weeklyDigest: false,
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    // Load investigator profile from session/API
    const userInfo = JSON.parse(sessionStorage.getItem("userInfo") || "{}");
    setProfile({
      investigator_id: userInfo.id || "INV-001",
      name: userInfo.name || "Investigator Name",
      email: userInfo.email || "investigator@university.edu",
      designation: userInfo.designation || "Senior Investigator",
    });
  }, []);

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // API call to update profile
      console.log("Updating profile:", profile);
      
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setMessage({ type: "success", text: "Profile updated successfully!" });
      
      // Update session storage
      const userInfo = JSON.parse(sessionStorage.getItem("userInfo") || "{}");
      sessionStorage.setItem(
        "userInfo",
        JSON.stringify({ ...userInfo, ...profile })
      );
    } catch (error) {
      setMessage({ type: "error", text: "Failed to update profile." });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    // Validation
    if (!passwords.currentPassword) {
      setMessage({ type: "error", text: "Please enter your current password!" });
      setLoading(false);
      return;
    }

    if (passwords.newPassword !== passwords.confirmPassword) {
      setMessage({ type: "error", text: "New passwords do not match!" });
      setLoading(false);
      return;
    }

    if (passwords.newPassword.length < 8) {
      setMessage({
        type: "error",
        text: "Password must be at least 8 characters long!",
      });
      setLoading(false);
      return;
    }

    if (passwords.currentPassword === passwords.newPassword) {
      setMessage({
        type: "error",
        text: "New password must be different from current password!",
      });
      setLoading(false);
      return;
    }

    try {
      // API call to change password
      const response = await apiService.changePassword({
        current_password: passwords.currentPassword,
        new_password: passwords.newPassword,
      });

      if (response.error) {
        setMessage({ type: "error", text: response.error || "Failed to change password." });
      } else {
        setMessage({ type: "success", text: "Password changed successfully!" });
        setPasswords({
          currentPassword: "",
          newPassword: "",
          confirmPassword: "",
        });
      }
    } catch (error: any) {
      console.error("Password change error:", error);
      setMessage({ 
        type: "error", 
        text: error.message || "Failed to change password. Please try again." 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationUpdate = async () => {
    setLoading(true);
    setMessage(null);

    try {
      // API call to update notification preferences
      console.log("Updating notifications:", notifications);
      
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setMessage({
        type: "success",
        text: "Notification preferences updated!",
      });
    } catch (error) {
      setMessage({ type: "error", text: "Failed to update preferences." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <InvestigatorSidebar />
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <InvestigatorHeader />
        <div className="flex-1 p-6 overflow-y-auto max-w-4xl">
          {/* Message Alert */}
          {message && (
            <div
              className={`mb-6 p-4 rounded-lg ${
                message.type === "success"
                  ? "bg-green-100 text-green-800 border border-green-200"
                  : "bg-red-100 text-red-800 border border-red-200"
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Profile Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <User className="w-6 h-6 text-indigo-900" />
                <h2 className="text-xl font-bold text-gray-900">
                  Profile Information
                </h2>
              </div>
            </div>

            <form onSubmit={handleProfileUpdate} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) =>
                      setProfile({ ...profile, name: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) =>
                      setProfile({ ...profile, email: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Investigator ID
                  </label>
                  <input
                    type="text"
                    value={profile.investigator_id}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Designation
                  </label>
                  <input
                    type="text"
                    value={profile.designation}
                    onChange={(e) =>
                      setProfile({ ...profile, designation: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-900 text-white px-6 py-2 rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  Save Profile
                </button>
              </div>
            </form>
          </div>

          {/* Password Change */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Lock className="w-6 h-6 text-indigo-900" />
                <h2 className="text-xl font-bold text-gray-900">
                  Change Password
                </h2>
              </div>
            </div>

            <form onSubmit={handlePasswordChange} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwords.currentPassword}
                  onChange={(e) =>
                    setPasswords({ ...passwords, currentPassword: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwords.newPassword}
                    onChange={(e) =>
                      setPasswords({ ...passwords, newPassword: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwords.confirmPassword}
                    onChange={(e) =>
                      setPasswords({
                        ...passwords,
                        confirmPassword: e.target.value,
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-900 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-900 text-white px-6 py-2 rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  <Lock className="w-4 h-4" />
                  Change Password
                </button>
              </div>
            </form>
          </div>

          {/* Notification Preferences */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Bell className="w-6 h-6 text-indigo-900" />
                <h2 className="text-xl font-bold text-gray-900">
                  Notification Preferences
                </h2>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-gray-900">Email Notifications</p>
                  <p className="text-sm text-gray-500">
                    Receive notifications via email
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.emailNotifications}
                  onChange={(e) =>
                    setNotifications({
                      ...notifications,
                      emailNotifications: e.target.checked,
                    })
                  }
                  className="w-5 h-5 text-indigo-900 border-gray-300 rounded focus:ring-indigo-900"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-gray-900">Violation Alerts</p>
                  <p className="text-sm text-gray-500">
                    Get notified when new violations are flagged
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.violationAlerts}
                  onChange={(e) =>
                    setNotifications({
                      ...notifications,
                      violationAlerts: e.target.checked,
                    })
                  }
                  className="w-5 h-5 text-indigo-900 border-gray-300 rounded focus:ring-indigo-900"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-gray-900">Report Ready</p>
                  <p className="text-sm text-gray-500">
                    Notify when reports are generated
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.reportReady}
                  onChange={(e) =>
                    setNotifications({
                      ...notifications,
                      reportReady: e.target.checked,
                    })
                  }
                  className="w-5 h-5 text-indigo-900 border-gray-300 rounded focus:ring-indigo-900"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-gray-900">Weekly Digest</p>
                  <p className="text-sm text-gray-500">
                    Receive weekly summary of activities
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.weeklyDigest}
                  onChange={(e) =>
                    setNotifications({
                      ...notifications,
                      weeklyDigest: e.target.checked,
                    })
                  }
                  className="w-5 h-5 text-indigo-900 border-gray-300 rounded focus:ring-indigo-900"
                />
              </label>

              <div className="flex justify-end pt-4 border-t border-gray-200">
                <button
                  onClick={handleNotificationUpdate}
                  disabled={loading}
                  className="bg-indigo-900 text-white px-6 py-2 rounded-lg hover:bg-indigo-800 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  Save Preferences
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

