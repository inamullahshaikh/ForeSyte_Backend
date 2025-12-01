import React from "react";
import { 
  AlertCircle, 
  CheckCircle,
  Award,
  AlertTriangle,
  Eye,
  MessageSquare
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import StudentHeader from "./StudentHeader";

interface DashboardStat {
  title: string;
  value: string;
  change: string;
  changeType: "positive" | "negative";
  icon: LucideIcon;
  iconColor: string;
}

const StudentDashboardPage: React.FC = () => {
  const stats: DashboardStat[] = [
    {
      title: "Disciplinary Cases",
      value: "0",
      change: "No recent issues",
      changeType: "positive",
      icon: AlertCircle,
      iconColor: "text-blue-600"
    },
    {
      title: "Cheating Activity Flags",
      value: "0",
      change: "Clean record",
      changeType: "positive",
      icon: Award,
      iconColor: "text-purple-600"
    }
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
      <StudentHeader />
      
      <div className="flex-1 p-6 overflow-y-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Welcome back, Student 👋
                </h1>
                <p className="text-gray-600">
                  Review your status and recent activity.
                </p>
              </div>
              <div className="flex items-center bg-green-50 px-4 py-2 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-green-700 font-medium">Good Standing</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <div className="lg:col-span-2 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl p-6 shadow-sm text-white">
              <h3 className="text-lg font-semibold mb-6">Your Profile</h3>
              
              <div className="space-y-4">
                <div>
                  <p className="text-purple-100 text-sm">Student ID</p>
                  <p className="text-white font-semibold">STU-2024-001</p>
                </div>
                
                <div>
                  <p className="text-purple-100 text-sm">Enrollment Status</p>
                  <p className="text-white font-semibold">Active</p>
                </div>
                
                <div>
                  <p className="text-purple-100 text-sm">Academic Standing</p>
                  <p className="text-white font-semibold">Excellent</p>
                </div>

                <div className="pt-4 border-t border-purple-400">
                  <p className="text-purple-100 text-xs">Last Login</p>
                  <p className="text-white text-sm">Today at 10:30 AM</p>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-6">
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={index} className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md transition-shadow flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <div className="p-3 rounded-lg bg-gray-50">
                        <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        stat.changeType === "positive" ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"
                      }`}>{stat.change}</span>
                    </div>
                    <div className="mt-4">
                      <p className="text-gray-600 text-sm">{stat.title}</p>
                      <h3 className="text-3xl font-bold text-gray-900 leading-tight">{stat.value}</h3>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-8 bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Recent Cheating Activities</h2>
              <AlertTriangle className="h-6 w-6 text-red-500" />
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Suspicious head movement detected</p>
                    <p className="text-sm text-gray-500">Today • 10:30 AM • Exam: Calculus I</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">Flagged</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Eye className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Multiple faces detected</p>
                    <p className="text-sm text-gray-500">Yesterday • 4:12 PM • Exam: Programming Basics</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">Warning</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="h-6 w-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Keyboard activity spike</p>
                    <p className="text-sm text-gray-500">2 days ago • 6:05 PM • Exam: Data Structures</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">Notice</span>
              </div>
            </div>
          </div>
      </div>
    </div>
  );
};

export default StudentDashboardPage;