import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  BarChart3, 
  Video, 
  FileText, 
  AlertTriangle, 
  TrendingUp, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Users,
  GraduationCap,
  LayoutGrid
} from "lucide-react";
import Logo from "./Logo";

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3, path: "/dashboard" },
    { id: "monitoring", label: "Live Monitoring", icon: Video, path: "/monitoring" },
    { id: "exams", label: "Exams", icon: GraduationCap, path: "/exams" },
    { id: "seating-plans", label: "Seating Plans", icon: LayoutGrid, path: "/seating-plans" },
    { id: "upload", label: "Upload Seating Plan", icon: FileText, path: "/upload-seating-plan" },
    { id: "incidents", label: "Incidents", icon: AlertTriangle, path: "/incidents" },
    { id: "reports", label: "Reports", icon: FileText, path: "/reports" },
    { id: "analytics", label: "Analytics", icon: TrendingUp, path: "/analytics" },
    { id: "users", label: "Users", icon: Users, path: "/users" },
    { id: "settings", label: "Settings", icon: Settings, path: "/settings" },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div 
      className={`bg-gray-900 h-screen flex flex-col overflow-x-hidden transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo Section */}
      {/* <div className="border-b border-gray-800 flex-shrink-0 flex items-center justify-between">
        <div className="flex items-center overflow-hidden">
          <Logo />
          {!isCollapsed && (
            <span className="text-2xl font-bold text-white whitespace-nowrap">Foresyte</span>
          )}
        </div>
      </div> */}

      {/* Toggle Button */}
      <div className="px-4 py-3 flex-shrink-0">
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation Menu */}
      <div className="flex-1 px-4 py-2 bg-gray-900 overflow-x-hidden">
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleNavigation(item.path)}
                className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} px-4 py-3 rounded-lg text-left transition-all duration-200 relative group ${
                  isActive
                    ? "bg-lime-300 text-gray-900 font-medium"
                    : "text-gray-300 hover:text-white hover:bg-gray-800"
                }`}
                title={isCollapsed ? item.label : ''}
              >
                <div className="flex items-center">
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && (
                    <span className="ml-3 whitespace-nowrap">{item.label}</span>
                  )}
                </div>
                {/* {item.badge && !isCollapsed && (
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    isActive ? 'bg-gray-900 text-lime-500' : 'bg-lime-500 text-gray-900'
                  }`}>
                    {item.badge}
                  </span>
                )} */}
                {/* {item.badge && isCollapsed && (
                  <span className="absolute -top-1 -right-1 bg-lime-500 text-gray-900 text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
                    {item.badge}
                  </span>
                )} */}
                
                {/* Tooltip for collapsed state */}
                {isCollapsed && (
                  <div className="absolute left-full ml-2 px-3 py-2 bg-gray-800 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                    {item.label}
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-800 bg-gray-900 flex-shrink-0">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : ''}`}>
          <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-medium text-sm">DU</span>
          </div>
          {!isCollapsed && (
            <div className="ml-3 overflow-hidden">
              <div className="text-white font-medium text-sm whitespace-nowrap">Demo User</div>
              <div className="text-gray-400 text-xs whitespace-nowrap">Administrator</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;