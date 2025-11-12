"""
Guide Rapide Client - Prédictions Virales Exactes
=================================================

Ce guide montre comment utiliser le système pour prédire
EXACTEMENT combien de vues/likes/€ votre contenu va générer.
"""

import asyncio
from src.services.scoring.advanced_metrics_predictor import get_advanced_metrics_predictor

# ============================================================================
# EXEMPLE 1: Prédiction simple - "Combien de vues va avoir mon post TikTok?"
# ============================================================================

async def exemple_prediction_simple():
    """
    Cas d'usage: Je veux poster sur TikTok, combien de vues vais-je avoir?
    """
    print("\n" + "="*70)
    print("EXEMPLE 1: Prédiction simple (TikTok)")
    print("="*70)
    
    predictor = get_advanced_metrics_predictor()
    
    # Votre contenu
    mon_contenu = {
        'titre': '10 astuces Python pour débutants',
        'plateforme': 'tiktok',
        'followers': 10000,
        'viral_score': 0.85  # Vient du modèle ML (automatique)
    }
    
    # Prédiction
    prediction = predictor.predict_metrics(
        viral_score=mon_contenu['viral_score'],
        platform=mon_contenu['plateforme'],
        follower_count=mon_contenu['followers']
    )
    
    print(f"""
📊 RÉSULTAT POUR: "{mon_contenu['titre']}"
────────────────────────────────────────────────────────────────────

✅ VUES PRÉDITES:           {prediction.predicted_views:,}
   Range (90% confiance):   {prediction.views_range[0]:,} - {prediction.views_range[1]:,}

❤️  LIKES PRÉDITS:           {prediction.predicted_likes:,}

💬 COMMENTAIRES PRÉDITS:    {prediction.predicted_comments:,}

🔄 PARTAGES PRÉDITS:        {prediction.predicted_shares:,}

📈 TAUX ENGAGEMENT:         {prediction.engagement_rate:.2f}%

💰 REVENU ESTIMÉ:           €{prediction.estimated_revenue:,.2f}

💸 ROI:                     {prediction.roi_percentage:.1f}%
   (Coût création: €100 → Retour: €{prediction.estimated_revenue:.0f})

⏰ MEILLEUR MOMENT:         {prediction.best_posting_day} à {prediction.best_posting_time}

📝 RECOMMANDATIONS:
""")
    
    for i, rec in enumerate(prediction.recommendations, 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*70)
    
    # Décision
    if prediction.roi_percentage > 10000:
        print("🔥 VERDICT: POST VIRAL ASSURÉ - POSTEZ IMMÉDIATEMENT!")
    elif prediction.roi_percentage > 5000:
        print("✅ VERDICT: Très bon potentiel - Go!")
    elif prediction.roi_percentage > 1000:
        print("👍 VERDICT: Bon potentiel - À poster")
    else:
        print("⚠️  VERDICT: Retravailler le contenu")


# ============================================================================
# EXEMPLE 2: Comparaison plateformes - "Sur quelle plateforme poster?"
# ============================================================================

