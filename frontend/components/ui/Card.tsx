/**
 * Card Component - Advanced UI
 * 
 * Carte avec glassmorphism, gradients, hover effects.
 * Support dark mode et animations Framer Motion.
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn, variants as designVariants, animations } from '@/lib/design-system';

// ============================================================================
// TYPES
// ============================================================================

export interface CardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: React.ReactNode;
    variant?: 'default' | 'glass' | 'gradient' | 'elevated';
    padding?: 'none' | 'sm' | 'md' | 'lg';
    hover?: boolean;
    clickable?: boolean;
    bordered?: boolean;
}

// ============================================================================
// CARD COMPONENT
// ============================================================================

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
    (
        {
            children,
            variant = 'default',
            padding = 'md',
            hover = true,
            clickable = false,
            bordered = true,
            className,
            ...props
        },
        ref
    ) => {
        return (
            <motion.div
                ref={ref}
                className={cn(
                    designVariants.card.base,
                    designVariants.card.variant[variant],
                    designVariants.card.padding[padding],
                    !bordered && 'border-0',
                    clickable && 'cursor-pointer',
                    className
                )}
                initial="initial"
                animate="animate"
                exit="exit"
                variants={hover ? animations.scaleIn : undefined}
                whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : undefined}
                {...props}
            >
                {children}
            </motion.div>
        );
    }
);

Card.displayName = 'Card';

// ============================================================================
// CARD HEADER
// ============================================================================

export interface CardHeaderProps {
    children: React.ReactNode;
    className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => {
    return (
        <div className={cn('mb-4', className)}>
            {children}
        </div>
    );
};

// ============================================================================
// CARD TITLE
// ============================================================================

export interface CardTitleProps {
    children: React.ReactNode;
    className?: string;
}

export const CardTitle: React.FC<CardTitleProps> = ({ children, className }) => {
    return (
        <h3 className={cn('text-2xl font-bold text-gray-900 dark:text-white', className)}>
            {children}
        </h3>
    );
};

// ============================================================================
// CARD DESCRIPTION
// ============================================================================

export interface CardDescriptionProps {
    children: React.ReactNode;
    className?: string;
}

export const CardDescription: React.FC<CardDescriptionProps> = ({ children, className }) => {
    return (
        <p className={cn('text-sm text-gray-600 dark:text-gray-400 mt-2', className)}>
            {children}
        </p>
    );
};

// ============================================================================
// CARD CONTENT
// ============================================================================

export interface CardContentProps {
    children: React.ReactNode;
    className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({ children, className }) => {
    return (
        <div className={cn('space-y-4', className)}>
            {children}
        </div>
    );
};

// ============================================================================
// CARD FOOTER
// ============================================================================

export interface CardFooterProps {
    children: React.ReactNode;
    className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => {
    return (
        <div className={cn('mt-6 flex items-center justify-between', className)}>
            {children}
        </div>
    );
};
