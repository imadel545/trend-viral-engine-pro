'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    TrendingUp,
    Target,
    Video,
    Activity,
    Database,
    Settings,
    Zap,
    Link2
} from 'lucide-react';
import { motion } from 'framer-motion';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Analyser Post', href: '/analyze', icon: Link2 },
    { name: 'Tendances Virales', href: '/trends', icon: TrendingUp },
    { name: 'Prédictions ML', href: '/prediction', icon: Target },
    { name: 'Génération Contenu', href: '/generation', icon: Video },
    { name: 'Collecte Données', href: '/ingestion', icon: Database },
    { name: 'Monitoring', href: '/monitoring', icon: Activity },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="fixed left-0 top-0 h-screen w-64 bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 border-r border-gray-700/50 backdrop-blur-xl">
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-700/50">
                <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 blur-lg opacity-50" />
                    <Zap className="relative w-8 h-8 text-white" />
                </div>
                <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        Viral Engine
                    </h1>
                    <p className="text-xs text-gray-400">Pro Edition</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="px-3 py-6 space-y-1">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link key={item.name} href={item.href}>
                            <motion.div
                                whileHover={{ x: 4 }}
                                whileTap={{ scale: 0.98 }}
                                className={`
                  relative flex items-center gap-3 px-4 py-3 rounded-lg
                  transition-all duration-200 group
                  ${isActive
                                        ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white shadow-lg shadow-purple-500/20'
                                        : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                                    }
                `}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-purple-500 to-pink-500 rounded-r"
                                        transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                                    />
                                )}

                                <Icon className={`w-5 h-5 ${isActive ? 'text-purple-400' : ''}`} />
                                <span className="font-medium">{item.name}</span>

                                {isActive && (
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="ml-auto w-2 h-2 rounded-full bg-green-400"
                                    />
                                )}
                            </motion.div>
                        </Link>
                    );
                })}
            </nav>

            {/* Stats Footer */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700/50">
                <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 backdrop-blur">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-400">Statut API</span>
                        <span className="flex items-center gap-1 text-xs text-green-400">
                            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                            En ligne
                        </span>
                    </div>
                    <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Modèle ML</span>
                            <span className="text-white font-medium">LightGBM</span>
                        </div>
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Précision</span>
                            <span className="text-purple-400 font-medium">87.3%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