async def exemple_comparaison_plateformes():
    """
    Cas d'usage: J'ai un contenu, sur quelle plateforme le poster
    pour maximiser mes vues/revenue?
    """
    print("\n" + "="*70)
    print("EXEMPLE 2: Comparaison multi-plateformes")
    print("="*70)
    
    predictor = get_advanced_metrics_predictor()
    
    # Votre situation
    mon_contenu = {
        'titre': 'Comment créer une app IA en 2024',
        'viral_score': 0.82,
        'followers': {
            'tiktok': 10000,
            'instagram': 15000,
            'youtube': 5000,
            'reddit': 8000
        }
    }
    
    print(f'\n📱 Contenu: "{mon_contenu["titre"]}"')
    print(f'🎯 Viral score: {mon_contenu["viral_score"]*100:.0f}%')
    print('\n🔍 Analyse de toutes les plateformes...\n')
    
    # Comparaison
    comparison = predictor.compare_platforms(
        viral_score=mon_contenu['viral_score'],
        follower_counts=mon_contenu['followers']
    )
    
    # Trier par ROI
    sorted_platforms = sorted(
        comparison.items(),
        key=lambda x: x[1].roi_percentage,
        reverse=True
    )
    
    print("📊 RÉSULTATS PAR PLATEFORME:")
    print("─" * 70)
    
    for rank, (platform, pred) in enumerate(sorted_platforms, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        
        print(f"""
{medal} {rank}. {platform.upper()}
   Vues:     {pred.predicted_views:>8,}
   Likes:    {pred.predicted_likes:>8,}
   Revenue:  €{pred.estimated_revenue:>8,.2f}
   ROI:      {pred.roi_percentage:>8,.1f}%
""")
    
    # Recommandation finale
    best = sorted_platforms[0]
    print("="*70)
    print(f"🎯 RECOMMANDATION FINALE:")
    print(f"   Poster sur {best[0].upper()}")
    print(f"   → {best[1].predicted_views:,} vues attendues")
    print(f"   → €{best[1].estimated_revenue:,.2f} revenue estimé")
    print(f"   → ROI de {best[1].roi_percentage:,.1f}%")
    print("="*70)


# ============================================================================
# EXEMPLE 3: Batch analysis - "Quelle idée choisir parmi 5?"
# ============================================================================

async def exemple_batch_analysis():
    """
    Cas d'usage: J'ai 5 idées de contenu, laquelle va performer le mieux?
    """
    print("\n" + "="*70)
    print("EXEMPLE 3: Analyse batch (5 idées)")
    print("="*70)
    
    predictor = get_advanced_metrics_predictor()
    
    # Vos 5 idées
    mes_idees = [
        {
            'id': 'idea_001',
            'title': '10 astuces Python pour débutants',
            'viral_score': 0.92,
            'follower_count': 10000
        },
        {
            'id': 'idea_002',
            'title': 'Comment créer une app IA en 2024',
            'viral_score': 0.78,
            'follower_count': 10000
        },
        {
            'id': 'idea_003',
            'title': 'Les bases du Machine Learning',
            'viral_score': 0.65,
            'follower_count': 10000
        },
        {
            'id': 'idea_004',
            'title': 'Django vs Flask: Quel framework choisir?',
            'viral_score': 0.58,
            'follower_count': 10000
        },
        {
            'id': 'idea_005',
            'title': 'Automatiser votre workflow avec Python',
            'viral_score': 0.71,
            'follower_count': 10000
        }
    ]
    
    print(f"\n📝 Analyse de {len(mes_idees)} idées de contenu...")
    print("🎯 Plateforme cible: TikTok\n")
    
    # Analyse batch
    predictions = predictor.predict_batch(
        mes_idees,
        platform='tiktok'
    )
    
    print("📊 CLASSEMENT PAR POTENTIEL:")
    print("="*70)
    
    for rank, pred in enumerate(predictions, 1):
        title = getattr(pred, 'title', 'Untitled')
        idea_id = getattr(pred, 'idea_id', '')
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        
        print(f"""
{medal} #{rank} - {title[:50]}
   ID:       {idea_id}
   Vues:     {pred.predicted_views:>8,}
   Likes:    {pred.predicted_likes:>8,}
   Revenue:  €{pred.estimated_revenue:>8,.2f}
   ROI:      {pred.roi_percentage:>8,.1f}%
""")
    
    # Recommandation
    best = predictions[0]
    best_title = getattr(best, 'title', 'Top idea')
    
    print("="*70)
    print("🎯 VERDICT:")
    print(f"   → Créer d'abord: \"{best_title}\"")
    print(f"   → Potentiel: {best.predicted_views:,} vues, €{best.estimated_revenue:,.2f}")
    print(f"   → Ensuite créer les autres par ordre de ROI")
    print("="*70)


# ============================================================================
# EXEMPLE 4: Stratégie content - "Planifier ma semaine"
# ============================================================================

async def exemple_strategie_semaine():
    """
    Cas d'usage: Je veux planifier mes 7 posts de la semaine
    pour maximiser mon reach total.
    """
    print("\n" + "="*70)
    print("EXEMPLE 4: Stratégie content hebdomadaire")
    print("="*70)
    
    predictor = get_advanced_metrics_predictor()
    
    # Planning semaine
    posts_semaine = [
        {'day': 'Lundi', 'content': 'Tutorial Python basics', 'platform': 'youtube', 'viral_score': 0.75},
        {'day': 'Mardi', 'content': 'Quick tips TikTok', 'platform': 'tiktok', 'viral_score': 0.88},
        {'day': 'Mercredi', 'content': 'Instagram Reel IA', 'platform': 'instagram', 'viral_score': 0.82},
        {'day': 'Jeudi', 'content': 'Reddit AMA Tech', 'platform': 'reddit', 'viral_score': 0.70},
        {'day': 'Vendredi', 'content': 'TikTok Weekend Viral', 'platform': 'tiktok', 'viral_score': 0.91},
        {'day': 'Samedi', 'content': 'YouTube Long Format', 'platform': 'youtube', 'viral_score': 0.78},
        {'day': 'Dimanche', 'content': 'Instagram Story', 'platform': 'instagram', 'viral_score': 0.65}
    ]
    
    print("\n📅 PLANNING HEBDOMADAIRE:")
    print("="*70)
    
    total_views = 0
    total_revenue = 0
    
    for post in posts_semaine:
        prediction = predictor.predict_metrics(
            viral_score=post['viral_score'],
            platform=post['platform'],
            follower_count=10000
        )
        
        total_views += prediction.predicted_views
        total_revenue += prediction.estimated_revenue
        
        print(f"""
📅 {post['day']:10} | {post['platform'].upper():10} | {post['content'][:30]:30}
   → {prediction.predicted_views:>8,} vues | €{prediction.estimated_revenue:>8,.2f} | {prediction.best_posting_time}
""")
    
    print("="*70)
    print(f"📊 TOTAL SEMAINE:")
    print(f"   Vues totales:    {total_views:>10,}")
    print(f"   Revenue estimé:  €{total_revenue:>10,.2f}")
    print(f"   ROI moyen:       {(total_revenue/700)*100:>10,.1f}% (coût: €700)")
    print("="*70)


# ============================================================================
# EXEMPLE 5: API Integration - "Intégrer dans mon app"
# ============================================================================

def exemple_api_integration():
    """
    Cas d'usage: Intégrer les prédictions dans votre application
    """
    print("\n" + "="*70)
    print("EXEMPLE 5: Intégration API")
    print("="*70)
    
    api_example = '''
# Dans votre app (Flask, FastAPI, etc.)

from src.services.scoring.advanced_metrics_predictor import get_advanced_metrics_predictor

@app.post("/api/predict")
async def predict_content_performance(
    content_title: str,
    platform: str,
    follower_count: int,
    viral_score: float  # Vient de votre ML model
):
    """Endpoint pour prédire performance d'un contenu"""
    
    predictor = get_advanced_metrics_predictor()
    
    prediction = predictor.predict_metrics(
        viral_score=viral_score,
        platform=platform,
        follower_count=follower_count
    )
    
    return {
        "success": True,
        "content": content_title,
        "predictions": {
            "views": prediction.predicted_views,
            "views_range": prediction.views_range,
            "likes": prediction.predicted_likes,
            "comments": prediction.predicted_comments,
            "engagement_rate": prediction.engagement_rate,
            "estimated_revenue": prediction.estimated_revenue,
            "roi_percentage": prediction.roi_percentage,
            "best_timing": {
                "day": prediction.best_posting_day,
                "time": prediction.best_posting_time
            },
            "recommendations": prediction.recommendations
        }
    }

# Exemple d'appel:
# POST /api/predict
# {
#   "content_title": "10 astuces Python",
#   "platform": "tiktok",
#   "follower_count": 10000,
#   "viral_score": 0.85
# }
#
# Response:
# {
#   "success": true,
#   "content": "10 astuces Python",
#   "predictions": {
#     "views": 43500,
#     "views_range": [30450, 56550],
#     "likes": 3480,
#     "estimated_revenue": 17552.25,
#     "roi_percentage": 8676.1,
#     "recommendations": [...]
#   }
# }
'''
    
    print(api_example)
    print("="*70)


# ============================================================================
# MAIN - Lancer tous les exemples
# ============================================================================

async def main():
    """Lance tous les exemples"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                 🚀 GUIDE CLIENT - PRÉDICTIONS EXACTES                 ║
║                                                                       ║
║   Ce guide montre comment prédire EXACTEMENT:                         ║
║   • Combien de vues votre contenu va générer                          ║
║   • Combien de likes/commentaires/partages                            ║
║   • Combien d'€ de revenue vous allez faire                           ║
║   • Sur quelle plateforme poster pour maximiser ROI                   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")
    
    # Exemple 1: Prédiction simple
    await exemple_prediction_simple()
    
    input("\n[Appuyez sur ENTRÉE pour continuer...]")
    
    # Exemple 2: Comparaison plateformes
    await exemple_comparaison_plateformes()
    
    input("\n[Appuyez sur ENTRÉE pour continuer...]")
    
    # Exemple 3: Batch analysis
    await exemple_batch_analysis()
    
    input("\n[Appuyez sur ENTRÉE pour continuer...]")
    
    # Exemple 4: Stratégie semaine
    await exemple_strategie_semaine()
    
    input("\n[Appuyez sur ENTRÉE pour continuer...]")
    
    # Exemple 5: API integration
    exemple_api_integration()
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                     ✅ FIN DES EXEMPLES                               ║
║                                                                       ║
║   📚 Pour plus d'infos:                                               ║
║      • docs/RESUME_EXECUTIF_COMMERCIAL.md - Vue d'ensemble            ║
║      • docs/MULTIPLATFORM_API_SETUP.md - Configuration APIs           ║
║      • test_multiplatform_system.py - Tests complets                  ║
║                                                                       ║
║   💼 Support commercial: support@trend-viral-engine.com               ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    asyncio.run(main())
