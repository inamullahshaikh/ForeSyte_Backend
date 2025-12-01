import React from "react";

interface SocialButtonProps {
  provider: "Google" | "Facebook";
  onClick?: () => void;
}

const SocialButton: React.FC<SocialButtonProps> = ({ provider, onClick }) => {
  const colors =
    provider === "Google"
      ? "bg-red-500 hover:bg-red-600"
      : "bg-blue-600 hover:bg-blue-700";
  return (
    <button
      onClick={onClick}
      className={`w-full py-2 px-4 rounded-lg text-white ${colors} mb-2 transition-[var(--transition)]`}
    >
      Sign Up with {provider}
    </button>
  );
};

export default SocialButton;
