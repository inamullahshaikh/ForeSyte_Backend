import React, { useState } from "react";
import { 
  LayoutDashboard, 
  FileUp, 
  History, 
  Award, 
  AlertCircle,
  Settings,
  ChevronDown
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const StudentSidebar = () => {
  const location = useLocation();
  const [expandedMenu, setExpandedMenu] = useState<string | null>(null);

  const menuItems = [
    { 
      name: "Dashboard", 
      icon: LayoutDashboard, 
      path: "/student-dashboard",
      submenu: null
    },
    { 
      name: "Upload Documents", 
      icon: FileUp, 
      path: "/student/upload",
      submenu: null
    },
    { 
      name: "Exam History", 
      icon: History, 
      path: "/student/exams",
      submenu: null
    },
    { 
      name: "Achievements", 
      icon: Award, 
      path: "/student/achievements",
      submenu: null
    },
    { 
      name: "Disciplinary Records", 
      icon: AlertCircle, 
      path: "/student/records",
      submenu: null
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white flex flex-col shadow-lg">
      {/* Logo Area */}
      <div className="px-6 py-8 border-b border-gray-700">
        <h1 className="text-xl font-bold text-purple-400">Foresyte Student</h1>
        <p className="text-xs text-gray-400 mt-1">Exam Portal</p>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);

          return (
            <div key={item.name}>
              <Link
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  active
                    ? "bg-purple-600 text-white shadow-lg"
                    : "text-gray-300 hover:bg-gray-700 hover:text-white"
                }`}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span className="font-medium text-sm">{item.name}</span>
              </Link>
            </div>
          );
        })}
      </nav>

      {/* Settings & Help */}
      <div className="px-4 py-4 border-t border-gray-700 space-y-2">
        <Link
          to="/student/settings"
          className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-all duration-200"
        >
          <Settings className="h-5 w-5 flex-shrink-0" />
          <span className="font-medium text-sm">Settings</span>
        </Link>

        <div className="px-4 py-3 bg-gray-700 rounded-lg">
          <p className="text-xs font-semibold text-gray-300 mb-1">Need Help?</p>
          <p className="text-xs text-gray-400">Contact support: support@foresyte.com</p>
        </div>
      </div>
    </div>
  );
};

export default StudentSidebar;