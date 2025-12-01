import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Shield, Eye, Search } from "lucide-react";

const SelectRole: React.FC = () => {
  const [email, setEmail] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [role, setRole] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const emailParam = params.get("email");
    const nameParam = params.get("name");

    if (!emailParam) {
      setError("Email not provided. Please try logging in again.");
      return;
    }

    setEmail(emailParam);
    setName(nameParam || "");
  }, [location.search]);

  const handleSubmit = async () => {
    if (!role) {
      setError("Please select a role.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/register-role", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, name, role }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Registration failed.");
      }

      const data = await response.json();

      // Save token and user info
      sessionStorage.setItem("token", data.access_token);
      sessionStorage.setItem("user_type", data.user_type);
      sessionStorage.setItem("user_id", data.id);

      // Redirect based on role
      if (data.user_type === "investigator") {
        navigate("/investigator/dashboard", { replace: true });
      } else if (data.user_type === "student") {
        navigate("/student/dashboard", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-gray-50 flex items-center justify-center px-4 py-16">
      {/* Minimal card */}
      <div className="w-full max-w-2xl bg-white border border-gray-200 shadow-sm rounded-2xl p-8 md:p-10">
          <div className="mb-8">
            <h1 className="text-2xl md:text-3xl font-semibold text-gray-900 text-center">
              Welcome{name ? `, ${name}` : ", User"} <span className="align-middle">👋</span>
            </h1>
            <p className="text-gray-500 text-center mt-2">Select your role to continue</p>
            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-md text-sm text-center">
                {error}
              </div>
            )}
          </div>

          {/* Roles grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-8">
            {[
              { label: "Admin", icon: Shield },
              { label: "Invigilator", icon: Eye },
              { label: "Investigator", icon: Search },
            ].map(({ label, icon: Icon }) => {
              const value = label.toLowerCase();
              const isActive = role === value;
              return (
                <button
                  key={label}
                  type="button"
                  onClick={() => setRole(value)}
                  className={`group relative rounded-xl p-5 text-left transition-all duration-200 border ${
                    isActive
                      ? "bg-purple-50 border-purple-200 ring-2 ring-purple-200"
                      : "bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 transition-colors ${
                    isActive ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`font-medium ${isActive ? "text-gray-900" : "text-gray-800"}`}>{label}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      isActive ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600"
                    }`}>
                      {isActive ? "Selected" : "Choose"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`w-full py-3 rounded-lg font-medium transition-colors ${
              loading
                ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                : "bg-purple-600 text-white hover:bg-purple-700"
            }`}
          >
            {loading ? "Submitting..." : "Continue"}
          </button>
        </div>
    </div>
  );
};

export default SelectRole;
