// import React, { useState, useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import { Lock, Eye, EyeOff } from "lucide-react";
// import login_illustration from "../assets/login_illustration.png";
// import Logo from "../components/Logo";
// import Slogan from "../components/Slogan";

// const Illustration = () => {
//   return (
//     <div className="flex justify-center items-center animate-float">
//       <div className="w-130 h-130 flex items-center justify-center">
//         <img
//           src={login_illustration}
//           alt="Login Illustration"
//           className="max-w-full max-h-full object-contain drop-shadow-2xl"
//         />
//       </div>
//     </div>
//   );
// };

// const LoginForm = () => {
//   const navigate = useNavigate();
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const [showPassword, setShowPassword] = useState(false);
//   const [isLoading, setIsLoading] = useState(false);

//   const handleSubmit = async (
//     e: React.MouseEvent<HTMLButtonElement, MouseEvent>
//   ): Promise<void> => {
//     e.preventDefault();
//     setIsLoading(true);

//     try {
//       const response = await fetch("http://127.0.0.1:8000/auth/login", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({
//           email: email,
//           password: password,
//         }),
//       });

//       if (!response.ok) {
//         const error = await response.json();
//         alert(`Error: ${error.detail || "Login failed"}`);
//         return;
//       }

//       const data = await response.json();
//       console.log("✅ Login successful:", data);

//       // Store the token and user info - matching backend response
//       sessionStorage.setItem("token", data.access_token);
//       sessionStorage.setItem("user_type", data.user_type);
//       sessionStorage.setItem("user_id", data.id); // Backend sends 'id', not 'user_id'

//       navigate("/dashboard");
//     } catch (err) {
//       console.error("❌ Login failed:", err);
//       alert("Something went wrong! Please check your connection.");
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="w-full max-w-md animate-slide-up">
//       <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/20 hover:shadow-3xl transition-all duration-500 hover:scale-[1.02]">
//         <div className="text-center mb-8">
//           <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3 animate-fade-in">
//             Welcome Back
//           </h2>
//           <p className="text-gray-600 text-lg animate-fade-in-delay">
//             Sign in to your account
//           </p>
//         </div>

//         <div className="space-y-6">
//           {/* Email Field */}
//           <div className="space-y-2">
//             <label
//               htmlFor="email"
//               className="block text-sm font-medium text-gray-700"
//             >
//               Email
//             </label>
//             <input
//               id="email"
//               type="email"
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               placeholder="Enter your email"
//               required
//               className="block w-full px-3 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
//             />
//           </div>

//           {/* Password Field */}
//           <div className="space-y-2 animate-slide-in-right">
//             <label
//               htmlFor="password"
//               className="block text-sm font-medium text-gray-700"
//             >
//               Password
//             </label>
//             <div className="relative group">
//               <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors duration-300 group-focus-within:text-purple-500">
//                 <Lock className="h-5 w-5 text-gray-400 group-focus-within:text-purple-500" />
//               </div>
//               <input
//                 id="password"
//                 type={showPassword ? "text" : "password"}
//                 value={password}
//                 onChange={(e) => setPassword(e.target.value)}
//                 className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-gray-50/50 focus:bg-white hover:bg-white/80 transform focus:scale-[1.02]"
//                 placeholder="Enter your password"
//                 required
//               />
//               <button
//                 type="button"
//                 className="absolute inset-y-0 right-0 pr-3 flex items-center transition-all duration-300 hover:scale-110"
//                 onClick={() => setShowPassword(!showPassword)}
//               >
//                 {showPassword ? (
//                   <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
//                 ) : (
//                   <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
//                 )}
//               </button>
//             </div>
//           </div>

//           {/* Remember Me & Forgot Password */}
//           <div className="flex items-center justify-between animate-fade-in-up">
//             <div className="flex items-center">
//               <input
//                 id="remember"
//                 type="checkbox"
//                 className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded transition-all duration-300"
//               />
//               <label
//                 htmlFor="remember"
//                 className="ml-2 block text-sm text-gray-700 hover:text-gray-900 transition-colors duration-300"
//               >
//                 Remember me
//               </label>
//             </div>
//             <div>
//               <a
//                 href="#"
//                 className="text-sm text-purple-600 hover:text-purple-500 font-medium transition-all duration-300 hover:scale-105"
//               >
//                 Forgot password?
//               </a>
//             </div>
//           </div>

