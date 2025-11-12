/**
 * PredictionResults Component - Advanced UI
 * 
 * Affichage des résultats avec :
 * - Charts interactifs (Recharts)
 * - Métriques animées
 * - Glassmorphism cards
 * - Recommendations intelligentes
 * - Copy to clipboard
 * 
 * Author: Trend & Viral Engine Pro
 * Date: 11 novembre 2025
 */

'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Eye,
    Heart,
    TrendingUp,
    DollarSign,
    Clock,
    Lightbulb,
    Copy,
    Check,
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { usePredictionStore } from '@/lib/stores';
import { Prediction } from '@/lib/models';
import { animations } from '@/lib/design-system';
import { useCopyToClipboard } from '@/hooks';

// ============================================================================
// METRIC CARD
// ============================================================================

interface MetricCardProps {
    icon: React.ReactNode;
    label: string;
    value: string | number;
    subtitle?: string;
    trend?: number;
    color?: string;
    delay?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({
    icon,
    label,
    value,
    subtitle,
    trend,
    color = 'indigo',
    delay = 0,
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
        >
            <Card variant="glass" padding="md" className="h-full">
                <div className="flex items-start justify-between">
                    <div className={`p-3 rounded-lg bg-${color}-100 dark:bg-${color}-900/20`}>
                        {icon}
                    </div>

                    {trend !== undefined && (
                        <Badge variant={trend > 0 ? 'success' : 'danger'} className="text-xs">
                            {trend > 0 ? '+' : ''}{trend}%
                        </Badge>
                    )}
                </div>

                <div className="mt-4 space-y-1">
                    <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">
                        {value}
                    </p>
                    {subtitle && (
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                            {subtitle}
                        </p>
                    )}
                </div>
            </Card>
        </motion.div>
    );
};

// ============================================================================
// VIEWS PROJECTION CHART
// ============================================================================

interface ViewsProjectionProps {
    prediction: Prediction;
}

const ViewsProjection: React.FC<ViewsProjectionProps> = ({ prediction }) => {
    // Generate stable projection data (memoized)
    const data = React.useMemo(() => {
        return Array.from({ length: 7 }, (_, i) => {
            const dayFactor = i === 0 ? 0.3 : i === 1 ? 0.6 : 1;
            // Use seed based on prediction ID for stable randomness
            const seed = prediction.id.charCodeAt(0) + i;
            const variance = 0.9 + ((seed % 10) / 50); // 0.9 to 1.1
            return {
                day: `J${i + 1}`,
                views: Math.round(prediction.views * dayFactor * variance),
                likes: Math.round(prediction.likes * dayFactor * variance),
            };
        });
    }, [prediction.id, prediction.views, prediction.likes]);

    return (
        <Card variant="glass" padding="lg">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-indigo-500" />
                    Projection sur 7 jours
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366F1" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="likesGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#EC4899" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#EC4899" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis dataKey="day" stroke="#9CA3AF" />
                        <YAxis stroke="#9CA3AF" />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'rgba(17, 24, 39, 0.8)',
                                border: 'none',
                                borderRadius: '8px',
                                color: '#fff',
                            }}
                        />
                        <Area
                            type="monotone"
                            dataKey="views"
                            stroke="#6366F1"
                            fillOpacity={1}
                            fill="url(#viewsGradient)"
                        />
                        <Area
                            type="monotone"
                            dataKey="likes"
                            stroke="#EC4899"
                            fillOpacity={1}
                            fill="url(#likesGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

// ============================================================================
// ENGAGEMENT RADAR
// ============================================================================

interface EngagementRadarProps {
    prediction: Prediction;
}

const EngagementRadar: React.FC<EngagementRadarProps> = ({ prediction }) => {
    const data = [
        { metric: 'Vues', value: Math.min(100, (prediction.views / 1000000) * 100) },
        { metric: 'Likes', value: Math.min(100, (prediction.likes / 100000) * 100) },
        { metric: 'Engagement', value: prediction.viralProbability * 100 },
        { metric: 'ROI', value: Math.min(100, prediction.roi / 1000) },
        { metric: 'Viralité', value: prediction.viralProbability * 100 },
    ];

    return (
        <Card variant="glass" padding="lg">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-500" />
                    Analyse Multi-Métriques
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={data}>
                        <PolarGrid stroke="#374151" />
                        <PolarAngleAxis dataKey="metric" stroke="#9CA3AF" />
                        <PolarRadiusAxis stroke="#9CA3AF" />
                        <Radar
                            name="Performance"
                            dataKey="value"
                            stroke="#8B5CF6"
                            fill="#8B5CF6"
                            fillOpacity={0.6}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

// ============================================================================
// RECOMMENDATIONS
// ============================================================================

interface RecommendationsProps {
    prediction: Prediction;
}

const Recommendations: React.FC<RecommendationsProps> = ({ prediction }) => {
    const [copied, copy] = useCopyToClipboard();

    const handleCopy = () => {
        const text = prediction.recommendations.join('\n');
        copy(text);
    };

    return (
        <Card variant="gradient" padding="lg">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Lightbulb className="h-5 w-5 text-yellow-500" />
                        Recommandations IA
                    </CardTitle>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCopy}
                        leftIcon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    >
                        {copied ? 'Copié !' : 'Copier'}
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <motion.ul
                    variants={animations.stagger.container}
                    initial="initial"
                    animate="animate"
                    className="space-y-3"
                >
                    {prediction.recommendations.map((rec, index) => (
                        <motion.li
                            key={index}
                            variants={animations.stagger.item}
                            className="flex items-start gap-3 p-3 rounded-lg bg-white/50 dark:bg-gray-800/50"
                        >
                            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm font-bold">
                                {index + 1}
                            </span>
                            <p className="text-sm text-gray-700 dark:text-gray-300">{rec}</p>
                        </motion.li>
                    ))}
                </motion.ul>
            </CardContent>
        </Card>
    );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const PredictionResults: React.FC = () => {
    const { currentPrediction } = usePredictionStore();

    if (!currentPrediction) {
        return null;
    }

    const prediction = currentPrediction;

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key={prediction.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
            >
                {/* Hero Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard
                        icon={<Eye className="h-6 w-6 text-indigo-500" />}
                        label="Vues Prédites"
                        value={prediction.getFormattedViews()}
                        subtitle={`Engagement: ${(prediction.viralProbability * 100).toFixed(0)}%`}
                        color="indigo"
                        delay={0}
                    />
                    <MetricCard
                        icon={<Heart className="h-6 w-6 text-pink-500" />}
                        label="Likes Estimés"
                        value={new Intl.NumberFormat('fr-FR').format(prediction.likes)}
                        color="pink"
                        delay={0.1}
                    />
                    <MetricCard
                        icon={<DollarSign className="h-6 w-6 text-green-500" />}
                        label="Revenu Estimé"
                        value={prediction.getFormattedRevenue()}
                        trend={prediction.roi > 100 ? Math.round(prediction.roi / 10) : undefined}
                        color="green"
                        delay={0.2}
                    />
                    <MetricCard
                        icon={<Clock className="h-6 w-6 text-orange-500" />}
                        label="Meilleur Moment"
                        value={prediction.getBestPostingDateTime().split(' à ')[1]}
                        subtitle={prediction.getBestPostingDateTime().split(' à ')[0]}
                        color="orange"
                        delay={0.3}
                    />
                </div>

                {/* Viral Badge */}
                {prediction.isViralContent() && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                        className="flex justify-center"
                    >
                        <Badge variant="viral" className="text-lg px-6 py-2">
                            🔥 Contenu à Potentiel VIRAL !
                        </Badge>
                    </motion.div>
                )}

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ViewsProjection prediction={prediction} />
                    <EngagementRadar prediction={prediction} />
                </div>

                {/* Recommendations */}
                <Recommendations prediction={prediction} />
            </motion.div>
        </AnimatePresence>
    );
};
