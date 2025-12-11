import React from 'react';

export const Button = ({ children, onClick, className = "", variant = "primary", disabled = false, type = "button" }: any) => {
    const baseStyle = "px-4 py-2 rounded-lg font-medium btn flex items-center justify-center";
    const variants = {
        primary: "bg-violet-600 hover:bg-violet-500 text-white",
        secondary: "bg-slate-700 hover:bg-slate-600 text-slate-200",
        outline: "border border-slate-600 hover:border-slate-500 text-slate-300"
    };

    return (
        <button
            type={type}
            disabled={disabled}
            onClick={onClick}
            className={`${baseStyle} ${variants[variant as keyof typeof variants]} ${className} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
            {children}
        </button>
    );
};

export const Input = ({ value, onChange, placeholder, type = "text", className = "" }: any) => (
    <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-100 placeholder-slate-500 ${className}`}
    />
);

export const Card = ({ children, className = "" }: any) => (
    <div className={`glass rounded-xl p-6 ${className}`}>
        {children}
    </div>
);
