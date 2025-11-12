/**
 * Input Component - Advanced UI
 * 
 * Input avec glassmorphism, icons, validation states.
 * Support dark mode et animations.
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Eye, EyeOff } from 'lucide-react';
import { cn, variants as designVariants } from '@/lib/design-system';

// ============================================================================
// TYPES
// ============================================================================

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
    label?: string;
    error?: string;
    success?: string;
    hint?: string;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
    variant?: 'default' | 'glass' | 'gradient';
    inputSize?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
}

// ============================================================================
// INPUT COMPONENT
// ============================================================================

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    (
        {
            label,
            error,
            success,
            hint,
            leftIcon,
            rightIcon,
            variant = 'default',
            inputSize = 'md',
            fullWidth = true,
            type = 'text',
            className,
            disabled,
            ...props
        },
        ref
    ) => {
        const [showPassword, setShowPassword] = React.useState(false);
        const [isFocused, setIsFocused] = React.useState(false);

        const isPassword = type === 'password';
        const inputType = isPassword && showPassword ? 'text' : type;

        return (
            <div className={cn('space-y-2', fullWidth && 'w-full')}>
                {/* Label */}
                {label && (
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        {label}
                    </label>
                )}

                {/* Input Container */}
                <motion.div
                    className="relative"
                    animate={isFocused ? { scale: 1.01 } : { scale: 1 }}
                    transition={{ duration: 0.2 }}
                >
                    {/* Left Icon */}
                    {leftIcon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                            {leftIcon}
                        </div>
                    )}

                    {/* Input */}
                    <input
                        ref={ref}
                        type={inputType}
                        className={cn(
                            designVariants.input.base,
                            designVariants.input.variant[variant],
                            designVariants.input.size[inputSize],
                            leftIcon && 'pl-10',
                            (rightIcon || isPassword) && 'pr-10',
                            error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
                            success && 'border-green-500 focus:border-green-500 focus:ring-green-500',
                            disabled && 'bg-gray-100 dark:bg-gray-900',
                            className
                        )}
                        disabled={disabled}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        {...props}
                    />

                    {/* Right Icon / Password Toggle */}
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                        {isPassword && (
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                                tabIndex={-1}
                            >
                                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                        )}

                        {!isPassword && rightIcon && (
                            <div className="text-gray-400">
                                {rightIcon}
                            </div>
                        )}

                        {/* Validation Icons */}
                        {error && <AlertCircle className="h-5 w-5 text-red-500" />}
                        {success && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                    </div>
                </motion.div>

                {/* Messages */}
                <div className="min-h-[20px]">
                    {error && (
                        <motion.p
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-sm text-red-500 flex items-center gap-1"
                        >
                            <AlertCircle className="h-4 w-4" />
                            {error}
                        </motion.p>
                    )}

                    {success && !error && (
                        <motion.p
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-sm text-green-500 flex items-center gap-1"
                        >
                            <CheckCircle2 className="h-4 w-4" />
                            {success}
                        </motion.p>
                    )}

                    {hint && !error && !success && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            {hint}
                        </p>
                    )}
                </div>
            </div>
        );
    }
);

Input.displayName = 'Input';