//           {/* Login Button */}
//           <button
//             onClick={handleSubmit}
//             disabled={isLoading}
//             className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-medium text-white 
//              bg-gradient-to-r from-purple-500 to-blue-600 
//              hover:from-purple-600 hover:to-blue-700
//              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500
//              transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl
//              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
//              animate-pulse-slow"
//           >
//             {isLoading ? (
//               <>
//                 <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
//                 Signing In...
//               </>
//             ) : (
//               "Sign In"
//             )}
//           </button>
//         </div>

//         {/* Sign Up Link */}
//         <div className="mt-6 text-center animate-fade-in-delay-2">
//           <p className="text-sm text-gray-600">
//             Don't have an account?{" "}
//             <a
//               href="/signup"
//               className="font-medium text-purple-600 hover:text-purple-500 transition-all duration-300 hover:scale-105 inline-block"
//             >
//               Sign up here
//             </a>
//           </p>
//         </div>

//         {/* Divider */}
//         <div className="mt-6">
//           <div className="relative">
//             <div className="absolute inset-0 flex items-center">
//               <div className="w-full border-t border-gray-300/50" />
//             </div>
//           </div>
//         </div>
//         {/* Google Login Button */}
//         <div className="mt-6 animate-fade-in-up">
//           <button
//             onClick={() =>
//               (window.location.href = "http://127.0.0.1:8000/auth/google")
//             }
//             className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-xl shadow-sm 
//       bg-white hover:bg-gray-50 transition-all duration-300 hover:shadow-md transform hover:scale-[1.02]"
//           >
//             {/* Google Logo */}
//             <img
//               src="https://www.svgrepo.com/show/475656/google-color.svg"
//               alt="Google Logo"
//               className="h-5 w-5"
//             />
//             <span className="text-gray-700 font-medium">
//               Sign in with Google
//             </span>
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// const LeftSide = () => {
//   return (
//     <div className="w-1/3 bg-gradient-to-br from-purple-400 via-purple-500 to-blue-600 flex flex-col h-screen relative overflow-hidden">
//       {/* Animated background elements */}
//       <div className="absolute inset-0">
//         <div className="absolute top-20 left-10 w-32 h-32 bg-white/10 rounded-full blur-xl animate-pulse"></div>
//         <div className="absolute bottom-20 right-10 w-24 h-24 bg-white/20 rounded-full blur-lg animate-bounce"></div>
//         <div className="absolute top-1/2 left-1/4 w-16 h-16 bg-white/15 rounded-full blur-md animate-float-delayed"></div>
//       </div>

//       {/* Logo at top center */}
//       <div className="flex justify-center pt-8 pb-2 animate-slide-down">
//         <div className="transform hover:scale-110 transition-transform duration-300">
//           <Logo />
//         </div>
//       </div>

//       {/* Slogan just under logo */}
//       <div className="flex justify-center px-6 -mt-12">
//         <div className="animate-fade-in-up-delayed">
//           <Slogan />
//         </div>
//       </div>

//       {/* Spacer to push rest of content down if needed */}
//       <div className="flex-1"></div>
//     </div>
//   );
// };

// const RightSide = () => {
//   return (
//     <div className="w-2/3 bg-gradient-to-br from-gray-50 to-white flex items-center justify-center p-8 h-screen relative overflow-hidden">
//       {/* Subtle background pattern */}
//       <div className="absolute inset-0 bg-gradient-to-br from-purple-50/50 to-blue-50/50"></div>
//       <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(147,51,234,0.1),transparent_70%)]"></div>

//       <div className="relative z-10">
//         <LoginForm />
//       </div>
//     </div>
//   );
// };

// const LoginPage = () => {
//   const [mounted, setMounted] = useState(false);

//   useEffect(() => {
//     setMounted(true);
//   }, []);

