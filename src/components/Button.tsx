import React from "react";

interface ButtonProps {
  text: string;
  type?: "button" | "submit" | "reset";
  className?: string;
  onClick?: () => void;
  disabled?: boolean; // Add this line
}

const Button: React.FC<ButtonProps> = ({
  text,
  type = "button",
  className = "",
  onClick,
  disabled = false, // Add this line with default value
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled} // Add this line
      className={`w-full px-4 py-2 text-white bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 disabled:cursor-not-allowed rounded-md transition-colors ${className}`}
    >
      {text}
    </button>
  );
};

export default Button;
