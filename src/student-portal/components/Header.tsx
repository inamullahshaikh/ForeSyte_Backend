import React from "react";
import { Search, Bell, User, LogOut } from "lucide-react";
import Logo from "../../components/Logo";

const StudentHeader = () => {
  const handleLogout = () => {
    sessionStorage.clear();
    window.location.href = "/login";
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 flex items-center justify-between flex-shrink-0 h-16">
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
            placeholder="Search your documents..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-50 text-gray-700 placeholder-gray-400"
          />
        </div>
      </div>

      {/* Right side - Notifications and User */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <div className="relative">
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
            <Bell className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        {/* User Profile */}
        <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
          <div className="text-right">
            <div className="font-semibold text-gray-900 text-sm">Student User</div>
            <div className="text-gray-500 text-xs">Student Account</div>
          </div>
          <div className="relative group">
            <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-purple-700 transition-colors">
              <User className="h-5 w-5 text-white" />
            </div>
            
            {/* Dropdown Menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-sm font-semibold text-gray-900">Student User</p>
                <p className="text-xs text-gray-500">student@example.com</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center space-x-2 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentHeader;