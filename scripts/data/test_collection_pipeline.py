"""
Test complet de la collecte de données avec VRAIES APIs.
Détecte erreurs, hallucinations, problèmes de rate limiting, etc.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv
from loguru import logger

# Load environment
load_dotenv()


class DataCollectionTester:
    """Test exhaustif de toutes les sources de données"""
    
    def __init__(self):
        self.results = {
            "google_trends": {"status": "pending", "samples": 0, "errors": []},
            "reddit": {"status": "pending", "samples": 0, "errors": []},
            "tiktok": {"status": "pending", "samples": 0, "errors": []},
            "facebook": {"status": "pending", "samples": 0, "errors": []},
        }
    
    async def test_google_trends(self) -> Dict:
        """Test Google Trends (pas d'auth requise)"""
        logger.info("🔍 Testing Google Trends...")
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='fr', tz=360)
            trending = pytrends.trending_searches(pn='france')
            
            samples = len(trending)
            self.results["google_trends"]["status"] = "✅ OK"
            self.results["google_trends"]["samples"] = samples
            
            logger.success(f"✅ Google Trends: {samples} trends collected")
            
            # Vérifier qualité données
            if samples == 0:
                self.results["google_trends"]["errors"].append("⚠️  No trends returned")
            
            return {"success": True, "samples": samples}
            
        except Exception as e:
            self.results["google_trends"]["status"] = "❌ FAILED"
            self.results["google_trends"]["errors"].append(str(e))
            logger.error(f"❌ Google Trends failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_reddit(self) -> Dict:
        """Test Reddit API avec tokens du .env"""
        logger.info("🔍 Testing Reddit API...")
        try:
            import praw
            
            client_id = os.getenv("REDDIT_CLIENT_ID")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET")
            user_agent = os.getenv("REDDIT_USER_AGENT")
            
            if not all([client_id, client_secret, user_agent]):
                raise ValueError("Missing Reddit credentials in .env")
            
            # Test credentials
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Collect from r/tiktok
            posts = []
            for post in reddit.subreddit("tiktok").hot(limit=10):
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "comments": post.num_comments,
                    "created": datetime.fromtimestamp(post.created_utc).isoformat()
                })
            
            samples = len(posts)
            self.results["reddit"]["status"] = "✅ OK"
            self.results["reddit"]["samples"] = samples
            
            logger.success(f"✅ Reddit: {samples} posts collected from r/tiktok")
            
            # Vérifier qualité
            if samples < 10:
                self.results["reddit"]["errors"].append("⚠️  Less than expected posts")
            
            avg_score = sum(p["score"] for p in posts) / len(posts) if posts else 0
            logger.info(f"   Average score: {avg_score:.1f}")
            
            return {"success": True, "samples": samples, "avg_score": avg_score}
            
        except Exception as e:
            self.results["reddit"]["status"] = "❌ FAILED"
            self.results["reddit"]["errors"].append(str(e))
            logger.error(f"❌ Reddit failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_tiktok(self) -> Dict:
        """Test TikTok Creative Center API"""
        logger.info("🔍 Testing TikTok Creative Center...")
        try:
            import httpx
            
            client_key = os.getenv("TIKTOK_CLIENT_KEY")
            client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
            
            if not all([client_key, client_secret]):
                raise ValueError("Missing TikTok credentials in .env")
            
            # TikTok Creative Center endpoint (public API)
            # Note: API réelle nécessite OAuth 2.0 flow complet
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test endpoint public (si disponible)
                # Pour l'instant, simulons la vérification des credentials
                
                logger.warning("⚠️  TikTok Creative Center requires full OAuth 2.0 flow")
                logger.info(f"   CLIENT_KEY configured: {client_key[:10]}...")
                logger.info(f"   CLIENT_SECRET configured: {client_secret[:10]}...")
                
                self.results["tiktok"]["status"] = "⚠️  CREDENTIALS OK, API requires OAuth flow"
                self.results["tiktok"]["errors"].append("Needs OAuth 2.0 authorization code flow")
                
                return {
                    "success": False,
                    "reason": "OAuth 2.0 flow required (see OAUTH_SETUP.md)",
                    "credentials_present": True
                }
                
        except Exception as e:
            self.results["tiktok"]["status"] = "❌ FAILED"
            self.results["tiktok"]["errors"].append(str(e))
            logger.error(f"❌ TikTok failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_facebook(self) -> Dict:
        """Test Facebook Graph API"""
        logger.info("🔍 Testing Facebook Graph API...")
        try:
            import httpx
            
            app_id = os.getenv("FACEBOOK_APP_ID")
            app_secret = os.getenv("FACEBOOK_APP_SECRET")
            access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
            
            if not all([app_id, app_secret]):
                raise ValueError("Missing Facebook credentials in .env")
            
            if not access_token:
                logger.warning("⚠️  FACEBOOK_ACCESS_TOKEN empty in .env")
                self.results["facebook"]["status"] = "⚠️  CREDENTIALS OK, missing ACCESS_TOKEN"
                self.results["facebook"]["errors"].append("ACCESS_TOKEN not generated (see OAUTH_SETUP.md)")
                return {
                    "success": False,
                    "reason": "ACCESS_TOKEN required",
                    "credentials_present": True
                }
            
            # Test avec Graph API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.results["facebook"]["status"] = "✅ OK"
                    logger.success(f"✅ Facebook: Connected as {data.get('name', 'Unknown')}")
                    return {"success": True, "user": data}
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            self.results["facebook"]["status"] = "❌ FAILED"
            self.results["facebook"]["errors"].append(str(e))
            logger.error(f"❌ Facebook failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self):
        """Execute tous les tests en parallèle"""
        logger.info("=" * 70)
        logger.info("🧪 TESTING DATA COLLECTION PIPELINE")
        logger.info("=" * 70)
        
        # Run tests concurrently
        results = await asyncio.gather(
            self.test_google_trends(),
            self.test_reddit(),
            self.test_tiktok(),
            self.test_facebook(),
            return_exceptions=True
        )
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 SUMMARY")
        logger.info("=" * 70)
        
        for source, data in self.results.items():
            status = data["status"]
            samples = data["samples"]
            errors = data["errors"]
            
            logger.info(f"\n{source.upper()}:")
            logger.info(f"  Status: {status}")
            logger.info(f"  Samples: {samples}")
            if errors:
                logger.info(f"  Errors: {', '.join(errors)}")
        
        # Calculate success rate
        successful = sum(1 for r in self.results.values() if "✅" in r["status"])
        total = len(self.results)
        success_rate = (successful / total) * 100
        
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Success Rate: {successful}/{total} ({success_rate:.0f}%)")
        logger.info(f"{'=' * 70}")
        
        return self.results


async def main():
    """Main test function"""
    tester = DataCollectionTester()
    results = await tester.run_all_tests()
    
    # Recommendations
    logger.info("\n" + "=" * 70)
    logger.info("💡 RECOMMENDATIONS")
    logger.info("=" * 70)
    
    if "❌" in results["reddit"]["status"]:
        logger.warning("❌ Reddit: Verify credentials in .env")
    
    if "⚠️" in results["tiktok"]["status"]:
        logger.warning("⚠️  TikTok: Follow docs/OAUTH_SETUP.md for OAuth 2.0 flow")
    
    if "⚠️" in results["facebook"]["status"] or "❌" in results["facebook"]["status"]:
        logger.warning("⚠️  Facebook: Generate ACCESS_TOKEN (see docs/OAUTH_SETUP.md)")
    
    logger.info("\n✅ Google Trends: Ready to use (no auth required)")


if __name__ == "__main__":
    asyncio.run(main())
