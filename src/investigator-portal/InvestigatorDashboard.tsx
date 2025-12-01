import { useEffect, useState } from "react";
import InvestigatorHeader from "./components/InvestigatorHeader";
import InvestigatorSidebar from "./components/InvestigatorSidebar";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Activity,
} from "lucide-react";
import { apiService } from "../services/api";

interface DashboardStats {
  totalViolations: number;
  pendingReviews: number;
  resolvedToday: number;
  activeExams: number;
}

interface RecentActivity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  severity: string;
  status: string;
}

const InvestigatorDashboard = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalViolations: 0,
    pendingReviews: 0,
    resolvedToday: 0,
    activeExams: 0,
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"today" | "week" | "month">("today");

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Fetch high-level dashboard stats (active exams + incidents)
        const statsResponse = await apiService.getDashboardStats(period);

        // Fetch violations to derive total / pending / resolved counts
        const violationsResponse = await apiService.getViolations();

        let totalViolations = 0;
        let pendingReviews = 0;
        let resolvedToday = 0;

        if (violationsResponse.data && Array.isArray(violationsResponse.data)) {
          const violations = violationsResponse.data as any[];
          totalViolations = violations.length;
          pendingReviews = violations.filter(
            (v) => v.status === "pending"
          ).length;

          const today = new Date().toDateString();
          resolvedToday = violations.filter((v) => {
            if (!v.timestamp) return false;
            const d = new Date(v.timestamp);
            return v.status === "confirmed" && d.toDateString() === today;
          }).length;
        }

        setStats({
          totalViolations,
          pendingReviews,
          resolvedToday,
          activeExams:
            (statsResponse.data as any)?.active_exams ??
            (statsResponse.data as any)?.activeExams ??
            0,
        });

        // Fetch recent incidents and map into RecentActivity cards
        const incidentsResponse = await apiService.getRecentIncidents(10);
        if (
          incidentsResponse.data &&
          Array.isArray(incidentsResponse.data)
        ) {
          const activities = (incidentsResponse.data as any[]).map(
            (incident) => {
              const timestamp = incident.timestamp
                ? new Date(incident.timestamp)
                : null;

              return {
                id: incident.id,
                type: incident.type || "Incident",
                description: incident.student_name
                  ? `${incident.student_name} - ${incident.type || "Activity"}`
                  : incident.type || "Activity",
                timestamp: timestamp
                  ? timestamp.toLocaleString()
                  : "Unknown time",
                severity: incident.severity || "low",
                // We don't have review status on this endpoint yet, so default to pending
                status: "pending",
              } as RecentActivity;
            }
          );
          setRecentActivities(activities);
        } else {
          setRecentActivities([]);
        }
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [period]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "text-red-600 bg-red-100";
      case "medium":
        return "text-yellow-600 bg-yellow-100";
      case "low":
        return "text-blue-600 bg-blue-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "text-orange-600 bg-orange-100";
      case "resolved":
        return "text-green-600 bg-green-100";
      case "dismissed":
        return "text-gray-600 bg-gray-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <InvestigatorSidebar />
        <div className="flex-1 flex flex-col overflow-hidden ml-64">
          <InvestigatorHeader />
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <InvestigatorSidebar />
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <InvestigatorHeader />
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Period Filter */}
          <div className="mb-6 flex justify-end">
            <div className="inline-flex rounded-lg border border-gray-300 bg-white">
              <button
                onClick={() => setPeriod("today")}
                className={`px-4 py-2 text-sm font-medium ${
                  period === "today"
                    ? "bg-indigo-900 text-white"
                    : "text-gray-700 hover:bg-gray-50"
                } rounded-l-lg`}
              >
                Today
              </button>
              <button
                onClick={() => setPeriod("week")}
                className={`px-4 py-2 text-sm font-medium ${
                  period === "week"
                    ? "bg-indigo-900 text-white"
                    : "text-gray-700 hover:bg-gray-50"
                } border-l border-gray-300`}
              >
                This Week
              </button>
              <button
                onClick={() => setPeriod("month")}
                className={`px-4 py-2 text-sm font-medium ${
                  period === "month"
                    ? "bg-indigo-900 text-white"
                    : "text-gray-700 hover:bg-gray-50"
                } border-l border-gray-300 rounded-r-lg`}
              >
                This Month
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Violations</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.totalViolations}</p>
                </div>
                <div className="p-3 bg-red-100 rounded-lg">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Pending Reviews</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.pendingReviews}</p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <Clock className="w-8 h-8 text-yellow-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Resolved Today</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.resolvedToday}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Active Exams</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.activeExams}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="w-8 h-8 text-blue-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activities */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <Activity className="w-6 h-6 text-indigo-900" />
                  Recent Activities
                </h2>
                <button className="text-sm text-indigo-900 hover:text-indigo-700 font-medium">
                  View All
                </button>
              </div>
            </div>

            <div className="divide-y divide-gray-200">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900">{activity.type}</h3>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(
                            activity.severity
                          )}`}
                        >
                          {activity.severity.toUpperCase()}
                        </span>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                            activity.status
                          )}`}
                        >
                          {activity.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{activity.description}</p>
                      <p className="text-xs text-gray-500">{activity.timestamp}</p>
                    </div>
                    <button className="ml-4 px-4 py-2 bg-indigo-900 text-white rounded-lg hover:bg-indigo-800 transition-colors text-sm">
                      Review
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvestigatorDashboard;

