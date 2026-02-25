import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export const TextArea: React.FC<TextAreaProps> = ({ label, className = '', ...props }) => {
  return (
    <div className="w-full">
      {label && <label className="block text-sm font-medium text-stone-600 mb-2">{label}</label>}
      <textarea
        className={`w-full p-4 rounded-2xl bg-white border-0 shadow-sm ring-1 ring-stone-200 focus:ring-2 focus:ring-rose-300 outline-none transition-all placeholder:text-stone-400 text-stone-700 resize-none min-h-[150px] ${className}`}
        {...props}
      />
    </div>
  );
};
