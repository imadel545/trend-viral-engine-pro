#!/usr/bin/env python3
"""
COLLECTE MASSIVE - 5000 posts Reddit avec retry et anti-ban
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from loguru import logger
from src.services.ingestion import get_ingestion_service


async def collect_massive(target: int = 5000):
    """Collecte MASSIVE avec retry."""
    logger.info(f"🔥 OBJECTIF: {target} posts Reddit")
    
    service = get_ingestion_service()
    all_data = []
    attempts = 0
    max_attempts = 50
    
    while len(all_data) < target and attempts < max_attempts:
        attempts += 1
        
        try:
            results = await service.run_collection(sources=['reddit'])
            reddit_file = results.get('reddit')
            
            if reddit_file and reddit_file.exists():
                df = pd.read_parquet(reddit_file)
                all_data.append(df)
                
                total = sum(len(d) for d in all_data)
                logger.success(f"✅ Batch {attempts}: +{len(df)} posts (TOTAL: {total}/{target})")
            
            if total >= target:
                break
                
            await asyncio.sleep(3)  # Anti-ban
            
        except Exception as e:
            logger.warning(f"Batch {attempts} failed: {e}")
            await asyncio.sleep(5)
            continue
    
    # Fusionner et nettoyer
    df_all = pd.concat(all_data, ignore_index=True)
    df_all = df_all.drop_duplicates(subset=['post_id'] if 'post_id' in df_all.columns else None)
    
    # Labels intelligents (top 15% = viral pour balance)
    if 'score' in df_all.columns:
        threshold = df_all['score'].quantile(0.85)
        df_all['is_breakout'] = (df_all['score'] > threshold).astype(int)
        
        viral = df_all['is_breakout'].sum()
        logger.success(f"🎯 FINAL: {len(df_all)} posts ({viral} viraux = {100*viral/len(df_all):.1f}%)")
    
    # Sauvegarder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = Path(f'data/raw/reddit_massive_{len(df_all)}_{timestamp}.parquet')
    df_all.to_parquet(output)
    logger.success(f"💾 {output}")
    
    return output


if __name__ == "__main__":
    asyncio.run(collect_massive(5000))