//   return (
//     <>
//       {/* Custom CSS for animations */}
//       <style>{`
//         @keyframes float {
//           0%,
//           100% {
//             transform: translateY(0px);
//           }
//           50% {
//             transform: translateY(-20px);
//           }
//         }

//         @keyframes float-delayed {
//           0%,
//           100% {
//             transform: translateY(0px);
//           }
//           50% {
//             transform: translateY(-15px);
//           }
//         }

//         @keyframes slide-up {
//           from {
//             opacity: 0;
//             transform: translateY(30px);
//           }
//           to {
//             opacity: 1;
//             transform: translateY(0);
//           }
//         }

//         @keyframes slide-down {
//           from {
//             opacity: 0;
//             transform: translateY(-30px);
//           }
//           to {
//             opacity: 1;
//             transform: translateY(0);
//           }
//         }

//         @keyframes slide-in-left {
//           from {
//             opacity: 0;
//             transform: translateX(-30px);
//           }
//           to {
//             opacity: 1;
//             transform: translateX(0);
//           }
//         }

//         @keyframes slide-in-right {
//           from {
//             opacity: 0;
//             transform: translateX(30px);
//           }
//           to {
//             opacity: 1;
//             transform: translateX(0);
//           }
//         }

//         @keyframes fade-in {
//           from {
//             opacity: 0;
//           }
//           to {
//             opacity: 1;
//           }
//         }

//         @keyframes fade-in-up {
//           from {
//             opacity: 0;
//             transform: translateY(20px);
//           }
//           to {
//             opacity: 1;
//             transform: translateY(0);
//           }
//         }

//         .animate-float {
//           animation: float 6s ease-in-out infinite;
//         }

//         .animate-float-delayed {
//           animation: float-delayed 8s ease-in-out infinite;
//         }

//         .animate-slide-up {
//           animation: slide-up 0.8s ease-out;
//         }

//         .animate-slide-down {
//           animation: slide-down 0.6s ease-out;
//         }

//         .animate-slide-in-left {
//           animation: slide-in-left 0.6s ease-out 0.2s both;
//         }

//         .animate-slide-in-right {
//           animation: slide-in-right 0.6s ease-out 0.4s both;
//         }

//         .animate-fade-in {
//           animation: fade-in 0.8s ease-out;
//         }

//         .animate-fade-in-delay {
//           animation: fade-in 0.8s ease-out 0.3s both;
//         }

//         .animate-fade-in-delay-2 {
//           animation: fade-in 0.8s ease-out 0.6s both;
//         }

//         .animate-fade-in-up {
//           animation: fade-in-up 0.6s ease-out 0.5s both;
//         }

//         .animate-fade-in-up-delayed {
//           animation: fade-in-up 1s ease-out 0.8s both;
//         }

//         .animate-pulse-slow {
//           animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
//         }

//         .shadow-3xl {
//           box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
//         }
//       `}</style>

//       <div
//         className={`flex h-screen bg-white overflow-hidden relative ${
//           mounted ? "opacity-100" : "opacity-0"
//         } transition-opacity duration-500`}
//       >
//         <LeftSide />
//         <RightSide />
//         {/* Illustration positioned at the boundary with improved positioning */}
//         <div className="absolute top-[25%] left-[27%] transform -translate-x-1/2 pointer-events-none z-20">
//           <Illustration />
//         </div>
//       </div>
//     </>
//   );
// };

// export default LoginPage;
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, Eye, EyeOff } from "lucide-react";
import login_illustration from "../assets/login_illustration.png";
import Logo from "../components/Logo";
import Slogan from "../components/Slogan";

// Interface for backend API response
interface LoginResponse {
  access_token: string;
  user_type: "student" | "investigator" | "admin" | "invigilator";
  id: string;
}

const Illustration: React.FC = () => {
  return (
    <div className="flex justify-center items-center animate-float">
      <div className="w-130 h-130 flex items-center justify-center">
        <img
          src={login_illustration}
          alt="Login Illustration"
          className="max-w-full max-h-full object-contain drop-shadow-2xl"
        />
      </div>
    </div>
  );
};

