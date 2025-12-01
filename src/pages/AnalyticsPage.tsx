import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { TrendingUp, TrendingDown, BarChart3, PieChart, Calendar, Filter } from "lucide-react";

const AnalyticsPage: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<"today" | "week" | "month" | "year">("month");

  // Mock data for charts
  const incidentTrendData = [
    { period: "Jan", incidents: 12, resolved: 10 },
    { period: "Feb", incidents: 15, resolved: 14 },
    { period: "Mar", incidents: 8, resolved: 7 },
    { period: "Apr", incidents: 20, resolved: 18 },
    { period: "May", incidents: 14, resolved: 12 },
    { period: "Jun", incidents: 18, resolved: 16 }
  ];

  const incidentTypeData = [
    { type: "Suspicious Movement", count: 45, percentage: 35 },
    { type: "Device Detected", count: 32, percentage: 25 },
    { type: "Multiple Faces", count: 28, percentage: 22 },
    { type: "Looking Away", count: 15, percentage: 12 },
    { type: "Other", count: 8, percentage: 6 }
  ];

  const examPerformanceData = [
    { exam: "Calculus I", students: 120, incidents: 5, rate: 4.2 },
    { exam: "Physics", students: 95, incidents: 3, rate: 3.2 },
    { exam: "Programming", students: 150, incidents: 8, rate: 5.3 },
    { exam: "Chemistry", students: 110, incidents: 4, rate: 3.6 }
  ];

  const maxIncidents = Math.max(...incidentTrendData.map(d => Math.max(d.incidents, d.resolved)));

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
                  Analytics
                </h1>
                <p className="text-gray-600">
                  Comprehensive insights and data analysis
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value as "today" | "week" | "month" | "year")}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="year">This Year</option>
                </select>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-600 text-sm">Total Incidents</p>
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">128</p>
              <p className="text-sm text-green-600 mt-1">+12% from last period</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-600 text-sm">Resolution Rate</p>
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">87%</p>
              <p className="text-sm text-green-600 mt-1">+5% from last period</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-600 text-sm">Avg. Response Time</p>
                <TrendingDown className="h-5 w-5 text-red-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">4.2m</p>
              <p className="text-sm text-red-600 mt-1">+0.5m from last period</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-600 text-sm">False Positives</p>
                <TrendingDown className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">8%</p>
              <p className="text-sm text-green-600 mt-1">-2% from last period</p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Incident Trend Chart */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Incident Trends</h2>
                <BarChart3 className="h-5 w-5 text-gray-400" />
              </div>
              
              <div className="h-64 flex items-end justify-between space-x-2">
                {incidentTrendData.map((data, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center space-y-2">
                    <div className="w-full flex flex-col items-center space-y-1" style={{ height: "200px" }}>
                      <div
                        className="w-full bg-gradient-to-t from-red-600 to-red-400 rounded-t transition-all duration-300 hover:opacity-80"
                        style={{ height: `${(data.incidents / maxIncidents) * 100}%` }}
                        title={`${data.incidents} incidents`}
                      />
                      <div
                        className="w-full bg-gradient-to-t from-green-600 to-green-400 rounded-t transition-all duration-300 hover:opacity-80"
                        style={{ height: `${(data.resolved / maxIncidents) * 100}%` }}
                        title={`${data.resolved} resolved`}
                      />
                    </div>
                    <span className="text-xs text-gray-500">{data.period}</span>
                  </div>
                ))}
              </div>
              
              <div className="flex items-center justify-center space-x-6 mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-600 rounded"></div>
                  <span className="text-sm text-gray-600">Incidents</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-600 rounded"></div>
                  <span className="text-sm text-gray-600">Resolved</span>
                </div>
              </div>
            </div>

            {/* Incident Type Distribution */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Incident Types</h2>
                <PieChart className="h-5 w-5 text-gray-400" />
              </div>
              
              <div className="space-y-4">
                {incidentTypeData.map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900">{item.type}</span>
                      <span className="text-sm text-gray-600">{item.count} ({item.percentage}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${item.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Exam Performance Table */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Exam Performance</h2>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-3">Exam</th>
                    <th className="pb-3">Students</th>
                    <th className="pb-3">Incidents</th>
                    <th className="pb-3">Incident Rate</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {examPerformanceData.map((exam, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-4 font-medium text-gray-900">{exam.exam}</td>
                      <td className="py-4 text-gray-600">{exam.students}</td>
                      <td className="py-4 text-gray-600">{exam.incidents}</td>
                      <td className="py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          exam.rate < 4 ? "bg-green-100 text-green-800" :
                          exam.rate < 6 ? "bg-yellow-100 text-yellow-800" :
                          "bg-red-100 text-red-800"
                        }`}>
                          {exam.rate}%
                        </span>
                      </td>
                      <td className="py-4">
                        <span className="text-sm text-gray-600">
                          {exam.rate < 4 ? "Good" : exam.rate < 6 ? "Moderate" : "Needs Attention"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;

