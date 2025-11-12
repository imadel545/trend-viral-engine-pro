'use client';

import { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Video, FileText, Sparkles, Download, Loader } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000/api/v1';

const platforms = [
    { id: 'tiktok', name: 'TikTok', color: 'from-pink-500 to-purple-500' },
    { id: 'instagram', name: 'Instagram', color: 'from-purple-500 to-pink-500' },
    { id: 'youtube', name: 'YouTube', color: 'from-red-500 to-orange-500' },
    { id: 'reddit', name: 'Reddit', color: 'from-orange-500 to-red-500' },
];

export default function GenerationPage() {
    const [topic, setTopic] = useState('');
    const [platform, setPlatform] = useState('tiktok');
    const [duration, setDuration] = useState(60);
    const [script, setScript] = useState('');
    const [videoUrl, setVideoUrl] = useState('');
    const [loading, setLoading] = useState(false);

    const generateScript = async () => {
        if (!topic.trim()) {
            toast.error('Veuillez entrer un sujet');
            return;
        }

        setLoading(true);
        setScript('');
        const loadingToast = toast.loading('Génération du script avec Groq LLM...');

        try {
            const response = await axios.post(\`\${API_BASE}/generate/script\`, {
                topic,
                platform,
                duration
            });
            setScript(response.data.script);
            toast.success('🎬 Script généré avec succès !', { id: loadingToast });
        } catch (error: unknown) {
            console.error('Erreur génération script:', error);
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(
                err.response?.data?.detail || 'Erreur lors de la génération du script',
                { id: loadingToast }
            );
        } finally {
            setLoading(false);
        }
    };

    const generateVideo = async () => {
        if (!script) {
            toast.error('Veuillez générer un script d\\'abord');
            return;
        }

        setLoading(true);
        setVideoUrl('');
        const loadingToast = toast.loading('Génération de la vidéo MP4 avec MoviePy...');

        try {
            const response = await axios.post(\`\${API_BASE}/generate/video\`, {
                script,
                platform,
                style: 'modern'
            });

            const videoPath = response.data.video_path;
            const filename = videoPath.split('/').pop();
            const fullUrl = \`http://localhost:8000/outputs/\${filename}\`;

            setVideoUrl(fullUrl);
            toast.success('🎥 Vidéo générée avec succès !', { id: loadingToast });
        } catch (error: unknown) {
            console.error('Erreur génération vidéo:', error);
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(
                err.response?.data?.detail || 'Erreur lors de la génération de la vidéo',
                { id: loadingToast }
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        Génération de Contenu
                    </h1>
                    <p className="text-gray-400 mt-2">Créez du contenu viral automatiquement avec IA</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card variant="glass" className="p-6">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-purple-400" />
                            Configuration
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-gray-300 mb-2 font-medium">Sujet</label>
                                <Input
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder="Ex: Top 10 AI Tools 2025"
                                    variant="glass"
                                />
                            </div>

                            <div>
                                <label className="block text-gray-300 mb-3 font-medium">Plateforme</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {platforms.map((p) => (
                                        <motion.button
                                            key={p.id}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setPlatform(p.id)}
                                            className={\`p-4 rounded-lg border-2 transition-all \${platform === p.id ? \`border-purple-500 bg-gradient-to-r \${p.color} bg-opacity-10\` : 'border-gray-700 bg-gray-800/50'}\`}
                                        >
                                            <span className={\`font-medium \${platform === p.id ? \`bg-gradient-to-r \${p.color} bg-clip-text text-transparent\` : 'text-gray-400'}\`}>
                                                {p.name}
                                            </span>
                                        </motion.button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-gray-300 mb-2 font-medium">
                                    Durée: {duration}s
                                </label>
                                <input
                                    type="range"
                                    min="15"
                                    max="180"
                                    step="15"
                                    value={duration}
                                    onChange={(e) => setDuration(Number(e.target.value))}
                                    className="w-full accent-purple-500"
                                    title="Durée de la vidéo"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>15s</span>
                                    <span>180s</span>
                                </div>
                            </div>

                            <div className="pt-4 space-y-3">
                                <Button
                                    onClick={generateScript}
                                    disabled={loading || !topic.trim()}
                                    className="w-full"
                                >
                                    {loading ? (
                                        <>
                                            <Loader className="w-4 h-4 animate-spin" />
                                            Génération en cours...
                                        </>
                                    ) : (
                                        <>
                                            <FileText className="w-4 h-4" />
                                            Générer Script
                                        </>
                                    )}
                                </Button>

                                <Button
                                    onClick={generateVideo}
                                    disabled={loading || !script}
                                    variant="secondary"
                                    className="w-full"
                                >
                                    <Video className="w-4 h-4" />
                                    Générer Vidéo
                                </Button>
                            </div>
                        </div>
                    </Card>

                    <div className="space-y-6">
                        {script && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <Card variant="glass" className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                            <FileText className="w-5 h-5 text-green-400" />
                                            Script Généré
                                        </h3>
                                        <Button variant="outline" size="sm">
                                            <Download className="w-4 h-4" />
                                            Télécharger
                                        </Button>
                                    </div>
                                    <div className="bg-gray-900/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                                        <pre className="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed">
                                            {script}
                                        </pre>
                                    </div>
                                </Card>
                            </motion.div>
                        )}

                        {videoUrl && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <Card variant="glass" className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                            <Video className="w-5 h-5 text-purple-400" />
                                            Vidéo Générée
                                        </h3>
                                        <Button variant="outline" size="sm">
                                            <Download className="w-4 h-4" />
                                            Télécharger MP4
                                        </Button>
                                    </div>
                                    <div className="bg-gray-900 rounded-lg overflow-hidden">
                                        <video controls className="w-full" src={videoUrl}>
                                            Votre navigateur ne supporte pas la lecture vidéo.
                                        </video>
                                    </div>
                                    <div className="mt-4 text-sm text-gray-400">
                                        <p>Fichier: {videoUrl}</p>
                                    </div>
                                </Card>
                            </motion.div>
                        )}

                        {!script && !videoUrl && (
                            <Card variant="glass" className="p-12">
                                <div className="text-center">
                                    <div className="w-16 h-16 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Sparkles className="w-8 h-8 text-purple-400" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">
                                        Prêt à créer du contenu viral ?
                                    </h3>
                                    <p className="text-gray-400">
                                        Remplissez le formulaire et générez votre contenu automatiquement
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