const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const isStudentEmail = (emailAddress: string): boolean => {
    const studentEmailPattern = /^i\d{5}@(?:nu|isb)\.nu\.edu\.pk$/i;
    return studentEmailPattern.test(emailAddress);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setIsLoading(true);

    // ============================================================================
    // TEMPORARY: Frontend-only navigation (for development without backend)
    // ============================================================================
    // COMMENTED OUT: Now using proper backend authentication
    // ============================================================================
    /*
    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Determine user type based on email pattern (temporary logic)
    let userType: string = "admin"; // default
    if (isStudentEmail(email)) {
      userType = "student";
    } else if (email.includes("investigator") || email.includes("inv")) {
      userType = "investigator";
    } else if (email.includes("invigilator") || email.includes("invig")) {
      userType = "invigilator";
    }
    
    // Store mock data in sessionStorage
    sessionStorage.setItem("token", "mock_token_for_development");
    sessionStorage.setItem("user_type", userType);
    sessionStorage.setItem("user_id", "mock_user_id");
    
    console.log("✅ Mock login successful - User type:", userType);
    console.log("✅ Token stored in sessionStorage");
    
    // Navigate based on user type
    setIsLoading(false);
    
    if (userType === "student") {
      navigate("/student/dashboard", { replace: true });
    } else {
      navigate("/dashboard", { replace: true });
    }
    
    return;
    */
    // ============================================================================
    // END OF TEMPORARY CODE
    // ============================================================================

    // ============================================================================
    // BACKEND API CALL - Proper authentication with backend
    // ============================================================================
    try {
      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        alert(`Error: ${error.detail || "Login failed"}`);
        setIsLoading(false);
        return;
      }

      const data: LoginResponse = await response.json();
      console.log("✅ Login successful:", data);

      // Store the token and user info
      sessionStorage.setItem("token", data.access_token);
      sessionStorage.setItem("user_type", data.user_type);
      sessionStorage.setItem("user_id", data.id);
      
      // Store user info if available in response (for signup it includes name/email)
      if ((data as any).name || (data as any).email) {
        const userInfo = {
          id: data.id,
          name: (data as any).name || "",
          email: (data as any).email || email,
          user_type: data.user_type,
        };
        sessionStorage.setItem("userInfo", JSON.stringify(userInfo));
      }

      // Navigate based on user type
      if (data.user_type === "student" || isStudentEmail(email)) {
        navigate("/student/dashboard");
      } else if (data.user_type === "investigator") {
        navigate("/investigator/dashboard");
      } else if (data.user_type === "admin") {
        navigate("/dashboard");
      } else if (data.user_type === "invigilator") {
        navigate("/dashboard");
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      console.error("❌ Login failed:", err);
      alert("Something went wrong! Please check your connection.");
    } finally {
      setIsLoading(false);
    }
    // ============================================================================
    // END OF BACKEND CODE
    // ============================================================================
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md animate-slide-up">
      <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/20 hover:shadow-3xl transition-all duration-500 hover:scale-[1.02]">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3 animate-fade-in">
            Welcome Back
          </h2>
          <p className="text-gray-600 text-lg animate-fade-in-delay">
            Sign in to your account
          </p>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              className="block w-full px-3 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="space-y-2 animate-slide-in-right">
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors duration-300 group-focus-within:text-purple-500">
                <Lock className="h-5 w-5 text-gray-400 group-focus-within:text-purple-500" />
              </div>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 bg-gray-50/50 focus:bg-white hover:bg-white/80 transform focus:scale-[1.02]"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center transition-all duration-300 hover:scale-110"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between animate-fade-in-up">
            <div className="flex items-center">
              <input
                id="remember"
                type="checkbox"
                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded transition-all duration-300"
              />
              <label
                htmlFor="remember"
                className="ml-2 block text-sm text-gray-700 hover:text-gray-900 transition-colors duration-300"
              >
                Remember me
              </label>
            </div>
            <div>
              <a
                href="#"
                className="text-sm text-purple-600 hover:text-purple-500 font-medium transition-all duration-300 hover:scale-105"
              >
                Forgot password?
              </a>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-medium text-white 
             bg-gradient-to-r from-purple-500 to-blue-600 
             hover:from-purple-600 hover:to-blue-700
             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500
             transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl
             disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
             animate-pulse-slow"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Signing In...
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </div>

        <div className="mt-6 text-center animate-fade-in-delay-2">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <a
              href="/signup"
              className="font-medium text-purple-600 hover:text-purple-500 transition-all duration-300 hover:scale-105 inline-block"
            >
              Sign up here
            </a>
          </p>
        </div>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300/50" />
            </div>
          </div>
        </div>

        <div className="mt-6 animate-fade-in-up">
          <button
            type="button"
            onClick={() =>
              (window.location.href = "http://127.0.0.1:8000/auth/google")
            }
            className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-xl shadow-sm 
      bg-white hover:bg-gray-50 transition-all duration-300 hover:shadow-md transform hover:scale-[1.02]"
          >
            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              alt="Google Logo"
              className="h-5 w-5"
            />
            <span className="text-gray-700 font-medium">
              Sign in with Google
            </span>
          </button>
        </div>
      </div>
    </form>
  );
};

