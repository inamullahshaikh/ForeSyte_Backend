import React from "react";
import type { ChangeEvent } from "react";
interface InputFieldProps {
  label?: string;
  type?: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
}

const InputField: React.FC<InputFieldProps> = ({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
}) => (
  <div className="mb-4 w-full">
    {label && <label className="block text-gray-700 mb-1">{label}</label>}
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
    />
  </div>
);

export default InputField;
