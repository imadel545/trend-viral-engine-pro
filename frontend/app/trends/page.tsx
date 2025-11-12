'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { TrendingUp, RefreshCw, Play, Download, Filter } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000/api/v1';

interface Trend {
    title: string;
    platform: string;
    viral_score: number;
    collected_at: string;
    metadata?: any;
}

export default function TrendsPage() {
    const [trends, setTrends] = useState<Trend[]>([]);
    const [loading, setLoading] = useState(false);
    const [collecting, setCollecting] = useState(false);
    const [topK, setTopK] = useState(20);

    const fetchTopTrends = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_BASE}/trends/topK?k=${topK}`);
            setTrends(response.data.trends || []);
            toast.success(`✅ ${response.data.trends.length} tendances chargées`);
        } catch (error: unknown) {
            console.error('Erreur fetch trends:', error);
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Erreur lors du chargement');
        } finally {
            setLoading(false);
        }
    };

    const startCollection = async () => {
        setCollecting(true);
        const loadingToast = toast.loading('Collecte en cours (Google Trends + Reddit)...');

        try {
            await axios.post(`${API_BASE}/trends/collect`, {
                sources: ['google_trends', 'reddit']
            });
            toast.success('🎉 Collecte terminée avec succès !', { id: loadingToast });
            // Attendre 2 secondes puis recharger
            setTimeout(() => {
                fetchTopTrends();
                setCollecting(false);
            }, 2000);
        } catch (error: unknown) {
            console.error('Erreur collection:', error);
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Erreur lors de la collecte', { id: loadingToast });
            setCollecting(false);
        }
    };

    useEffect(() => {
        fetchTopTrends();
    }, [topK]);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                            Tendances Virales
                        </h1>
                        <p className="text-gray-400 mt-2">Collecte et analyse en temps réel</p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            onClick={fetchTopTrends}
                            disabled={loading}
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            Rafraîchir
                        </Button>
                        <Button
                            onClick={startCollection}
                            disabled={collecting}
                        >
                            <Play className="w-4 h-4" />
                            {collecting ? 'Collecte en cours...' : 'Lancer Collecte'}
                        </Button>
                    </div>
                </div>

                {/* Filters */}
                <Card variant="glass" className="p-4">
                    <div className="flex items-center gap-4">
                        <Filter className="w-5 h-5 text-gray-400" />
                        <div className="flex items-center gap-2">
                            <label className="text-gray-300">Top</label>
                            <select
                                value={topK}
                                onChange={(e) => setTopK(Number(e.target.value))}
                                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                            >
                                <option value={10}>10</option>
                                <option value={20}>20</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                            </select>
                            <span className="text-gray-400">tendances</span>
                        </div>
                    </div>
                </Card>

                {/* Trends Table */}
                <Card variant="glass" className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xl font-bold text-white">
                            Top {topK} Tendances ({trends.length})
                        </h3>
                        <Button variant="secondary" size="sm">
                            <Download className="w-4 h-4" />
                            Exporter CSV
                        </Button>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-20">
                            <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-700">
                                        <th className="text-left text-gray-400 font-medium pb-3">#</th>
                                        <th className="text-left text-gray-400 font-medium pb-3">Titre</th>
                                        <th className="text-left text-gray-400 font-medium pb-3">Plateforme</th>
                                        <th className="text-left text-gray-400 font-medium pb-3">Score Viral</th>
                                        <th className="text-left text-gray-400 font-medium pb-3">Collecté</th>
                                        <th className="text-right text-gray-400 font-medium pb-3">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {trends.map((trend, index) => (
                                        <motion.tr
                                            key={index}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.03 }}
                                            whileHover={{ backgroundColor: 'rgba(139, 92, 246, 0.05)' }}
                                            className="border-b border-gray-800"
                                        >
                                            <td className="py-4 text-gray-400">#{index + 1}</td>
                                            <td className="py-4 text-white font-medium max-w-md truncate">
                                                {trend.title}
                                            </td>
                                            <td className="py-4">
                                                <span className="px-3 py-1 bg-gray-800 text-gray-300 rounded-full text-sm">
                                                    {trend.platform}
                                                </span>
                                            </td>
                                            <td className="py-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${trend.viral_score * 100}%` }}
                                                            className={`h-full ${trend.viral_score > 0.7 ? 'bg-green-500' :
                                                                trend.viral_score > 0.5 ? 'bg-yellow-500' :
                                                                    'bg-gray-500'
                                                                }`}
                                                        />
                                                    </div>
                                                    <span className="text-white font-bold">
                                                        {(trend.viral_score * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-4 text-gray-400 text-sm">
                                                {new Date(trend.collected_at).toLocaleString('fr-FR')}
                                            </td>
                                            <td className="py-4 text-right">
                                                <button className="text-purple-400 hover:text-purple-300 font-medium text-sm">
                                                    Analyser →
                                                </button>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </Card>
            </div>
        </DashboardLayout>
    );
}
