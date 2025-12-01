import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { Settings, Save, Bell, Shield, Database, Camera, AlertTriangle, LogOut } from "lucide-react";

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"general" | "notifications" | "security" | "system">("general");
  const [settings, setSettings] = useState({
    systemName: "ForeSyte",
    timezone: "UTC+5",
    language: "English",
    autoSave: true,
    emailNotifications: true,
    incidentAlerts: true,
    reportGeneration: true,
    twoFactorAuth: false,
    sessionTimeout: 30,
    maxUploadSize: 20,
    cameraRefreshRate: 5,
    incidentThreshold: 75
  });

  const handleSave = () => {
    alert("Settings saved successfully!");
  };

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to logout?")) {
      // Clear all authentication data
      sessionStorage.clear();
      localStorage.clear();
      // Redirect to login page
      navigate("/login", { replace: true });
      window.location.reload(); // Ensure a clean state
    }
  };

  const tabs = [
    { id: "general", label: "General", icon: Settings },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "system", label: "System", icon: Database }
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Header Section */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Settings
            </h1>
            <p className="text-gray-600">
              Manage system configuration and preferences
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar Tabs */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors mb-1 ${
                        activeTab === tab.id
                          ? "bg-purple-50 text-purple-700 border border-purple-200"
                          : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Settings Content */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                {/* General Settings */}
                {activeTab === "general" && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">General Settings</h2>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        System Name
                      </label>
                      <input
                        type="text"
                        value={settings.systemName}
                        onChange={(e) => setSettings({...settings, systemName: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Timezone
                      </label>
                      <select
                        value={settings.timezone}
                        onChange={(e) => setSettings({...settings, timezone: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="UTC+5">UTC+5 (PKT)</option>
                        <option value="UTC+0">UTC+0 (GMT)</option>
                        <option value="UTC-5">UTC-5 (EST)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Language
                      </label>
                      <select
                        value={settings.language}
                        onChange={(e) => setSettings({...settings, language: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="English">English</option>
                        <option value="Urdu">Urdu</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Auto-save Changes
                        </label>
                        <p className="text-sm text-gray-500">Automatically save settings changes</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.autoSave}
                        onChange={(e) => setSettings({...settings, autoSave: e.target.checked})}
                        className="h-5 w-5 text-purple-600 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                )}

                {/* Notifications Settings */}
                {activeTab === "notifications" && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Notification Settings</h2>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Email Notifications
                          </label>
                          <p className="text-sm text-gray-500">Receive notifications via email</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={settings.emailNotifications}
                          onChange={(e) => setSettings({...settings, emailNotifications: e.target.checked})}
                          className="h-5 w-5 text-purple-600 focus:ring-purple-500"
                        />
                      </div>

                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Incident Alerts
                          </label>
                          <p className="text-sm text-gray-500">Get notified when incidents are detected</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={settings.incidentAlerts}
                          onChange={(e) => setSettings({...settings, incidentAlerts: e.target.checked})}
                          className="h-5 w-5 text-purple-600 focus:ring-purple-500"
                        />
                      </div>

                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Report Generation
                          </label>
                          <p className="text-sm text-gray-500">Notify when reports are ready</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={settings.reportGeneration}
                          onChange={(e) => setSettings({...settings, reportGeneration: e.target.checked})}
                          className="h-5 w-5 text-purple-600 focus:ring-purple-500"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Security Settings */}
                {activeTab === "security" && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Security Settings</h2>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Two-Factor Authentication
                          </label>
                          <p className="text-sm text-gray-500">Add an extra layer of security</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={settings.twoFactorAuth}
                          onChange={(e) => setSettings({...settings, twoFactorAuth: e.target.checked})}
                          className="h-5 w-5 text-purple-600 focus:ring-purple-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Session Timeout (minutes)
                        </label>
                        <input
                          type="number"
                          value={settings.sessionTimeout}
                          onChange={(e) => setSettings({...settings, sessionTimeout: parseInt(e.target.value)})}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          min="5"
                          max="120"
                        />
                      </div>

                      {/* Logout Section */}
                      <div className="mt-8 pt-6 border-t border-gray-200">
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <h3 className="text-lg font-semibold text-red-900 mb-2">Account Actions</h3>
                          <p className="text-sm text-red-700 mb-4">
                            Sign out of your account. You will need to login again to access the system.
                          </p>
                          <button
                            onClick={handleLogout}
                            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                          >
                            <LogOut className="h-5 w-5" />
                            <span>Logout</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* System Settings */}
                {activeTab === "system" && (
                  <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">System Settings</h2>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Max Upload Size (MB)
                        </label>
                        <input
                          type="number"
                          value={settings.maxUploadSize}
                          onChange={(e) => setSettings({...settings, maxUploadSize: parseInt(e.target.value)})}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          min="1"
                          max="100"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Camera Refresh Rate (seconds)
                        </label>
                        <input
                          type="number"
                          value={settings.cameraRefreshRate}
                          onChange={(e) => setSettings({...settings, cameraRefreshRate: parseInt(e.target.value)})}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          min="1"
                          max="60"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Incident Detection Threshold (%)
                        </label>
                        <input
                          type="number"
                          value={settings.incidentThreshold}
                          onChange={(e) => setSettings({...settings, incidentThreshold: parseInt(e.target.value)})}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          min="0"
                          max="100"
                        />
                        <p className="text-sm text-gray-500 mt-1">
                          Minimum confidence level to flag an incident
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Save Button */}
                <div className="mt-8 pt-6 border-t border-gray-200">
                  <button
                    onClick={handleSave}
                    className="flex items-center space-x-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    <Save className="h-5 w-5" />
                    <span>Save Settings</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

