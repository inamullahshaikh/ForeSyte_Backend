import React from "react";
import Logo from "../components/Logo";
import { Bell, User } from "lucide-react";

const StudentHeader: React.FC = () => {
  return (
    <div className="bg-white border-b border-gray-200 px-6 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center">
        <Logo />
        <span className="ml-3 text-2xl font-bold text-purple-600">Foresyte</span>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative">
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
            <Bell className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
          <div className="text-right">
            <div className="font-semibold text-gray-900 text-sm">Student</div>
            <div className="text-gray-500 text-xs">Portal</div>
          </div>
          <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-purple-700 transition-colors">
            <User className="h-5 w-5 text-white" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentHeader;


