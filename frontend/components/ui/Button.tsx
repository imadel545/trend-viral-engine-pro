/**
 * Button Component - Advanced UI
 * 
 * Composant bouton ultra-moderne avec :
 * - Variants multiples (primary, secondary, ghost, etc.)
 * - Animations Framer Motion
 * - Loading states avec spinner
 * - Icons support
 * - Ripple effect
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn, variants as designVariants } from '@/lib/design-system';

// ============================================================================
// TYPES
// ============================================================================

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
    children: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    loading?: boolean;
    disabled?: boolean;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
    fullWidth?: boolean;
    ripple?: boolean;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            children,
            variant = 'primary',
            size = 'md',
            loading = false,
            disabled = false,
            leftIcon,
            rightIcon,
            fullWidth = false,
            ripple = true,
            className,
            ...props
        },
        ref
    ) => {
        const [ripples, setRipples] = React.useState<Array<{ x: number; y: number; id: number }>>([]);

        const handleRipple = (event: React.MouseEvent<HTMLButtonElement>) => {
            if (!ripple || disabled || loading) return;

            const button = event.currentTarget;
            const rect = button.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            const newRipple = { x, y, id: Date.now() };
            setRipples((prev) => [...prev, newRipple]);

            // Remove ripple after animation
            setTimeout(() => {
                setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
            }, 600);
        };

        return (
            <motion.button
                ref={ref}
                className={cn(
                    designVariants.button.base,
                    designVariants.button.variant[variant],
                    designVariants.button.size[size],
                    fullWidth && 'w-full',
                    'relative overflow-hidden',
                    className
                )}
                disabled={disabled || loading}
                onClick={handleRipple}
                whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
                whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
                transition={{ duration: 0.2 }}
                {...props}
            >
                {/* Ripple Effect */}
                {ripples.map((ripple) => (
                    <motion.span
                        key={ripple.id}
                        className="absolute rounded-full bg-white/30"
                        initial={{ width: 0, height: 0, x: ripple.x, y: ripple.y }}
                        animate={{ width: 300, height: 300, opacity: 0 }}
                        transition={{ duration: 0.6 }}
                        style={{
                            transform: 'translate(-50%, -50%)',
                        }}
                    />
                ))}

                {/* Content */}
                <span className="relative flex items-center justify-center gap-2">
                    {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                    {!loading && leftIcon && <span>{leftIcon}</span>}
                    {children}
                    {!loading && rightIcon && <span>{rightIcon}</span>}
                </span>
            </motion.button>
        );
    }
);

Button.displayName = 'Button';
