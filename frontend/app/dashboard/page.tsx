'use client';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { TrendingUp, Target, Video, Database, Activity, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const stats = [
    {
        name: 'Tendances Collectées',
        value: '1,247',
        change: '+12.5%',
        icon: TrendingUp,
        color: 'from-purple-500 to-pink-500',
        bgColor: 'bg-purple-500/10'
    },
    {
        name: 'Prédictions Réalisées',
        value: '843',
        change: '+8.2%',
        icon: Target,
        color: 'from-blue-500 to-cyan-500',
        bgColor: 'bg-blue-500/10'
    },
    {
        name: 'Vidéos Générées',
        value: '127',
        change: '+23.1%',
        icon: Video,
        color: 'from-green-500 to-emerald-500',
        bgColor: 'bg-green-500/10'
    },
    {
        name: 'Précision Modèle',
        value: '87.3%',
        change: '+2.1%',
        icon: Activity,
        color: 'from-orange-500 to-red-500',
        bgColor: 'bg-orange-500/10'
    },
];

const viralityData = [
    { date: '01/11', tiktok: 4200, instagram: 3100, youtube: 2400, reddit: 1800 },
    { date: '02/11', tiktok: 5100, instagram: 3800, youtube: 2900, reddit: 2200 },
    { date: '03/11', tiktok: 4800, instagram: 4200, youtube: 3200, reddit: 2400 },
    { date: '04/11', tiktok: 6200, instagram: 4800, youtube: 3600, reddit: 2800 },
    { date: '05/11', tiktok: 7100, instagram: 5200, youtube: 4100, reddit: 3200 },
    { date: '06/11', tiktok: 6800, instagram: 5600, youtube: 4400, reddit: 3400 },
    { date: '07/11', tiktok: 8200, instagram: 6100, youtube: 4800, reddit: 3800 },
];

const platformDistribution = [
    { name: 'TikTok', value: 42, color: '#8b5cf6' },
    { name: 'Instagram', value: 28, color: '#ec4899' },
    { name: 'YouTube', value: 18, color: '#3b82f6' },
    { name: 'Reddit', value: 12, color: '#10b981' },
];

const recentPredictions = [
    { id: 1, title: 'Top 10 AI Tools 2025', platform: 'TikTok', score: 0.89, status: 'Viral' },
    { id: 2, title: 'ChatGPT Secret Tips', platform: 'Instagram', score: 0.76, status: 'High' },
    { id: 3, title: 'Coding in 2025', platform: 'YouTube', score: 0.92, status: 'Viral' },
    { id: 4, title: 'Tech News Today', platform: 'Reddit', score: 0.65, status: 'Medium' },
    { id: 5, title: 'AI Art Tutorial', platform: 'TikTok', score: 0.82, status: 'High' },
];

export default function DashboardPage() {
    return (
        <DashboardLayout>
            <div className="space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
                            Dashboard Principal
                        </h1>
                        <p className="text-gray-400 mt-2">Vue d'ensemble de votre moteur viral IA</p>
                    </div>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white font-medium shadow-lg shadow-purple-500/50"
                    >
                        <Zap className="w-5 h-5" />
                        Nouvelle Analyse
                    </motion.button>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {stats.map((stat, index) => {
                        const Icon = stat.icon;
                        return (
                            <motion.div
                                key={stat.name}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <Card variant="glass" className="p-6">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <p className="text-gray-400 text-sm font-medium">{stat.name}</p>
                                            <h3 className="text-3xl font-bold text-white mt-2">{stat.value}</h3>
                                            <p className="text-green-400 text-sm mt-2 font-medium">{stat.change}</p>
                                        </div>
                                        <div className={`${stat.bgColor} p-3 rounded-lg`}>
                                            <Icon className={`w-6 h-6 bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`} />
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Virality Trends */}
                    <Card variant="glass" className="p-6">
                        <h3 className="text-xl font-bold text-white mb-6">Tendances de Viralité</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={viralityData}>
                                <defs>
                                    <linearGradient id="colorTiktok" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorInstagram" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ec4899" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="date" stroke="#9ca3af" />
                                <YAxis stroke="#9ca3af" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1f2937',
                                        border: '1px solid #374151',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                />
                                <Area type="monotone" dataKey="tiktok" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorTiktok)" />
                                <Area type="monotone" dataKey="instagram" stroke="#ec4899" fillOpacity={1} fill="url(#colorInstagram)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </Card>

                    {/* Platform Distribution */}
                    <Card variant="glass" className="p-6">
                        <h3 className="text-xl font-bold text-white mb-6">Distribution par Plateforme</h3>
                        <div className="flex items-center justify-between">
                            <ResponsiveContainer width="60%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={platformDistribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {platformDistribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="space-y-3">
                                {platformDistribution.map((item) => (
                                    <div key={item.name} className="flex items-center gap-3">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                        <span className="text-gray-300 text-sm">{item.name}</span>
                                        <span className="text-white font-bold ml-auto">{item.value}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Recent Predictions */}
                <Card variant="glass" className="p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Prédictions Récentes</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-700">
                                    <th className="text-left text-gray-400 font-medium pb-3">Titre</th>
                                    <th className="text-left text-gray-400 font-medium pb-3">Plateforme</th>
                                    <th className="text-left text-gray-400 font-medium pb-3">Score</th>
                                    <th className="text-left text-gray-400 font-medium pb-3">Statut</th>
                                    <th className="text-right text-gray-400 font-medium pb-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentPredictions.map((pred) => (
                                    <motion.tr
                                        key={pred.id}
                                        whileHover={{ backgroundColor: 'rgba(139, 92, 246, 0.05)' }}
                                        className="border-b border-gray-800"
                                    >
                                        <td className="py-4 text-white font-medium">{pred.title}</td>
                                        <td className="py-4">
                                            <span className="px-3 py-1 bg-gray-800 text-gray-300 rounded-full text-sm">
                                                {pred.platform}
                                            </span>
                                        </td>
                                        <td className="py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${pred.score * 100}%` }}
                                                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                                                    />
                                                </div>
                                                <span className="text-white font-bold">{(pred.score * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                        <td className="py-4">
                                            <span className={`
                        px-3 py-1 rounded-full text-sm font-medium
                        ${pred.status === 'Viral' ? 'bg-green-500/20 text-green-400' :
                                                    pred.status === 'High' ? 'bg-yellow-500/20 text-yellow-400' :
                                                        'bg-gray-500/20 text-gray-400'}
                      `}>
                                                {pred.status}
                                            </span>
                                        </td>
                                        <td className="py-4 text-right">
                                            <button className="text-purple-400 hover:text-purple-300 font-medium">
                                                Voir détails →
                                            </button>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            </div>
        </DashboardLayout>
    );
}
