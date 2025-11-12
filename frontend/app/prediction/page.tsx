'use client';

import { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Target, TrendingUp, DollarSign, Users, Eye, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import { AreaChart, Area, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000/api/v1';

const platforms = [
    { id: 'tiktok', name: 'TikTok' },
    { id: 'instagram', name: 'Instagram' },
    { id: 'youtube', name: 'YouTube' },
    { id: 'reddit', name: 'Reddit' },
];

export default function PredictionPage() {
    const [title, setTitle] = useState('');
    const [platform, setPlatform] = useState('tiktok');
    const [followers, setFollowers] = useState(50000);
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState<any>(null);

    const predictVirality = async () => {
        if (!title.trim()) {
            toast.error('Veuillez entrer un titre');
            return;
        }

        setLoading(true);
        const loadingToast = toast.loading('Analyse ML en cours...');

        try {
            const response = await axios.post(`${API_BASE}/predict`, {
                title,
                platform,
                follower_count: followers
            });
            setPrediction(response.data);
            toast.success('✨ Prédiction générée avec succès !', { id: loadingToast });
        } catch (error: any) {
            console.error('Erreur prédiction:', error);
            toast.error(
                error.response?.data?.detail || 'Erreur lors de la prédiction',
                { id: loadingToast }
            );
        } finally {
            setLoading(false);
        }
    };

    const projectionData = prediction?.projection_7_days || [];
    const radarData = prediction ? [
        { metric: 'Engagement', value: prediction.engagement_rate * 100 },
        { metric: 'Portée', value: (prediction.predicted_views / 100000) * 100 },
        { metric: 'Viralité', value: prediction.viral_probability * 100 },
        { metric: 'ROI', value: Math.min((prediction.roi_percentage / 200) * 100, 100) },
        { metric: 'Qualité', value: 85 },
    ] : [];

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        Prédiction ML
                    </h1>
                    <p className="text-gray-400 mt-2">
                        Analysez le potentiel viral de votre contenu avec intelligence artificielle
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Input Form */}
                    <Card variant="glass" className="p-6">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <Target className="w-5 h-5 text-blue-400" />
                            Configuration
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-gray-300 mb-2 font-medium">Titre du contenu</label>
                                <Input
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="Ex: Top 10 AI Tools 2025"
                                    variant="glass"
                                />
                            </div>

                            <div>
                                <label className="block text-gray-300 mb-2 font-medium">Plateforme</label>
                                <select
                                    value={platform}
                                    onChange={(e) => setPlatform(e.target.value)}
                                    className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-3 text-white"
                                    title="Sélectionner une plateforme"
                                >
                                    {platforms.map((p) => (
                                        <option key={p.id} value={p.id}>
                                            {p.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-gray-300 mb-2 font-medium">
                                    Abonnés: {followers.toLocaleString()}
                                </label>
                                <input
                                    type="range"
                                    min="1000"
                                    max="1000000"
                                    step="1000"
                                    value={followers}
                                    onChange={(e) => setFollowers(Number(e.target.value))}
                                    className="w-full accent-blue-500"
                                    title="Nombre d'abonnés"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>1K</span>
                                    <span>1M</span>
                                </div>
                            </div>

                            <Button
                                onClick={predictVirality}
                                disabled={loading || !title.trim()}
                                className="w-full"
                            >
                                {loading ? 'Analyse en cours...' : 'Analyser le Potentiel'}
                            </Button>
                        </div>
                    </Card>

                    {/* Results */}
                    <div className="lg:col-span-2 space-y-6">
                        {prediction ? (
                            <>
                                {/* Key Metrics */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <Card variant="glass" className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-blue-500/20 rounded-lg">
                                                <Eye className="w-5 h-5 text-blue-400" />
                                            </div>
                                            <div>
                                                <p className="text-gray-400 text-xs">Vues</p>
                                                <p className="text-white font-bold text-lg">
                                                    {prediction.predicted_views?.toLocaleString() || '0'}
                                                </p>
                                            </div>
                                        </div>
                                    </Card>

                                    <Card variant="glass" className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-pink-500/20 rounded-lg">
                                                <Heart className="w-5 h-5 text-pink-400" />
                                            </div>
                                            <div>
                                                <p className="text-gray-400 text-xs">Likes</p>
                                                <p className="text-white font-bold text-lg">
                                                    {prediction.predicted_likes?.toLocaleString() || '0'}
                                                </p>
                                            </div>
                                        </div>
                                    </Card>

                                    <Card variant="glass" className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-green-500/20 rounded-lg">
                                                <DollarSign className="w-5 h-5 text-green-400" />
                                            </div>
                                            <div>
                                                <p className="text-gray-400 text-xs">Revenu</p>
                                                <p className="text-white font-bold text-lg">
                                                    {prediction.estimated_revenue?.toLocaleString('fr-FR', {
                                                        style: 'currency',
                                                        currency: 'EUR',
                                                        maximumFractionDigits: 0
                                                    }) || '0€'}
                                                </p>
                                            </div>
                                        </div>
                                    </Card>

                                    <Card variant="glass" className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-purple-500/20 rounded-lg">
                                                <TrendingUp className="w-5 h-5 text-purple-400" />
                                            </div>
                                            <div>
                                                <p className="text-gray-400 text-xs">Viral</p>
                                                <p className="text-white font-bold text-lg">
                                                    {((prediction.viral_probability || 0) * 100).toFixed(0)}%
                                                </p>
                                            </div>
                                        </div>
                                    </Card>
                                </div>

                                {/* Charts */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    {/* Projection 7 jours */}
                                    <Card variant="glass" className="p-6">
                                        <h3 className="text-lg font-bold text-white mb-4">Projection 7 jours</h3>
                                        <ResponsiveContainer width="100%" height={250}>
                                            <AreaChart data={projectionData}>
                                                <defs>
                                                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                                <XAxis dataKey="day" stroke="#9ca3af" />
                                                <YAxis stroke="#9ca3af" />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: '#1f2937',
                                                        border: '1px solid #374151',
                                                        borderRadius: '8px',
                                                        color: '#fff'
                                                    }}
                                                />
                                                <Area
                                                    type="monotone"
                                                    dataKey="views"
                                                    stroke="#3b82f6"
                                                    fillOpacity={1}
                                                    fill="url(#colorViews)"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </Card>

                                    {/* Radar Performance */}
                                    <Card variant="glass" className="p-6">
                                        <h3 className="text-lg font-bold text-white mb-4">Performance Globale</h3>
                                        <ResponsiveContainer width="100%" height={250}>
                                            <RadarChart data={radarData}>
                                                <PolarGrid stroke="#374151" />
                                                <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
                                                <PolarRadiusAxis stroke="#9ca3af" />
                                                <Radar
                                                    name="Performance"
                                                    dataKey="value"
                                                    stroke="#8b5cf6"
                                                    fill="#8b5cf6"
                                                    fillOpacity={0.3}
                                                />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </Card>
                                </div>

                                {/* Recommendations */}
                                {prediction.recommendations && (
                                    <Card variant="glass" className="p-6">
                                        <h3 className="text-lg font-bold text-white mb-4">Recommandations IA</h3>
                                        <div className="space-y-2">
                                            {prediction.recommendations.map((rec: string, i: number) => (
                                                <div key={i} className="flex items-start gap-3">
                                                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                                        <span className="text-purple-400 text-sm">{i + 1}</span>
                                                    </div>
                                                    <p className="text-gray-300">{rec}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>
                                )}
                            </>
                        ) : (
                            <Card variant="glass" className="p-12 lg:col-span-2">
                                <div className="text-center">
                                    <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Target className="w-8 h-8 text-blue-400" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">
                                        Prêt à prédire la viralité ?
                                    </h3>
                                    <p className="text-gray-400">
                                        Remplissez le formulaire pour obtenir une analyse complète
                                    </p>
                                </div>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
