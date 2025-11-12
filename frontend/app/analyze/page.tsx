'use client';

import { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Link2, TrendingUp, Eye, Heart, MessageCircle, Share2, Sparkles, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

// Platform icons and colors
const platformConfig: Record<string, { name: string; color: string; example: string }> = {
    instagram: {
        name: 'Instagram',
        color: 'from-purple-500 to-pink-500',
        example: 'https://www.instagram.com/p/ABC123/'
    },
    tiktok: {
        name: 'TikTok',
        color: 'from-pink-500 to-cyan-500',
        example: 'https://www.tiktok.com/@user/video/1234567890'
    },
    facebook: {
        name: 'Facebook',
        color: 'from-blue-500 to-blue-700',
        example: 'https://www.facebook.com/user/posts/123456'
    },
    twitter: {
        name: 'Twitter/X',
        color: 'from-gray-700 to-gray-900',
        example: 'https://twitter.com/user/status/1234567890'
    },
    reddit: {
        name: 'Reddit',
        color: 'from-orange-500 to-red-500',
        example: 'https://www.reddit.com/r/viral/comments/abc123/'
    },
    youtube: {
        name: 'YouTube',
        color: 'from-red-500 to-red-700',
        example: 'https://www.youtube.com/watch?v=ABC123'
    }
};

export default function AnalyzePostPage() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<any>(null);

    const analyzePost = async () => {
        if (!url.trim()) {
            setError('Veuillez entrer une URL');
            return;
        }

        setLoading(true);
        setError('');
        setResult(null);

        try {
            const response = await axios.post(`${API_BASE}/analyze-post`, {
                url: url.trim(),
                extract_content: true
            });
            setResult(response.data);
        } catch (err: any) {
            console.error('Erreur analyse:', err);
            setError(err.response?.data?.detail || 'Erreur lors de l\'analyse du post');
        } finally {
            setLoading(false);
        }
    };

    const clearResults = () => {
        setResult(null);
        setUrl('');
        setError('');
    };

    const getClassificationColor = (classification: string) => {
        switch (classification) {
            case 'Viral': return 'text-green-400 bg-green-500/10 border-green-500/50';
            case 'High Performance': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/50';
            case 'Good Performance': return 'text-blue-400 bg-blue-500/10 border-blue-500/50';
            default: return 'text-gray-400 bg-gray-500/10 border-gray-500/50';
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                        Analyser un Post
                    </h1>
                    <p className="text-gray-400 mt-2">
                        Collez l&apos;URL de votre post Instagram, TikTok, Facebook, etc. pour une analyse complète
                    </p>
                </div>

                {/* Input Section */}
                <Card variant="glass" className="p-6">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                        <Link2 className="w-5 h-5 text-cyan-400" />
                        URL du Post
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <Input
                                value={url}
                                onChange={(e) => {
                                    setUrl(e.target.value);
                                    setError('');
                                }}
                                placeholder="https://www.instagram.com/p/ABC123/ ou https://www.tiktok.com/@user/video/123"
                                variant="glass"
                                disabled={loading}
                            />
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="mt-2 flex items-center gap-2 text-red-400 text-sm"
                                >
                                    <AlertCircle className="w-4 h-4" />
                                    {error}
                                </motion.div>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <Button
                                onClick={analyzePost}
                                disabled={loading || !url.trim()}
                                variant="primary"
                                className="flex-1"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                        Analyse en cours...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="w-4 h-4 mr-2" />
                                        Analyser le Post
                                    </>
                                )}
                            </Button>
                            {result && (
                                <Button onClick={clearResults} variant="ghost">
                                    Nouveau
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Platform Examples */}
                    <div className="mt-6 pt-6 border-t border-gray-700/50">
                        <p className="text-gray-400 text-sm mb-3">Plateformes supportées:</p>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {Object.entries(platformConfig).map(([key, config]) => (
                                <div
                                    key={key}
                                    className="text-xs text-gray-500 bg-gray-800/30 px-3 py-2 rounded-lg"
                                >
                                    <span className={`font-medium bg-gradient-to-r ${config.color} bg-clip-text text-transparent`}>
                                        {config.name}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </Card>

                {/* Results */}
                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Platform Badge */}
                        <Card variant="glass" className="p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-gray-400 text-sm">Plateforme détectée</p>
                                    <p className={`text-2xl font-bold bg-gradient-to-r ${platformConfig[result.platform]?.color || 'from-gray-400 to-gray-600'} bg-clip-text text-transparent`}>
                                        {platformConfig[result.platform]?.name || result.platform}
                                    </p>
                                </div>
                                <div className={`px-4 py-2 rounded-lg border ${getClassificationColor(result.analysis.classification)}`}>
                                    <p className="text-sm font-medium">{result.analysis.classification}</p>
                                </div>
                            </div>
                        </Card>

                        {/* Performance Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card variant="glass" className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/10 rounded-lg">
                                        <Eye className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-xs">Vues</p>
                                        <p className="text-white text-lg font-bold">
                                            {result.analysis.performance.views.toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </Card>

                            <Card variant="glass" className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-pink-500/10 rounded-lg">
                                        <Heart className="w-5 h-5 text-pink-400" />
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-xs">Likes</p>
                                        <p className="text-white text-lg font-bold">
                                            {result.analysis.performance.likes.toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </Card>

                            <Card variant="glass" className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-500/10 rounded-lg">
                                        <MessageCircle className="w-5 h-5 text-green-400" />
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-xs">Commentaires</p>
                                        <p className="text-white text-lg font-bold">
                                            {result.analysis.performance.comments.toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </Card>

                            <Card variant="glass" className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-purple-500/10 rounded-lg">
                                        <Share2 className="w-5 h-5 text-purple-400" />
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-xs">Partages</p>
                                        <p className="text-white text-lg font-bold">
                                            {result.analysis.performance.shares.toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </div>

                        {/* Viral Score */}
                        <Card variant="glass" className="p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-cyan-400" />
                                Score Viral & Engagement
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-400">Score Viral</span>
                                        <span className="text-white font-bold">{(result.analysis.viral_score * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-800 rounded-full h-3">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${result.analysis.viral_score * 100}%` }}
                                            transition={{ duration: 1, ease: "easeOut" }}
                                            className={`h-full rounded-full ${result.analysis.viral_score > 0.7 ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
                                                    result.analysis.viral_score > 0.5 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                                                        'bg-gradient-to-r from-blue-500 to-cyan-500'
                                                }`}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-400">Taux d'Engagement</span>
                                        <span className="text-white font-bold">{(result.analysis.engagement_rate * 100).toFixed(2)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-800 rounded-full h-3">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.min(result.analysis.engagement_rate * 100 * 20, 100)}%` }}
                                            transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
                                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full"
                                        />
                                    </div>
                                </div>
                            </div>
                        </Card>

                        {/* Success Factors */}
                        {result.analysis.success_factors && result.analysis.success_factors.length > 0 && (
                            <Card variant="glass" className="p-6">
                                <h3 className="text-lg font-bold text-white mb-4">✨ Facteurs de Succès</h3>
                                <div className="space-y-2">
                                    {result.analysis.success_factors.map((factor: string, index: number) => (
                                        <motion.div
                                            key={index}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            className="flex items-start gap-3 text-green-400"
                                        >
                                            <div className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2" />
                                            <p>{factor}</p>
                                        </motion.div>
                                    ))}
                                </div>
                            </Card>
                        )}

                        {/* Recommendations */}
                        {result.analysis.recommendations && result.analysis.recommendations.length > 0 && (
                            <Card variant="glass" className="p-6">
                                <h3 className="text-lg font-bold text-white mb-4">💡 Recommandations</h3>
                                <div className="space-y-3">
                                    {result.analysis.recommendations.map((rec: string, index: number) => (
                                        <motion.div
                                            key={index}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            className="flex items-start gap-3 text-yellow-400"
                                        >
                                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-yellow-500/10 border border-yellow-500/50 flex items-center justify-center text-xs font-bold">
                                                {index + 1}
                                            </div>
                                            <p>{rec}</p>
                                        </motion.div>
                                    ))}
                                </div>
                            </Card>
                        )}

                        {/* Post Metadata */}
                        <Card variant="glass" className="p-6">
                            <h3 className="text-lg font-bold text-white mb-4">📊 Métadonnées du Post</h3>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-gray-400">Auteur</p>
                                    <p className="text-white font-medium">{result.metadata.author}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Type de média</p>
                                    <p className="text-white font-medium capitalize">{result.metadata.media_type}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Posté le</p>
                                    <p className="text-white font-medium">
                                        {new Date(result.metadata.posted_at).toLocaleDateString('fr-FR')}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Hashtags</p>
                                    <p className="text-white font-medium">
                                        {result.metadata.hashtags?.length || 0} hashtags
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                )}
            </div>
        </DashboardLayout>
    );
}