const LeftSide: React.FC = () => {
  return (
    <div className="w-1/3 bg-gradient-to-br from-purple-400 via-purple-500 to-blue-600 flex flex-col h-screen relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-20 left-10 w-32 h-32 bg-white/10 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-24 h-24 bg-white/20 rounded-full blur-lg animate-bounce"></div>
        <div className="absolute top-1/2 left-1/4 w-16 h-16 bg-white/15 rounded-full blur-md animate-float-delayed"></div>
      </div>

      <div className="flex justify-center pt-8 pb-2 animate-slide-down">
        <div className="transform hover:scale-110 transition-transform duration-300">
          <Logo />
        </div>
      </div>

      <div className="flex justify-center px-6 -mt-12">
        <div className="animate-fade-in-up-delayed">
          <Slogan />
        </div>
      </div>

      <div className="flex-1"></div>
    </div>
  );
};

const RightSide: React.FC = () => {
  return (
    <div className="w-2/3 bg-gradient-to-br from-gray-50 to-white flex items-center justify-center p-8 h-screen relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50/50 to-blue-50/50"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(147,51,234,0.1),transparent_70%)]"></div>

      <div className="relative z-10">
        <LoginForm />
      </div>
    </div>
  );
};

const LoginPage: React.FC = () => {
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }

        @keyframes slide-up {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slide-down {
          from { opacity: 0; transform: translateY(-30px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slide-in-left {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slide-in-right {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }

        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-float-delayed { animation: float-delayed 8s ease-in-out infinite; }
        .animate-slide-up { animation: slide-up 0.8s ease-out; }
        .animate-slide-down { animation: slide-down 0.6s ease-out; }
        .animate-slide-in-left { animation: slide-in-left 0.6s ease-out 0.2s both; }
        .animate-slide-in-right { animation: slide-in-right 0.6s ease-out 0.4s both; }
        .animate-fade-in { animation: fade-in 0.8s ease-out; }
        .animate-fade-in-delay { animation: fade-in 0.8s ease-out 0.3s both; }
        .animate-fade-in-delay-2 { animation: fade-in 0.8s ease-out 0.6s both; }
        .animate-fade-in-up { animation: fade-in-up 0.6s ease-out 0.5s both; }
        .animate-fade-in-up-delayed { animation: fade-in-up 1s ease-out 0.8s both; }
        .animate-pulse-slow { animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .shadow-3xl { box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); }
      `}</style>

      <div
        className={`flex h-screen bg-white overflow-hidden relative ${
          mounted ? "opacity-100" : "opacity-0"
        } transition-opacity duration-500`}
      >
        <LeftSide />
        <RightSide />
        <div className="absolute top-[25%] left-[27%] transform -translate-x-1/2 pointer-events-none z-20">
          <Illustration />
        </div>
      </div>
    </>
  );
};

export default LoginPage;