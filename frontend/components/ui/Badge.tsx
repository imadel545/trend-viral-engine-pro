/**
 * Badge Component - Advanced UI
 * 
 * Badge moderne avec animations et variants.
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn, variants as designVariants } from '@/lib/design-system';

// ============================================================================
// TYPES
// ============================================================================

export interface BadgeProps {
    children: React.ReactNode;
    variant?: 'primary' | 'success' | 'warning' | 'danger' | 'viral';
    icon?: React.ReactNode;
    pulse?: boolean;
    className?: string;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const Badge: React.FC<BadgeProps> = ({
    children,
    variant = 'primary',
    icon,
    pulse = false,
    className,
}) => {
    return (
        <motion.span
            className={cn(
                designVariants.badge.base,
                designVariants.badge.variant[variant],
                pulse && 'animate-pulse',
                className
            )}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        >
            {icon && <span className="mr-1">{icon}</span>}
            {children}
        </motion.span>
    );
};
