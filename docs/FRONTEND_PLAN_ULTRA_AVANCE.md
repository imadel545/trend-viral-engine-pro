# 🎨 PLAN FRONTEND ULTRA-AVANCÉ - Architecture Complète

**Date**: 11 Novembre 2025  
**Statut actuel**: Backend ✅ COMPLET | Frontend ❌ PAS COMMENCÉ

---

## 📊 SITUATION ACTUELLE (Où on en est)

### ✅ CE QUI EST FAIT (Backend)

```
Backend (Python/FastAPI) ✅ 100% COMPLET
├── Prédictions exactes (vues/likes/€)
├── Multi-plateforme (TikTok/Instagram/YouTube/Reddit)
├── ROI automatique
├── Comparaison cross-platform
└── API REST basique (endpoints incomplets)
```

**Problème**: Pas d'interface utilisateur! Système utilisable uniquement via code Python.

### ❌ CE QUI MANQUE (Frontend)

```
Frontend ❌ 0% FAIT
├── ❌ Interface utilisateur (UI)
├── ❌ Expérience utilisateur (UX)
├── ❌ Dashboard interactif
├── ❌ Graphiques temps réel
├── ❌ Animations fluides
├── ❌ Design moderne
└── ❌ Application web accessible
```

**Résultat**: Personne ne peut utiliser le système sauf développeurs!

---

## 🎯 VISION FRONTEND ULTRA-AVANCÉ

### Ce qu'on veut créer:

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 TREND VIRAL ENGINE PRO - Dashboard                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 PRÉDICTION EN TEMPS RÉEL                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Titre: "10 astuces Python pour débutants"            │ │
│  │ Plateforme: [TikTok ▼]  Followers: [10,000]          │ │
│  │                                                       │ │
│  │ ⚡ Analyse IA en cours... [████████░░] 80%            │ │
│  │                                                       │ │
│  │ ✅ PRÉDICTIONS:                                       │ │
│  │   📈 47,000 vues (±30%)                               │ │
│  │   ❤️  3,760 likes                                      │ │
│  │   💰 €18,964 revenue                                  │ │
│  │   📊 ROI: 37,829%                                     │ │
│  │                                                       │ │
│  │ 🎯 Meilleur moment: Vendredi 19:00                   │ │
│  │                                                       │ │
│  │ 💡 RECOMMANDATIONS:                                   │ │
│  │   • 🎵 Utiliser un son trending                       │ │
│  │   • #️⃣ Hashtags: mix trending + niche                │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  📊 COMPARAISON PLATEFORMES                                 │
│  ┌──────┬──────────┬─────────┬──────────┐                  │
│  │ 🥇 Instagram  │ 61,500   │ €49,530  │                  │
│  │ 🥈 TikTok     │ 41,000   │ €32,987  │                  │
│  │ 🥉 Reddit     │ 32,800   │ €26,369  │                  │
│  └──────┴──────────┴─────────┴──────────┘                  │
│                                                             │
│  📈 GRAPHIQUE TEMPS RÉEL (Animation fluide)                 │
│  [Graphique ligne montrant prédictions vs historique]      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Caractéristiques**:

- ⚡ **Temps réel**: Prédictions instantanées (< 2 secondes)
- 🎨 **Animations fluides**: Transitions Framer Motion
- 📊 **Graphiques interactifs**: Charts.js / Recharts
- 🌓 **Dark/Light mode**: Toggle instantané
- 📱 **Responsive**: Mobile + Tablet + Desktop
- 🚀 **Performance**: 90+ Lighthouse score
- ♿ **Accessible**: WCAG 2.1 AA compliance

---

## 🏗️ ARCHITECTURE FRONTEND (POO)

### Stack Technique Recommandée

```typescript
Frontend Stack (Ultra-Moderne 2025)
├── Framework: Next.js 14 (React 18)
│   ├── App Router (nouvelle architecture)
│   ├── Server Components (performance)
│   ├── Server Actions (API simplifiées)
│   └── TypeScript strict mode
│
├── Styling: Tailwind CSS 4.0
│   ├── Design system custom
│   ├── Dark mode natif
│   └── Animations Framer Motion
│
├── State Management: Zustand
│   ├── Store POO (classes)
│   ├── Persist state (localStorage)
│   └── DevTools integration
│
├── Data Fetching: TanStack Query (React Query)
│   ├── Cache intelligent
│   ├── Optimistic updates
│   └── Real-time avec WebSocket
│
├── Forms: React Hook Form + Zod
│   ├── Validation TypeScript
│   ├── Performance optimale
│   └── Error handling
│
├── Charts: Recharts + D3.js
│   ├── Graphiques interactifs
│   ├── Animations fluides
│   └── Responsive
│
└── Real-time: Socket.io
    ├── WebSocket connection
    ├── Event-driven updates
    └── Reconnection auto
```

