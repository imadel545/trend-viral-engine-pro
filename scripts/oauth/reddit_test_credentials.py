"""
Reddit OAuth: Simple test and credential validator

Usage:
    python scripts/oauth/reddit_test_credentials.py

This script:
1. Tests your Reddit credentials from .env
2. Fetches a small sample of posts
3. Validates authentication works
4. Provides troubleshooting tips

Author: GitHub Copilot (autonomous mode)
Date: 5 novembre 2025
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


async def test_reddit_credentials():
    """
    Test Reddit credentials and fetch sample data.
    
    Returns:
        bool: True if credentials work, False otherwise
    """
    
    logger.info("🧪 Testing Reddit credentials...")
    logger.info(f"Client ID: {settings.reddit_client_id[:10]}...")
    logger.info(f"Client Secret: {settings.reddit_client_secret[:10]}...")
    logger.info(f"User Agent: {settings.reddit_user_agent}")
    
    # Import Reddit source
    try:
        from src.services.ingestion.advanced_sources import EnhancedRedditSource
        use_async = True
        logger.info("Using EnhancedRedditSource (asyncpraw)")
    except ImportError:
        logger.warning("EnhancedRedditSource not available, falling back to sync Reddit")
        from src.services.ingestion.service import RedditSource
        use_async = False
    
    try:
        if use_async:
            # Test with async Reddit
            reddit = EnhancedRedditSource()
            
            logger.info("📊 Fetching sample posts from r/python...")
            posts = await reddit.collect(
                subreddits=["python"],
                sort="hot",
                limit=5
            )
            
            if posts:
                print("\n" + "=" * 70)
                print(f"✅ Reddit Authentication SUCCESS!")
                print("=" * 70)
                print(f"\nCollected {len(posts)} posts from r/python:")
                print("-" * 70)
                
                for i, post in enumerate(posts[:3], 1):
                    title = post.get("title", "No title")[:60]
                    score = post.get("score", 0)
                    comments = post.get("num_comments", 0)
                    subreddit = post.get("subreddit", "unknown")
                    
                    print(f"\n{i}. [{score}↑ {comments}💬] {title}...")
                    print(f"   r/{subreddit}")
                
                print("\n" + "=" * 70)
                print("✅ Your Reddit credentials are VALID!")
                print("=" * 70)
                print("\n📝 Current .env configuration:")
                print(f'REDDIT_CLIENT_ID="{settings.reddit_client_id}"')
                print(f'REDDIT_CLIENT_SECRET="{settings.reddit_client_secret}"')
                print(f'REDDIT_USER_AGENT="{settings.reddit_user_agent}"')
                print("\n" + "=" * 70 + "\n")
                
                # Close client
                await reddit.close()
                
                return True
            else:
                logger.warning("⚠️  Authentication succeeded but no posts returned")
                await reddit.close()
                return True
                
        else:
            # Test with sync Reddit
            reddit = RedditSource()
            
            logger.info("📊 Fetching sample posts from r/python...")
            posts = await reddit.collect(subreddits=["python"], limit=5)
            
            if posts:
                print("\n" + "=" * 70)
                print(f"✅ Reddit Authentication SUCCESS!")
                print("=" * 70)
                print(f"\nCollected {len(posts)} posts")
                print("=" * 70 + "\n")
                return True
            else:
                logger.warning("⚠️  Authentication succeeded but no posts returned")
                return True
                
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Reddit Authentication FAILED!")
        print("=" * 70)
        logger.error(f"Error: {e}")
        
        # Provide troubleshooting
        print("\n" + "-" * 70)
        print("🔧 TROUBLESHOOTING")
        print("-" * 70)
        
        error_msg = str(e).lower()
        
        if "401" in error_msg or "unauthorized" in error_msg:
            print("\n❌ 401 Unauthorized - Invalid credentials")
            print("\nPossible fixes:")
            print("1. Verify credentials are correct (no extra spaces)")
            print("2. Make sure app type is 'script' (not 'web app')")
            print("3. Recreate the Reddit app:")
            print("   https://www.reddit.com/prefs/apps")
            print("\n4. Required fields:")
            print("   - name: TrendViralEngine")
            print("   - App type: ⚫ script")
            print("   - redirect uri: http://localhost:8080")
            
        elif "403" in error_msg or "forbidden" in error_msg:
            print("\n❌ 403 Forbidden - Permissions issue")
            print("\nPossible fixes:")
            print("1. Check your Reddit account is in good standing")
            print("2. Verify the app hasn't been suspended")
            print("3. Make sure user_agent is unique and descriptive")
            
        elif "rate" in error_msg or "429" in error_msg:
            print("\n❌ Rate Limit Exceeded")
            print("\nSolution: Wait a few minutes and try again")
            
        else:
            print(f"\n❌ Unknown error: {e}")
            print("\nGeneral troubleshooting:")
            print("1. Check .env file exists and is readable")
            print("2. Verify no typos in .env variable names")
            print("3. Restart your terminal/IDE to reload .env")
            print("4. Check Reddit API status: https://www.redditstatus.com/")
        
        print("\n" + "-" * 70)
        print("📝 Current .env values:")
        print("-" * 70)
        print(f"REDDIT_CLIENT_ID={settings.reddit_client_id[:20]}...")
        print(f"REDDIT_CLIENT_SECRET={settings.reddit_client_secret[:20]}...")
        print(f"REDDIT_USER_AGENT={settings.reddit_user_agent}")
        print("\n" + "=" * 70 + "\n")
        
        return False


def print_setup_guide():
    """Print Reddit app setup guide."""
    print("\n" + "=" * 70)
    print("🟠 Reddit App Setup Guide")
    print("=" * 70)
    print("\nIf you need to create or recreate your Reddit app:")
    print("\n1. Go to: https://www.reddit.com/prefs/apps")
    print("\n2. Scroll down and click 'create another app' or 'create app'")
    print("\n3. Fill in the form:")
    print("   - name: TrendViralEngine")
    print("   - App type: ⚫ script (IMPORTANT!)")
    print("   - description: Data collection for trend analysis")
    print("   - about url: (leave blank)")
    print("   - redirect uri: http://localhost:8080")
    print("\n4. Click 'create app'")
    print("\n5. Find your credentials:")
    print("   ┌─────────────────────────────────────┐")
    print("   │ TrendViralEngine                    │")
    print("   │ personal use script                 │")
    print("   │ ───────────────────────────────     │")
    print("   │ [14 characters]  ← CLIENT_ID        │")
    print("   │ secret: [27 chars]   ← SECRET       │")
    print("   └─────────────────────────────────────┘")
    print("\n6. Copy to .env:")
    print('   REDDIT_CLIENT_ID="your_14_char_id"')
    print('   REDDIT_CLIENT_SECRET="your_27_char_secret"')
    print('   REDDIT_USER_AGENT="TrendViralEngine/1.0 by /u/YOUR_USERNAME"')
    print("\n7. Replace YOUR_USERNAME with your actual Reddit username")
    print("\n" + "=" * 70 + "\n")


async def main():
    """CLI entry point."""
    
    # Check if credentials are configured
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        logger.error("❌ Reddit credentials not configured in .env")
        print_setup_guide()
        sys.exit(1)
    
    # Test credentials
    success = await test_reddit_credentials()
    
    if success:
        logger.info("✅ All checks passed!")
        print("🎉 You can now use Reddit for data collection!")
        print("\nNext steps:")
        print("1. Run full collection test:")
        print("   python scripts/data/test_collection_pipeline.py")
        print("\n2. Or collect real data:")
        print("   python -m src.services.ingestion.advanced_collector --target 100")
        sys.exit(0)
    else:
        logger.error("❌ Reddit credentials validation failed")
        print("\n💡 Need help setting up? Run:")
        print("   python scripts/oauth/reddit_test_credentials.py --help")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_setup_guide()
        sys.exit(0)
    
    asyncio.run(main())
