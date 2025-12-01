import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  Settings,
  Activity,
  Users,
  Video,
  Eye,
} from "lucide-react";

const InvestigatorSidebar = () => {
  const navItems = [
    {
      name: "Dashboard",
      path: "/investigator/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Violations",
      path: "/investigator/violations",
      icon: AlertTriangle,
    },
    {
      name: "Student Activities",
      path: "/investigator/student-activities",
      icon: Activity,
    },
    {
      name: "Invigilator Activities",
      path: "/investigator/invigilator-activities",
      icon: Users,
    },
    {
      name: "Video Processing",
      path: "/investigator/video-processing",
      icon: Video,
    },
    {
      name: "Live Monitoring",
      path: "/investigator/live-monitoring",
      icon: Eye,
    },
    {
      name: "Reports",
      path: "/investigator/reports",
      icon: FileText,
    },
    {
      name: "Settings",
      path: "/investigator/settings",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 bg-gray-900 text-white h-screen fixed left-0 top-0 overflow-y-auto flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">F</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">ForeSyte</h1>
            <p className="text-xs text-gray-400">Investigator Portal</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? "bg-lime-300 text-gray-900 font-medium"
                  : "text-gray-300 hover:text-white hover:bg-gray-800"
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 flex-shrink-0">
        <p className="text-xs text-gray-400 text-center">
          © 2024 ForeSyte AI
        </p>
      </div>
    </aside>
  );
};

export default InvestigatorSidebar;

