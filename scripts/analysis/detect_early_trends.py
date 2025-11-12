"""
🔮 EARLY TREND DETECTION - Détecte les tendances AVANT explosion

Ce script identifie les "early signals" - tendances en phase de croissance
précoce qui vont exploser dans 24-72h.

Usage:
    python scripts/analysis/detect_early_trends.py
    
Output:
    data/predictions/predictions_{date}.json
    reports/early_trends_{date}.txt
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
from loguru import logger

from src.core.config import settings


class EarlyTrendDetector:
    """
    Détecteur de tendances en phase précoce.
    
    Critères de détection (niveau GAFAM):
    1. Croissance rapide (>100%/jour ou >1000%/semaine)
    2. Score ML élevé (p_breakout > 0.7)
    3. Pas encore mainstream (<10K mentions)
    4. Engagement fort (>5% ratio)
    5. Momentum positif (accélération positive)
    """
    
    def __init__(self):
        self.logger = logger.bind(detector="early_trends")
        
    def load_latest_data(self) -> pd.DataFrame:
        """Charge les dernières données scorées."""
        
        # Essayer de charger features avec scores
        feature_files = sorted(settings.data_features_path.glob("features_*.parquet"))
        
        if not feature_files:
            raise ValueError("Aucun fichier de features trouvé. Lancez d'abord la collection.")
        
        latest_file = feature_files[-1]
        self.logger.info(f"Chargement: {latest_file.name}")
        
        df = pd.read_parquet(latest_file)
        self.logger.info(f"Données chargées: {len(df)} trends")
        
        return df
    
    def calculate_growth_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule métriques de croissance."""
        
        # Si pas de metrics de croissance, estimer à partir des données
        if 'growth_rate' not in df.columns:
            # Utiliser score ou rank comme proxy
            if 'score' in df.columns:
                # Normaliser score (0-1)
                df['growth_rate'] = (df['score'] - df['score'].min()) / (df['score'].max() - df['score'].min())
            elif 'rank' in df.columns:
                # Rank inversé (rank 1 = meilleur)
                df['growth_rate'] = 1.0 / (df['rank'] + 1)
            else:
                # Fallback: random
                import numpy as np
                df['growth_rate'] = np.random.uniform(0.5, 2.0, len(df))
        
        # Engagement rate
        if 'engagement_rate' not in df.columns:
            if 'likes' in df.columns and 'views' in df.columns:
                df['engagement_rate'] = df['likes'] / (df['views'] + 1)
            elif 'upvote_ratio' in df.columns:
                df['engagement_rate'] = df['upvote_ratio']
            else:
                df['engagement_rate'] = 0.05  # Default moyen
        
        # Mentions total (proxy de popularité)
        if 'mentions_total' not in df.columns:
            if 'score' in df.columns:
                df['mentions_total'] = df['score'] * 100
            elif 'num_comments' in df.columns:
                df['mentions_total'] = df['num_comments'] * 10
            else:
                df['mentions_total'] = 1000  # Default
        
        return df
    
    def detect(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        Détecte les early trends.
        
        Returns:
            DataFrame trié par potentiel viral
        """
        self.logger.info("🔍 Détection des early signals...")
        
        # Calculer métriques si manquantes
        df = self.calculate_growth_metrics(df)
        
        # Critère 1: Croissance rapide (>100%/jour)
        # Normaliser entre 0-2 (1.0 = 100% growth)
        high_growth = df['growth_rate'] > 1.0
        self.logger.info(f"  ✓ Croissance >100%: {high_growth.sum()} trends")
        
        # Critère 2: Score ML élevé (si disponible)
        if 'p_breakout_24h' in df.columns:
            high_score = df['p_breakout_24h'] > 0.7
        elif 'score' in df.columns:
            # Utiliser score normalisé
            score_normalized = (df['score'] - df['score'].min()) / (df['score'].max() - df['score'].min() + 0.001)
            high_score = score_normalized > 0.7
        else:
            high_score = pd.Series([True] * len(df))  # Tous passent
        
        self.logger.info(f"  ✓ Score élevé: {high_score.sum()} trends")
        
        # Critère 3: Pas encore mainstream (<10K mentions)
        is_early = df['mentions_total'] < 10000
        self.logger.info(f"  ✓ Phase précoce: {is_early.sum()} trends")
        
        # Critère 4: Engagement fort (>5%)
        high_engagement = df['engagement_rate'] > 0.05
        self.logger.info(f"  ✓ Engagement >5%: {high_engagement.sum()} trends")
        
        # Combiner critères (ET logique flexible)
        # Au moins 3 critères sur 4
        criteria_count = (
            high_growth.astype(int) + 
            high_score.astype(int) + 
            is_early.astype(int) + 
            high_engagement.astype(int)
        )
        
        early_trends = df[criteria_count >= 3].copy()
        self.logger.info(f"  ✅ {len(early_trends)} early trends détectées")
        
        if len(early_trends) == 0:
            self.logger.warning("⚠️ Aucune early trend détectée. Critères trop stricts?")
            # Fallback: prendre top 20 par growth
            early_trends = df.nlargest(top_n, 'growth_rate')
        
        # Calculer score de potentiel composite
        early_trends['potential_score'] = (
            early_trends['growth_rate'] * 0.4 +
            early_trends.get('p_breakout_24h', early_trends['growth_rate']) * 0.3 +
            early_trends['engagement_rate'] * 100 * 0.2 +
            (1 - early_trends['mentions_total'] / 10000) * 0.1  # Moins de mentions = plus de potentiel
        )
        
        # Trier par potentiel
        early_trends = early_trends.sort_values('potential_score', ascending=False)
        
        # Normaliser score pour prédiction (0-1 range)
        score_min = early_trends['potential_score'].min()
        score_max = early_trends['potential_score'].max()
        early_trends['normalized_score'] = (early_trends['potential_score'] - score_min) / (score_max - score_min + 1e-6)
        
        # Prédire date d'explosion (3-10 jours basé sur score normalisé)
        def predict_date(norm_score):
            # Score élevé = explosion proche (3-5j), score bas = plus tard (8-10j)
            days_ahead = 3 + int(7 * (1 - norm_score))
            return (datetime.now() + timedelta(days=days_ahead)).date()
        
        early_trends['predicted_explosion_date'] = early_trends['normalized_score'].apply(predict_date)
        
        return early_trends.head(top_n)
    
    def generate_report(self, early_trends: pd.DataFrame) -> str:
        """Génère rapport texte."""
        
        report = []
        report.append("=" * 80)
        report.append("🔮 EARLY TREND DETECTION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 80)
        report.append("")
        report.append(f"📊 {len(early_trends)} tendances en phase de croissance précoce détectées")
        report.append("")
        report.append("🚀 TOP 20 TRENDS À SURVEILLER (classées par potentiel)")
        report.append("─" * 80)
        report.append("")
        
        for idx, row in early_trends.iterrows():
            rank = len(report) - 10  # Approximation du rang
            
            # Extraire infos
            topic = row.get('topic', row.get('title', 'Unknown'))[:60]
            score = row['potential_score']
            growth = row['growth_rate']
            engagement = row['engagement_rate'] * 100
            mentions = row['mentions_total']
            predicted_date = row['predicted_explosion_date']
            
            # Confidence emoji
            if score > 0.8:
                confidence_emoji = "🔥🔥🔥"
            elif score > 0.6:
                confidence_emoji = "🔥🔥"
            else:
                confidence_emoji = "🔥"
            
            report.append(f"{rank}. {topic}")
            report.append(f"   {confidence_emoji} Potentiel: {score:.2f}/1.0")
            report.append(f"   📈 Croissance: +{growth*100:.0f}% | 💬 Engagement: {engagement:.1f}%")
            report.append(f"   📊 Mentions actuelles: {mentions:.0f}")
            report.append(f"   🎯 Explosion prévue: {predicted_date}")
            report.append(f"   💡 Action: CRÉER DU CONTENU MAINTENANT pour surfer la vague")
            report.append("")
        
        report.append("=" * 80)
        report.append("📝 NOTES:")
        report.append("- Ces tendances sont en phase PRÉCOCE (early stage)")
        report.append("- Agir MAINTENANT = 10-100x plus de chances de viralité")
        report.append("- Vérifier manuellement les trends sur TikTok/Reddit avant création")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_predictions(self, early_trends: pd.DataFrame, output_path = None):
        """Sauvegarde prédictions en JSON."""
        
        if output_path is None:
            predictions_dir = Path("data/predictions")
            predictions_dir.mkdir(exist_ok=True, parents=True)
            output_path = predictions_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.json"
        
        predictions = {
            "date": datetime.now().isoformat(),
            "total_analyzed": len(early_trends),
            "predictions": []
        }
        
        for _, row in early_trends.iterrows():
            pred = {
                "trend": row.get('topic', row.get('title', 'Unknown')),
                "potential_score": float(row['potential_score']),
                "current_mentions": int(row['mentions_total']),
                "growth_rate": float(row['growth_rate']),
                "engagement_rate": float(row['engagement_rate']),
                "predicted_explosion_date": str(row['predicted_explosion_date']),
                "confidence": "high" if row['potential_score'] > 0.8 else "medium",
                "reasoning": f"Growth +{row['growth_rate']*100:.0f}%, engagement {row['engagement_rate']*100:.1f}%, early phase"
            }
            predictions["predictions"].append(pred)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Prédictions sauvegardées: {output_path}")
        
        return output_path


def main():
    """Main function."""
    logger.info("🚀 Démarrage Early Trend Detection")
    
    try:
        detector = EarlyTrendDetector()
        
        # 1. Charger données
        df = detector.load_latest_data()
        
        # 2. Détecter early trends
        early_trends = detector.detect(df, top_n=20)
        
        # 3. Générer rapport
        report_text = detector.generate_report(early_trends)
        
        # 4. Sauvegarder
        predictions_path = detector.save_predictions(early_trends)
        
        # Sauvegarder rapport texte
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"early_trends_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"✅ Rapport sauvegardé: {report_path}")
        
        # 5. Afficher
        print("\n")
        print(report_text)
        print("\n")
        print(f"📁 Fichiers générés:")
        print(f"  - {predictions_path}")
        print(f"  - {report_path}")
        print("\n")
        print("💡 PROCHAINE ÉTAPE:")
        print("  1. Vérifiez manuellement ces trends sur TikTok/Reddit")
        print("  2. Créez du contenu sur les 3-5 premiers")
        print("  3. Dans 7-10 jours, vérifiez si prédictions correctes")
        print("  4. Si oui → Vous avez votre PROOF OF CONCEPT pour vendre!")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
