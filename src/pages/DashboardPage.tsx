import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Eye, 
  AlertTriangle, 
  Users, 
  Clock, 
  CheckCircle,
  TrendingUp,
  TrendingDown,
  FileText,
  Video,
  Shield,
  Activity,
  BarChart3
} from "lucide-react";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import { apiService } from "../services/api";

const DashboardPage = () => {
  const navigate = useNavigate();
  const [selectedPeriod, setSelectedPeriod] = useState<"today" | "week" | "month">("today");
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    active_exams: 0,
    incidents_detected: 0,
    students_monitored: 0,
    avg_exam_duration: 0,
    incidents_trend: "+0%",
    students_trend: "+0%",
    exams_trend: "+0%"
  });
  const [activityData, setActivityData] = useState<Array<{time: string; incidents: number; exams: number}>>([]);
  const [recentIncidents, setRecentIncidents] = useState<Array<{
    id: string;
    student_name: string;
    type: string;
    severity: string;
    timestamp: string;
  }>>([]);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsResponse, activityResponse, incidentsResponse] = await Promise.all([
        apiService.getDashboardStats(selectedPeriod),
        apiService.getActivityData(selectedPeriod),
        apiService.getRecentIncidents(5)
      ]);

      if (statsResponse.data) {
        setStats(statsResponse.data);
      }

      if (activityResponse.data?.data) {
        setActivityData(activityResponse.data.data);
      }

      if (incidentsResponse.data) {
        setRecentIncidents(Array.isArray(incidentsResponse.data) ? incidentsResponse.data : []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const statsCards = [
    {
      title: "Active Exams",
      value: stats.active_exams.toString(),
      change: stats.exams_trend,
      changeType: stats.exams_trend.startsWith("+") ? "positive" : "negative",
      icon: Eye,
      iconColor: "text-blue-600",
      bgColor: "bg-blue-50"
    },
    {
      title: "Incidents Detected",
      value: stats.incidents_detected.toString(),
      change: stats.incidents_trend,
      changeType: stats.incidents_trend.startsWith("+") ? "negative" : "positive",
      icon: AlertTriangle,
      iconColor: "text-red-600",
      bgColor: "bg-red-50"
    },
    {
      title: "Students Monitored",
      value: stats.students_monitored.toLocaleString(),
      change: stats.students_trend,
      changeType: stats.students_trend.startsWith("+") ? "positive" : "negative",
      icon: Users,
      iconColor: "text-green-600",
      bgColor: "bg-green-50"
    },
    {
      title: "Avg. Exam Duration",
      value: formatDuration(stats.avg_exam_duration),
      change: `vs last period`,
      changeType: "positive",
      icon: Clock,
      iconColor: "text-purple-600",
      bgColor: "bg-purple-50"
    }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "bg-red-100 text-red-800";
      case "high": return "bg-orange-100 text-orange-800";
      case "medium": return "bg-yellow-100 text-yellow-800";
      case "low": return "bg-blue-100 text-blue-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const maxValue = activityData.length > 0 
    ? Math.max(...activityData.map(d => Math.max(d.incidents, d.exams)), 1)
    : 1;

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Welcome Section */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Welcome back, Administrator 👋
                </h1>
                <p className="text-gray-600">
                  Monitor exams, review incidents, and manage the system.
                </p>
              </div>
              <div className="flex items-center bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-green-700 font-medium">All Systems Operational</span>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {loading ? (
              <div className="col-span-4 text-center py-8 text-gray-500">Loading...</div>
            ) : (
              statsCards.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                    </div>
                    <div className="flex items-center">
                      {stat.changeType === "positive" ? (
                        <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                      )}
                      <span className={`text-xs font-medium ${
                        stat.changeType === "positive" ? "text-green-600" : "text-red-600"
                      }`}>
                        {stat.change}
                      </span>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</h3>
                    <p className="text-gray-600 text-sm">{stat.title}</p>
                  </div>
                </div>
              );
            })
            )}
          </div>

          {/* Charts and Recent Activity Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Activity Chart */}
            <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Activity Overview</h2>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600">Live</span>
                  </div>
                  <select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value as "today" | "week" | "month")}
                    className="ml-4 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                  </select>
                </div>
              </div>
              
              {/* Simple Bar Chart */}
              <div className="h-64 flex items-end justify-between space-x-2">
                {loading ? (
                  <div className="w-full text-center py-8 text-gray-500">Loading chart data...</div>
                ) : activityData.length === 0 ? (
                  <div className="w-full text-center py-8 text-gray-500">No activity data available</div>
                ) : (
                  activityData.map((data, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center space-y-2">
                    <div className="w-full flex flex-col items-center space-y-1" style={{ height: "200px" }}>
                      <div
                        className="w-full bg-gradient-to-t from-purple-600 to-purple-400 rounded-t transition-all duration-300 hover:opacity-80"
                        style={{ height: `${(data.incidents / maxValue) * 100}%` }}
                        title={`${data.incidents} incidents`}
                      />
                      <div
                        className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t transition-all duration-300 hover:opacity-80"
                        style={{ height: `${(data.exams / maxValue) * 100}%` }}
                        title={`${data.exams} exams`}
                      />
                    </div>
                    <span className="text-xs text-gray-500">{data.time}</span>
                  </div>
                  ))
                )}
              </div>
              
              <div className="flex items-center justify-center space-x-6 mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-purple-600 rounded"></div>
                  <span className="text-sm text-gray-600">Incidents</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-600 rounded"></div>
                  <span className="text-sm text-gray-600">Active Exams</span>
                </div>
              </div>
            </div>

            {/* Recent Incidents */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Recent Incidents</h2>
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              
              <div className="space-y-4">
                {loading ? (
                  <div className="text-center py-4 text-gray-500">Loading incidents...</div>
                ) : recentIncidents.length === 0 ? (
                  <div className="text-center py-4 text-gray-500">No recent incidents</div>
                ) : (
                  recentIncidents.map((incident) => (
                    <div key={incident.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 text-sm">{incident.student_name || 'Unknown Student'}</p>
                          <p className="text-xs text-gray-500">{incident.type}</p>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                          {incident.severity}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-400">{incident.id}</span>
                        <span className="text-xs text-gray-500">{formatTimeAgo(incident.timestamp)}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
              
              <button 
                onClick={() => navigate('/incidents')}
                className="w-full mt-4 py-2 text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors"
              >
                View All Incidents →
              </button>
            </div>
          </div>

          {/* Quick Actions and System Status */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
              <div className="grid grid-cols-2 gap-4">
                <button 
                  onClick={() => navigate('/monitoring')}
                  className="flex flex-col items-center p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg hover:from-purple-100 hover:to-blue-100 transition-all border border-purple-200"
                >
                  <Video className="h-8 w-8 text-purple-600 mb-2" />
                  <span className="text-sm font-medium text-gray-900">Live Monitoring</span>
                </button>
                <button 
                  onClick={() => navigate('/reports')}
                  className="flex flex-col items-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg hover:from-blue-100 hover:to-indigo-100 transition-all border border-blue-200"
                >
                  <FileText className="h-8 w-8 text-blue-600 mb-2" />
                  <span className="text-sm font-medium text-gray-900">Generate Report</span>
                </button>
                <button 
                  onClick={() => navigate('/users')}
                  className="flex flex-col items-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg hover:from-green-100 hover:to-emerald-100 transition-all border border-green-200"
                >
                  <Users className="h-8 w-8 text-green-600 mb-2" />
                  <span className="text-sm font-medium text-gray-900">Manage Users</span>
                </button>
                <button 
                  onClick={() => navigate('/settings')}
                  className="flex flex-col items-center p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg hover:from-orange-100 hover:to-red-100 transition-all border border-orange-200"
                >
                  <Shield className="h-8 w-8 text-orange-600 mb-2" />
                  <span className="text-sm font-medium text-gray-900">System Settings</span>
                </button>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">System Status</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center space-x-3">
                    <Activity className="h-5 w-5 text-green-600" />
                    <span className="text-sm font-medium text-gray-900">Detection System</span>
                  </div>
                  <span className="text-sm text-green-700 font-medium">Operational</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center space-x-3">
                    <Video className="h-5 w-5 text-green-600" />
                    <span className="text-sm font-medium text-gray-900">Camera Network</span>
                  </div>
                  <span className="text-sm text-green-700 font-medium">24/24 Active</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center space-x-3">
                    <BarChart3 className="h-5 w-5 text-green-600" />
                    <span className="text-sm font-medium text-gray-900">Analytics Engine</span>
                  </div>
                  <span className="text-sm text-green-700 font-medium">Running</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-yellow-600" />
                    <span className="text-sm font-medium text-gray-900">Database</span>
                  </div>
                  <span className="text-sm text-yellow-700 font-medium">Syncing</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
