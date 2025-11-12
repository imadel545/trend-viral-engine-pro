/**
 * PredictionForm Component - Advanced UI
 * 
 * Formulaire de prédiction ultra-moderne avec :
 * - Glassmorphism design
 * - Real-time validation
 * - Platform selector avec icons
 * - Animations fluides
 * - Loading states avancés
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, TrendingUp, Users } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { usePredictionStore } from '@/lib/stores';
import { PlatformInfo, Platform } from '@/lib/models';
import { cn, animations } from '@/lib/design-system';

// ============================================================================
// PLATFORM SELECTOR
// ============================================================================

interface PlatformSelectorProps {
    selected: string;
    onSelect: (platform: string) => void;
}

const PlatformSelector: React.FC<PlatformSelectorProps> = ({ selected, onSelect }) => {
    const platforms = PlatformInfo.getAll();

    return (
        <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Plateforme
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {platforms.map((platform) => (
                    <motion.button
                        key={platform.name}
                        type="button"
                        onClick={() => onSelect(platform.name)}
                        className={cn(
                            'relative p-4 rounded-xl border-2 transition-all',
                            'flex flex-col items-center justify-center gap-2',
                            'hover:scale-105 active:scale-95',
                            selected === platform.name
                                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        )}
                        whileHover={{ y: -4 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        {/* Selected Indicator */}
                        {selected === platform.name && (
                            <motion.div
                                layoutId="platform-selector"
                                className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10"
                                initial={false}
                                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                            />
                        )}

                        {/* Icon */}
                        <span className="text-3xl relative z-10">{platform.icon}</span>

                        {/* Name */}
                        <span className={cn(
                            'text-sm font-medium relative z-10',
                            selected === platform.name
                                ? 'text-indigo-700 dark:text-indigo-300'
                                : 'text-gray-600 dark:text-gray-400'
                        )}>
                            {platform.displayName}
                        </span>

                        {/* Engagement Badge */}
                        {selected === platform.name && (
                            <Badge variant="primary" className="text-xs relative z-10">
                                {(platform.avgEngagement * 100).toFixed(1)}% engagement
                            </Badge>
                        )}
                    </motion.button>
                ))}
            </div>
        </div>
    );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const PredictionForm: React.FC = () => {
    const [title, setTitle] = useState('');
    const [platform, setPlatform] = useState<string>(Platform.TikTok);
    const [followerCount, setFollowerCount] = useState('');

    const { predict, loading, error } = usePredictionStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const followers = parseInt(followerCount, 10);
        if (isNaN(followers) || followers < 0) {
            return;
        }

        await predict(title, platform, followers);
    };

    const isValid = title.trim().length > 0 && followerCount.length > 0;

    return (
        <Card variant="glass" padding="lg" className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit}>
                <CardHeader>
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <CardTitle className="flex items-center gap-3">
                            <Sparkles className="h-8 w-8 text-indigo-500" />
                            Prédire la Viralité
                        </CardTitle>
                        <CardDescription>
                            Analysez le potentiel viral de votre contenu avec notre IA avancée
                        </CardDescription>
                    </motion.div>
                </CardHeader>

                <CardContent>
                    <motion.div
                        variants={animations.stagger.container}
                        initial="initial"
                        animate="animate"
                        className="space-y-6"
                    >
                        {/* Title Input */}
                        <motion.div variants={animations.stagger.item}>
                            <Input
                                label="Titre du contenu"
                                placeholder="Ex: Top 10 des tendances IA en 2025"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                leftIcon={<TrendingUp className="h-5 w-5" />}
                                hint="Soyez descriptif et accrocheur pour de meilleurs résultats"
                                variant="glass"
                                inputSize="lg"
                            />
                        </motion.div>

                        {/* Platform Selector */}
                        <motion.div variants={animations.stagger.item}>
                            <PlatformSelector selected={platform} onSelect={setPlatform} />
                        </motion.div>

                        {/* Follower Count */}
                        <motion.div variants={animations.stagger.item}>
                            <Input
                                label="Nombre d'abonnés"
                                type="number"
                                placeholder="50000"
                                value={followerCount}
                                onChange={(e) => setFollowerCount(e.target.value)}
                                leftIcon={<Users className="h-5 w-5" />}
                                hint="Votre audience actuelle sur cette plateforme"
                                variant="glass"
                                inputSize="lg"
                            />
                        </motion.div>

                        {/* Error Display */}
                        <AnimatePresence>
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
                                >
                                    <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </CardContent>

                <CardFooter>
                    <Button
                        type="submit"
                        variant="primary"
                        size="lg"
                        fullWidth
                        loading={loading}
                        disabled={!isValid || loading}
                        rightIcon={<Sparkles className="h-5 w-5" />}
                    >
                        {loading ? 'Analyse en cours...' : 'Analyser le Potentiel'}
                    </Button>
                </CardFooter>
            </form>

            {/* Decorative Background */}
            <div className="absolute inset-0 -z-10 overflow-hidden rounded-xl">
                <motion.div
                    className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-to-br from-indigo-500/10 to-purple-500/10 blur-3xl"
                    animate={{
                        scale: [1, 1.1, 1],
                        rotate: [0, 90, 0],
                    }}
                    transition={{
                        duration: 20,
                        repeat: Infinity,
                        ease: 'linear',
                    }}
                />
            </div>
        </Card>
    );
};