### Architecture POO Frontend

```typescript
// 1. MODELS (POO - Classes)
// src/frontend/models/Prediction.ts

export class Prediction {
  id: string;
  title: string;
  platform: Platform;
  viralScore: number;
  predictedViews: number;
  viewsRange: [number, number];
  predictedLikes: number;
  estimatedRevenue: number;
  roi: number;
  recommendations: string[];
  createdAt: Date;

  constructor(data: PredictionData) {
    this.id = data.id;
    this.title = data.title;
    this.platform = data.platform;
    this.viralScore = data.viral_score;
    this.predictedViews = data.predicted_views;
    this.viewsRange = data.views_range;
    this.predictedLikes = data.predicted_likes;
    this.estimatedRevenue = data.estimated_revenue;
    this.roi = data.roi_percentage;
    this.recommendations = data.recommendations;
    this.createdAt = new Date(data.created_at);
  }

  // Méthodes business logic
  isHighROI(): boolean {
    return this.roi > 10000;
  }

  getFormattedViews(): string {
    return new Intl.NumberFormat("fr-FR").format(this.predictedViews);
  }

  getFormattedRevenue(): string {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
    }).format(this.estimatedRevenue);
  }

  getConfidenceLevel(): "high" | "medium" | "low" {
    if (this.viralScore > 0.85) return "high";
    if (this.viralScore > 0.7) return "medium";
    return "low";
  }
}

// 2. SERVICES (POO - API Calls)
// src/frontend/services/PredictionService.ts

export class PredictionService {
  private baseURL: string;
  private wsClient: WebSocketClient;

  constructor(baseURL: string = "http://localhost:8000/api") {
    this.baseURL = baseURL;
    this.wsClient = new WebSocketClient();
  }

  async predict(
    title: string,
    platform: Platform,
    followerCount: number
  ): Promise<Prediction> {
    const response = await fetch(`${this.baseURL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        platform,
        follower_count: followerCount,
      }),
    });

    const data = await response.json();
    return new Prediction(data);
  }

  async comparePlatforms(
    title: string,
    followerCounts: Record<Platform, number>
  ): Promise<Map<Platform, Prediction>> {
    const response = await fetch(`${this.baseURL}/compare-platforms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        follower_counts: followerCounts,
      }),
    });

    const data = await response.json();
    const predictions = new Map<Platform, Prediction>();

    for (const [platform, predData] of Object.entries(data)) {
      predictions.set(platform as Platform, new Prediction(predData));
    }

    return predictions;
  }

  subscribeToRealtimeUpdates(
    callback: (prediction: Prediction) => void
  ): () => void {
    return this.wsClient.subscribe("prediction:update", (data) => {
      callback(new Prediction(data));
    });
  }
}

// 3. STORES (POO - State Management avec Zustand)
// src/frontend/stores/usePredictionStore.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PredictionStore {
  predictions: Prediction[];
  currentPrediction: Prediction | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addPrediction: (prediction: Prediction) => void;
  setCurrentPrediction: (prediction: Prediction | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearPredictions: () => void;
}

export const usePredictionStore = create<PredictionStore>()(
  persist(
    (set) => ({
      predictions: [],
      currentPrediction: null,
      isLoading: false,
      error: null,

      addPrediction: (prediction) =>
        set((state) => ({
          predictions: [prediction, ...state.predictions].slice(0, 50),
        })),

      setCurrentPrediction: (prediction) =>
        set({ currentPrediction: prediction }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      clearPredictions: () => set({ predictions: [] }),
    }),
    {
      name: "prediction-storage",
    }
  )
);

// 4. HOOKS (POO - Custom Hooks)
// src/frontend/hooks/usePrediction.ts

export function usePrediction() {
  const store = usePredictionStore();
  const service = useMemo(() => new PredictionService(), []);

  const predict = useCallback(
    async (title: string, platform: Platform, followers: number) => {
      store.setLoading(true);
      store.setError(null);

      try {
        const prediction = await service.predict(title, platform, followers);
        store.addPrediction(prediction);
        store.setCurrentPrediction(prediction);
        return prediction;
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unknown error";
        store.setError(message);
        throw error;
      } finally {
        store.setLoading(false);
      }
    },
    [service, store]
  );

  return {
    predictions: store.predictions,
    currentPrediction: store.currentPrediction,
    isLoading: store.isLoading,
    error: store.error,
    predict,
  };
}

// 5. COMPONENTS (POO - React Components)
// src/frontend/components/PredictionForm.tsx

("use client");

import { useState } from "react";
import { motion } from "framer-motion";
import { usePrediction } from "@/hooks/usePrediction";

export function PredictionForm() {
  const [title, setTitle] = useState("");
  const [platform, setPlatform] = useState<Platform>("tiktok");
  const [followers, setFollowers] = useState(10000);

  const { predict, isLoading } = usePrediction();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await predict(title, platform, followers);
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      onSubmit={handleSubmit}
      className="space-y-6 bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg"
    >
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Titre du contenu
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex: 10 astuces Python pour débutants"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm 
                     focus:border-indigo-500 focus:ring-indigo-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Plateforme
        </label>
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value as Platform)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        >
          <option value="tiktok">TikTok</option>
          <option value="instagram">Instagram</option>
          <option value="youtube">YouTube</option>
          <option value="reddit">Reddit</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-indigo-600 text-white py-3 rounded-lg 
                   hover:bg-indigo-700 transition-colors disabled:opacity-50"
      >
        {isLoading ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            ⚡ Analyse en cours...
          </motion.div>
        ) : (
          "🚀 Prédire les performances"
        )}
      </button>
    </motion.form>
  );
}
```

---

## 📁 STRUCTURE PROJET FRONTEND

```
trend-viral-engine-frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (dashboard)/              # Groupe routes dashboard
│   │   │   ├── page.tsx              # Page principale
│   │   │   ├── predictions/
│   │   │   │   ├── page.tsx          # Liste prédictions
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx      # Détail prédiction
│   │   │   ├── compare/
│   │   │   │   └── page.tsx          # Comparaison plateformes
│   │   │   └── analytics/
│   │   │       └── page.tsx          # Analytics temps réel
│   │   │
│   │   ├── api/                      # API Routes (proxy backend)
│   │   │   ├── predict/
│   │   │   │   └── route.ts
│   │   │   └── compare/
│   │   │       └── route.ts
│   │   │
│   │   ├── layout.tsx                # Layout global
│   │   └── page.tsx                  # Landing page
│   │
│   ├── components/                   # Components React
│   │   ├── ui/                       # Components UI réutilisables
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Select.tsx
│   │   │
│   │   ├── features/                 # Features business
│   │   │   ├── PredictionForm.tsx
│   │   │   ├── PredictionCard.tsx
│   │   │   ├── PlatformComparison.tsx
│   │   │   ├── RealtimeChart.tsx
│   │   │   └── RecommendationList.tsx
│   │   │
│   │   └── layout/                   # Layout components
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   │
│   ├── models/                       # Classes POO
│   │   ├── Prediction.ts
│   │   ├── Platform.ts
│   │   └── User.ts
│   │
│   ├── services/                     # Services API
│   │   ├── PredictionService.ts
│   │   ├── AnalyticsService.ts
│   │   └── WebSocketClient.ts
│   │
│   ├── stores/                       # State management
│   │   ├── usePredictionStore.ts
│   │   ├── useUserStore.ts
│   │   └── useUIStore.ts
│   │
│   ├── hooks/                        # Custom hooks
│   │   ├── usePrediction.ts
│   │   ├── useRealtime.ts
│   │   └── useTheme.ts
│   │
│   ├── lib/                          # Utilities
│   │   ├── utils.ts
│   │   ├── validators.ts
│   │   └── formatters.ts
│   │
│   ├── styles/                       # Styles globaux
│   │   └── globals.css
│   │
│   └── types/                        # TypeScript types
│       ├── prediction.ts
│       ├── api.ts
│       └── common.ts
│
├── public/                           # Assets statiques
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── tests/                            # Tests
│   ├── unit/
│   └── e2e/
│
├── .env.local                        # Config locale
├── next.config.js                    # Config Next.js
├── tailwind.config.ts                # Config Tailwind
├── tsconfig.json                     # Config TypeScript
└── package.json
```

---

## 🎨 DESIGN SYSTEM ULTRA-MODERNE

### Couleurs (Dark Mode Ready)

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Brand colors
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9", // Main brand color
          600: "#0284c7",
          900: "#0c4a6e",
        },

        // Success (prédictions high ROI)
        success: {
          50: "#f0fdf4",
          500: "#22c55e",
          900: "#14532d",
        },

        // Warning (prédictions medium)
        warning: {
          50: "#fffbeb",
          500: "#f59e0b",
          900: "#78350f",
        },

        // Danger (prédictions low)
        danger: {
          50: "#fef2f2",
          500: "#ef4444",
          900: "#7f1d1d",
        },

        // Neutral (dark mode)
        gray: {
          50: "#f9fafb",
          100: "#f3f4f6",
          800: "#1f2937",
          900: "#111827",
          950: "#030712",
        },
      },

      animation: {
        "fade-in": "fadeIn 0.5s ease-in",
        "slide-up": "slideUp 0.5s ease-out",
        "bounce-slow": "bounce 2s infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },

      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
};
```

### Components UI (Exemple Button)

```typescript
// src/components/ui/Button.tsx
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  icon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses =
    "inline-flex items-center justify-center rounded-lg font-medium transition-all";

  const variants = {
    primary: "bg-primary-500 text-white hover:bg-primary-600 active:scale-95",
    secondary:
      "bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-700 dark:text-white",
    danger: "bg-danger-500 text-white hover:bg-danger-600",
    ghost: "bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={cn(
        baseClasses,
        variants[variant],
        sizes[size],
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="mr-2"
        >
          ⚡
        </motion.div>
      ) : icon ? (
        <span className="mr-2">{icon}</span>
      ) : null}
      {children}
    </motion.button>
  );
}
```

---

## ⚡ FONCTIONNALITÉS TEMPS RÉEL

### WebSocket Integration

```typescript
// src/services/WebSocketClient.ts
export class WebSocketClient {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(url: string = "ws://localhost:8000/ws") {
    this.socket = io(url, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.socket.on("connect", () => {
      console.log("✅ WebSocket connected");
      this.reconnectAttempts = 0;
    });

    this.socket.on("disconnect", () => {
      console.log("⚠️ WebSocket disconnected");
    });

    this.socket.on("connect_error", () => {
      this.reconnectAttempts++;
      console.log(
        `🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
    });
  }

  subscribe(event: string, callback: (data: any) => void): () => void {
    if (!this.socket) throw new Error("WebSocket not connected");

    this.socket.on(event, callback);

    // Return unsubscribe function
    return () => {
      this.socket?.off(event, callback);
    };
  }

  emit(event: string, data: any) {
    if (!this.socket) throw new Error("WebSocket not connected");
    this.socket.emit(event, data);
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }
}

// Hook pour utiliser WebSocket
export function useRealtime() {
  const [client] = useState(() => new WebSocketClient());

  useEffect(() => {
    client.connect();
    return () => client.disconnect();
  }, [client]);

  return client;
}
```

### Dashboard Temps Réel

```typescript
// src/app/(dashboard)/page.tsx
"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePrediction } from "@/hooks/usePrediction";
import { useRealtime } from "@/services/WebSocketClient";
import { PredictionForm } from "@/components/features/PredictionForm";
import { PredictionCard } from "@/components/features/PredictionCard";
import { RealtimeChart } from "@/components/features/RealtimeChart";

export default function DashboardPage() {
  const { predictions, currentPrediction } = usePrediction();
  const wsClient = useRealtime();

  useEffect(() => {
    // Subscribe to real-time prediction updates
    const unsubscribe = wsClient.subscribe("prediction:update", (data) => {
      console.log("📊 Real-time update:", data);
      // Update store automatiquement
    });

    return unsubscribe;
  }, [wsClient]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl font-bold text-gray-900 dark:text-white mb-8"
        >
          🚀 Trend Viral Engine Pro
        </motion.h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Formulaire prédiction */}
          <div className="lg:col-span-1">
            <PredictionForm />
          </div>

          {/* Résultats temps réel */}
          <div className="lg:col-span-2">
            <AnimatePresence mode="wait">
              {currentPrediction && (
                <motion.div
                  key={currentPrediction.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.3 }}
                >
                  <PredictionCard prediction={currentPrediction} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Graphique temps réel */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-6"
            >
              <RealtimeChart predictions={predictions} />
            </motion.div>
          </div>
        </div>

        {/* Historique prédictions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12"
        >
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            📊 Historique des prédictions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {predictions.map((prediction, index) => (
              <motion.div
                key={prediction.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <PredictionCard prediction={prediction} compact />
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
```

---

## 📊 CE QU'IL MANQUE EXACTEMENT

### 1. Backend - API Endpoints Complets (2-3 jours)

**Actuellement**: API basique incomplet  
**Besoin**: Endpoints REST complets + WebSocket

```python
# src/api/routes/predictions.py (À COMPLÉTER)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.scoring.advanced_metrics_predictor import get_advanced_metrics_predictor

router = APIRouter(prefix="/api/v1", tags=["predictions"])

@router.post("/predict")
async def predict_content(
    title: str,
    platform: str,
    follower_count: int = 0
):
    """Endpoint prédiction principal"""
    predictor = get_advanced_metrics_predictor()

    # 1. Score viral (ML model)
    viral_score = 0.85  # TODO: Calculer avec ML model

    # 2. Prédictions exactes
    prediction = predictor.predict_metrics(
        viral_score=viral_score,
        platform=platform,
        follower_count=follower_count
    )

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "platform": platform,
        "viral_score": viral_score,
        "predicted_views": prediction.predicted_views,
        "views_range": prediction.views_range,
        "predicted_likes": prediction.predicted_likes,
        "predicted_comments": prediction.predicted_comments,
        "engagement_rate": prediction.engagement_rate,
        "estimated_revenue": prediction.estimated_revenue,
        "roi_percentage": prediction.roi_percentage,
        "best_posting_day": prediction.best_posting_day,
        "best_posting_time": prediction.best_posting_time,
        "recommendations": prediction.recommendations,
        "created_at": datetime.now().isoformat()
    }

@router.post("/compare-platforms")
async def compare_platforms(
    title: str,
    follower_counts: dict[str, int]
):
    """Comparer performance sur plusieurs plateformes"""
    predictor = get_advanced_metrics_predictor()
    viral_score = 0.85  # TODO: Calculer

    comparison = predictor.compare_platforms(
        viral_score=viral_score,
        follower_counts=follower_counts
    )

    return {
        platform: {
            "predicted_views": pred.predicted_views,
            "estimated_revenue": pred.estimated_revenue,
            "roi_percentage": pred.roi_percentage
        }
        for platform, pred in comparison.items()
    }

# WebSocket pour temps réel
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Recevoir données du client
            data = await websocket.receive_json()

            # Traiter prédiction
            # ... (code prédiction)

            # Envoyer résultat temps réel
            await websocket.send_json({
                "event": "prediction:update",
                "data": prediction_result
            })
    except WebSocketDisconnect:
        print("Client disconnected")
```

### 2. Frontend - Application Complète (1-2 semaines)

**Actuellement**: Rien  
**Besoin**: Application Next.js complète

```bash
# Installation
npx create-next-app@latest trend-viral-engine-frontend --typescript --tailwind --app

# Packages additionnels
npm install zustand @tanstack/react-query framer-motion recharts socket.io-client
npm install @hookform/resolvers react-hook-form zod
npm install -D @types/socket.io-client
```

### 3. Design System (3-4 jours)

- [ ] Composants UI réutilisables (Button, Card, Input, etc.)
- [ ] Dark mode implementation
- [ ] Animations Framer Motion
- [ ] Graphiques Recharts
- [ ] Layout responsive

### 4. Intégration Backend-Frontend (2-3 jours)

- [ ] Services API TypeScript
- [ ] WebSocket client
- [ ] State management (Zustand)
- [ ] Error handling
- [ ] Loading states

### 5. Tests & Optimisation (1 semaine)

- [ ] Tests unitaires (Vitest)
- [ ] Tests E2E (Playwright)
- [ ] Performance (Lighthouse 90+)
- [ ] SEO optimization
- [ ] Accessibility (WCAG 2.1)

---

## 📅 PLANNING DÉVELOPPEMENT

### Sprint 1 (Semaine 1): Backend API

**Jours 1-2**: Endpoints REST

- [ ] POST /api/v1/predict
- [ ] POST /api/v1/compare-platforms
- [ ] GET /api/v1/predictions (historique)
- [ ] GET /api/v1/predictions/:id

**Jours 3-4**: WebSocket

- [ ] WebSocket server setup
- [ ] Real-time prediction updates
- [ ] Connection management

**Jour 5**: Tests API

- [ ] Tests unitaires endpoints
- [ ] Documentation Swagger
- [ ] Postman collection

### Sprint 2 (Semaine 2): Frontend Setup

**Jours 1-2**: Project setup

- [ ] Next.js installation
- [ ] Structure folders
- [ ] Config TypeScript/Tailwind
- [ ] Design system base

**Jours 3-4**: Models & Services

- [ ] Classes POO (Prediction, Platform)
- [ ] API services (PredictionService)
- [ ] WebSocket client
- [ ] State management (Zustand)

**Jour 5**: Components UI

- [ ] Button, Card, Input
- [ ] Layout (Header, Sidebar)
- [ ] Animations setup

### Sprint 3 (Semaine 3): Features Core

**Jours 1-2**: Prédiction Form

- [ ] PredictionForm component
- [ ] Validation (React Hook Form + Zod)
- [ ] Real-time updates

**Jours 3-4**: Results Display

- [ ] PredictionCard component
- [ ] Graphiques (Recharts)
- [ ] Animations entrée/sortie

**Jour 5**: Comparaison Plateformes

- [ ] PlatformComparison component
- [ ] Tableau comparatif
- [ ] Recommandations

### Sprint 4 (Semaine 4): Polish & Deploy

**Jours 1-2**: Dark mode + Responsive

- [ ] Dark mode toggle
- [ ] Mobile responsive
- [ ] Tablet responsive

**Jours 3-4**: Tests & Optimisation

- [ ] Tests E2E
- [ ] Performance optimization
- [ ] Accessibility

**Jour 5**: Deployment

- [ ] Deploy backend (Docker)
- [ ] Deploy frontend (Vercel)
- [ ] CI/CD pipeline

---

## 🎯 RÉSUMÉ: CE QU'IL FAUT FAIRE

### Étape 1: Compléter API Backend (2-3 jours)

```python
# À faire dans: src/api/routes/predictions.py
- Endpoints REST complets
- WebSocket server
- Error handling
```

### Étape 2: Setup Frontend Next.js (1 jour)

```bash
npx create-next-app@latest --typescript --tailwind --app
npm install zustand framer-motion recharts socket.io-client
```

### Étape 3: Architecture POO Frontend (2-3 jours)

```typescript
- Models: Prediction.ts, Platform.ts
- Services: PredictionService.ts, WebSocketClient.ts
- Stores: usePredictionStore.ts
- Hooks: usePrediction.ts, useRealtime.ts
```

### Étape 4: Components UI (3-4 jours)

```typescript
- PredictionForm (input + validation)
- PredictionCard (affichage résultats)
- RealtimeChart (graphiques)
- PlatformComparison (comparaison)
```

### Étape 5: Integration & Polish (1 semaine)

```typescript
- WebSocket integration
- Dark mode
- Animations fluides
- Responsive design
- Tests
```

**TEMPS TOTAL**: 3-4 semaines pour frontend ultra-avancé complet

---

## 🚀 PROCHAINE ACTION

**Choisis**:

**Option A: Backend d'abord** (recommandé)

```bash
# 1. Compléter API endpoints (2-3 jours)
cd "/Users/imad/Desktop/Trend & Viral Engine Pro"
# Créer: src/api/routes/predictions_complete.py
# Ajouter WebSocket support

# 2. Tester API complète
python test_api_complete.py
```

**Option B: Frontend d'abord**

```bash
# 1. Setup Next.js (1 jour)
cd "/Users/imad/Desktop"
npx create-next-app@latest trend-viral-engine-frontend

# 2. Architecture POO (2-3 jours)
# Créer tous les fichiers ci-dessus
```

**Ma recommandation**: **Option A** (backend d'abord)

- API complète = frontend peut consommer immédiatement
- Plus facile de tester backend isolément
- Frontend peut être developpé en parallèle après

---

## ✅ CHECKLIST AVANT DE COMMENCER FRONTEND

- [ ] YouTube API configurée (PRIORITÉ du dernier message)
- [ ] API endpoints REST complets
- [ ] WebSocket server fonctionnel
- [ ] Documentation API (Swagger)
- [ ] Tests API passent

**Ensuite** → Lancer développement frontend ultra-avancé!

**Questions?** Dis-moi si tu veux que je commence par créer:

1. ✅ API endpoints complets backend
2. ✅ Setup frontend Next.js
3. ✅ Architecture POO complète
4. ✅ Ou tout en même temps!
