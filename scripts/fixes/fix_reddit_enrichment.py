"""
🔧 FIX CRITIQUE - Enrichissement données Reddit

PROBLÈME: 80% des posts Reddit ont text=NaN (inutilisables)
SOLUTION: Enrichir avec title + selftext + top comments

Ce patch modifie IngestionService pour collecter du texte exploitable.

Usage:
    python scripts/fixes/fix_reddit_enrichment.py --apply
    
Puis relancer collection:
    python test_real_viral_production.py
"""

import argparse
from pathlib import Path

from loguru import logger


REDDIT_ENRICHMENT_CODE = '''
    async def _enrich_reddit_text(self, submission) -> str:
        """
        Enrichir texte Reddit avec title + selftext + comments.
        
        Résout le problème des 80% de posts avec text=NaN.
        """
        parts = []
        
        try:
            # 1. Title (toujours présent) - PRIORITAIRE
            if hasattr(submission, 'title') and submission.title:
                parts.append(submission.title)
            
            # 2. Selftext si présent (description du post)
            if hasattr(submission, 'selftext') and submission.selftext:
                # Limiter à 500 caractères pour éviter bloat
                selftext_clean = submission.selftext.strip()
                if len(selftext_clean) > 20:  # Ignorer selftext trop courts
                    parts.append(selftext_clean[:500])
            
            # 3. Top 5 comments (source riche d'info)
            if hasattr(submission, 'comments'):
                try:
                    # Expand comments (limite 0 = ne pas aller trop profond)
                    submission.comments.replace_more(limit=0)
                    
                    # Trier par score (meilleurs comments en premier)
                    all_comments = submission.comments.list()
                    top_comments = sorted(
                        [c for c in all_comments if hasattr(c, 'body') and hasattr(c, 'score')],
                        key=lambda c: c.score,
                        reverse=True
                    )[:5]
                    
                    for comment in top_comments:
                        if hasattr(comment, 'body'):
                            comment_text = comment.body.strip()
                            # Ignorer comments trop courts ou deleted
                            if len(comment_text) > 20 and comment_text not in ['[deleted]', '[removed]']:
                                parts.append(comment_text[:200])  # Max 200 chars par comment
                
                except Exception as e:
                    self.logger.debug(f"Could not fetch comments: {e}")
        
        except Exception as e:
            self.logger.warning(f"Error enriching Reddit text: {e}")
        
        # Joindre toutes les parties avec séparateur
        full_text = " | ".join(parts) if parts else ""
        
        return full_text
'''


REDDIT_COLLECT_MODIFICATION = '''
        # Dans la boucle de collection des posts Reddit:
        # AVANT (ligne ~500):
        # item = {
        #     "topic": submission.title,
        #     "text": submission.selftext,  # ← Souvent vide !
        #     ...
        # }
        
        # APRÈS (à modifier):
        item = {
            "topic": submission.title,
            "text": await self._enrich_reddit_text(submission),  # ← NOUVEAU
            "url": f"https://reddit.com{submission.permalink}",
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "subreddit": submission.subreddit.display_name,
        }
'''


def apply_fix():
    """Applique le fix à IngestionService."""
    
    logger.info("🔧 Application du fix Reddit enrichment...")
    
    service_file = Path("src/services/ingestion/service.py")
    
    if not service_file.exists():
        logger.error(f"❌ Fichier non trouvé: {service_file}")
        return False
    
    # Lire contenu actuel
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà patché
    if '_enrich_reddit_text' in content:
        logger.warning("⚠️ Le fix semble déjà appliqué (méthode _enrich_reddit_text existe)")
        return True
    
    # Trouver la classe RedditSource
    if 'class RedditSource(DataSource):' not in content:
        logger.error("❌ Classe RedditSource non trouvée")
        return False
    
    # Position d'insertion: après __init__ de RedditSource
    # Chercher la ligne après "self.client = None" ou similaire
    
    logger.info("📝 Modification du fichier...")
    
    # Strategy: Insérer la méthode _enrich_reddit_text juste avant la méthode collect
    insert_marker = '    async def collect(self, subreddits:'
    
    if insert_marker not in content:
        logger.error("❌ Marker d'insertion non trouvé")
        return False
    
    # Insérer la nouvelle méthode
    content = content.replace(
        insert_marker,
        REDDIT_ENRICHMENT_CODE + '\n\n' + insert_marker
    )
    
    # Maintenant modifier l'appel dans collect() pour utiliser la nouvelle méthode
    # Chercher: "text": submission.selftext
    # Remplacer: "text": await self._enrich_reddit_text(submission)
    
    old_text_assignment = '"text": submission.selftext'
    new_text_assignment = '"text": await self._enrich_reddit_text(submission)'
    
    if old_text_assignment in content:
        content = content.replace(old_text_assignment, new_text_assignment)
        logger.info("✓ Remplacement text assignment effectué")
    else:
        logger.warning("⚠️ Assignment exact non trouvé, tentative pattern matching...")
        # Pattern plus flexible
        import re
        content = re.sub(
            r'"text":\s*submission\.selftext',
            '"text": await self._enrich_reddit_text(submission)',
            content
        )
    
    # Backup original
    backup_file = service_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        # Lire à nouveau l'original pour backup
        with open(service_file, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    
    logger.info(f"💾 Backup créé: {backup_file}")
    
    # Écrire version modifiée
    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ Fix appliqué avec succès: {service_file}")
    logger.info("")
    logger.info("📋 PROCHAINES ÉTAPES:")
    logger.info("  1. Vérifiez le fichier manuellement (optionnel)")
    logger.info("  2. Lancez une nouvelle collection:")
    logger.info("     python test_real_viral_production.py")
    logger.info("  3. Vérifiez que les données ont maintenant du texte:")
    logger.info("     python -c \"import pandas as pd; df=pd.read_parquet('data/raw/reddit_enhanced_*.parquet', engine='pyarrow'); print(df['text'].head())\"")
    logger.info("")
    
    return True


def show_preview():
    """Affiche un preview du code à appliquer."""
    
    print("=" * 80)
    print("🔍 PREVIEW DU FIX REDDIT ENRICHMENT")
    print("=" * 80)
    print()
    print("Nouvelle méthode à ajouter:")
    print("─" * 80)
    print(REDDIT_ENRICHMENT_CODE)
    print()
    print("Modification de la collection:")
    print("─" * 80)
    print(REDDIT_COLLECT_MODIFICATION)
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Fix Reddit enrichment")
    parser.add_argument(
        '--apply',
        action='store_true',
        help="Appliquer le fix immédiatement"
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help="Afficher preview sans appliquer"
    )
    
    args = parser.parse_args()
    
    if args.preview or (not args.apply):
        show_preview()
        
        if not args.apply:
            print("\n💡 Pour appliquer le fix, lancez:")
            print("   python scripts/fixes/fix_reddit_enrichment.py --apply")
        
        return 0
    
    if args.apply:
        success = apply_fix()
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())
