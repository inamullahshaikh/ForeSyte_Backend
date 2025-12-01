import { Bell, User, LogOut, Search, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Logo from "../../components/Logo";
import { apiService } from "../../services/api";

interface Notification {
  id: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface UserInfo {
  id: string;
  name: string;
  email: string;
  user_type: string;
  designation?: string;
}

const InvestigatorHeader = () => {
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [userInfo, setUserInfo] = useState<UserInfo>({
    id: "",
    name: "Investigator",
    email: "",
    user_type: "investigator",
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserInfo();
    // Mock notifications - in production, fetch from API
    setNotifications([
      {
        id: "1",
        message: "New violation flagged in Room 101",
        timestamp: "5 mins ago",
        read: false,
      },
      {
        id: "2",
        message: "Report generated for Exam CS101",
        timestamp: "1 hour ago",
        read: false,
      },
    ]);
  }, []);

  const fetchUserInfo = async () => {
    try {
      // Try to get from sessionStorage first (faster)
      const storedUserInfo = sessionStorage.getItem("userInfo");
      if (storedUserInfo) {
        const parsed = JSON.parse(storedUserInfo);
        if (parsed.name && parsed.email) {
          setUserInfo(parsed);
          setLoading(false);
          return;
        }
      }

      // Fetch from API
      const response = await apiService.getCurrentUser();
      if (response.data) {
        const userData = response.data as any;
        const user: UserInfo = {
          id: userData.id || "",
          name: userData.name || "Investigator",
          email: userData.email || "",
          user_type: userData.user_type || "investigator",
          designation: userData.designation,
        };
        setUserInfo(user);
        
        // Store in sessionStorage for future use
        sessionStorage.setItem("userInfo", JSON.stringify(user));
      }
    } catch (error) {
      console.error("Error fetching user info:", error);
      // Fallback to sessionStorage values if available
      const userId = sessionStorage.getItem("user_id");
      const userType = sessionStorage.getItem("user_type");
      if (userId && userType) {
        setUserInfo({
          id: userId,
          name: "Investigator",
          email: "",
          user_type: userType,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.clear();
    navigate("/login");
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <header className="bg-white border-b border-gray-200 px-6 flex items-center justify-between flex-shrink-0">
      {/* Left side - Logo */}
      <div className="flex items-center">
        <Logo />
        <span className="ml-3 text-2xl font-bold text-purple-600">Foresyte</span>
      </div>

      {/* Center - Search Bar */}
      <div className="flex-1 max-w-2xl mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search violations, students, reports..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-50 text-gray-700 placeholder-gray-400"
          />
        </div>
      </div>

      {/* Right side - Notifications and User */}
      <div className="flex items-center space-x-4">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors relative"
            >
              <Bell className="h-6 w-6 text-gray-600" />
              {unreadCount > 0 && (
                <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-y-auto">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                  <button
                    onClick={() => setShowNotifications(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="divide-y divide-gray-200">
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-4 hover:bg-gray-50 cursor-pointer ${
                          !notification.read ? "bg-blue-50" : ""
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className={`text-sm ${
                              !notification.read ? 'font-medium text-gray-900' : 'text-gray-700'
                            }`}>
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">{notification.timestamp}</p>
                          </div>
                          {!notification.read && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full ml-2"></div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-gray-500 text-sm">
                      No notifications
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Profile dropdown */}
          <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
            <div className="text-right">
              <div className="font-semibold text-gray-900 text-sm">
                {loading ? "Loading..." : userInfo.name || "Investigator"}
              </div>
              <div className="text-gray-500 text-xs">
                {userInfo.designation || "Investigator"}
              </div>
            </div>
            <div className="relative">
              <button
                onClick={() => setShowProfile(!showProfile)}
                className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-purple-700 transition-colors"
              >
                {userInfo.name ? (
                  <span className="text-white font-medium text-sm">
                    {userInfo.name.charAt(0).toUpperCase()}
                  </span>
                ) : (
                  <User className="h-5 w-5 text-white" />
                )}
              </button>

              {showProfile && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <button
                    onClick={() => {
                      setShowProfile(false);
                      navigate("/investigator/settings");
                    }}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <User className="w-4 h-4" />
                    <span>Profile Settings</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 text-red-600 flex items-center gap-2 border-t border-gray-200"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
      </div>
    </header>
  );
};

export default InvestigatorHeader;

