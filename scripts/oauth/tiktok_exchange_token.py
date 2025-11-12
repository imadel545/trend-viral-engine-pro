"""
TikTok OAuth: Exchange authorization code for access token

Usage:
    python scripts/oauth/tiktok_exchange_token.py YOUR_AUTH_CODE

Where to get auth code:
    1. Build URL with your client_key:
       https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_KEY&scope=research.data.basic&response_type=code&redirect_uri=http://localhost:8888/callback&state=random123
    
    2. Open in browser, authorize app
    
    3. Copy code from redirect URL:
       http://localhost:8888/callback?code=CODE_HERE&state=random123
    
    4. Run this script with the code (within 10 minutes)

Author: GitHub Copilot (autonomous mode)
Date: 5 novembre 2025
"""

import asyncio
import sys
from pathlib import Path

import aiohttp
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


async def exchange_code(auth_code: str):
    """
    Exchange TikTok authorization code for access token.
    
    Args:
        auth_code: Authorization code from OAuth redirect
    
    Returns:
        dict with access_token, refresh_token, expires_in
    """
    
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    
    data = {
        "client_key": settings.tiktok_client_key,
        "client_secret": settings.tiktok_client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:8888/callback"
    }
    
    logger.info(f"🔄 Exchanging authorization code for access token...")
    logger.debug(f"Client Key: {settings.tiktok_client_key[:10]}...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            response_text = await response.text()
            
            if response.status == 200:
                result = await response.json()
                
                # Extract tokens
                access_token = result.get("data", {}).get("access_token")
                refresh_token = result.get("data", {}).get("refresh_token")
                expires_in = result.get("data", {}).get("expires_in", 86400)
                
                if not access_token:
                    logger.error(f"❌ No access_token in response: {result}")
                    return None
                
                # Success display
                print("\n" + "=" * 70)
                print("✅ TikTok Access Token obtenu avec succès !")
                print("=" * 70)
                print(f"\nACCESS_TOKEN: {access_token}")
                if refresh_token:
                    print(f"REFRESH_TOKEN: {refresh_token}")
                print(f"\nExpire dans: {expires_in} secondes ({expires_in//3600}h)")
                print("\n" + "-" * 70)
                print("📝 Ajoutez ces lignes dans votre .env :")
                print("-" * 70)
                print(f'TIKTOK_ACCESS_TOKEN="{access_token}"')
                if refresh_token:
                    print(f'TIKTOK_REFRESH_TOKEN="{refresh_token}"')
                print("\n" + "=" * 70)
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": expires_in
                }
                
            else:
                logger.error(f"❌ TikTok API Error (HTTP {response.status})")
                logger.error(f"Response: {response_text}")
                
                # Parse error details if JSON
                try:
                    error_data = await response.json()
                    if "error" in error_data:
                        logger.error(f"Error: {error_data['error']}")
                    if "error_description" in error_data:
                        logger.error(f"Description: {error_data['error_description']}")
                except:
                    pass
                
                return None


def print_help():
    """Print usage instructions."""
    print("\n" + "=" * 70)
    print("🎵 TikTok OAuth Token Exchange")
    print("=" * 70)
    print("\nUsage:")
    print("    python scripts/oauth/tiktok_exchange_token.py YOUR_AUTH_CODE")
    print("\nSteps to get authorization code:")
    print("\n1. Build authorization URL (replace YOUR_CLIENT_KEY):")
    print("   https://www.tiktok.com/v2/auth/authorize/?\\")
    print("     client_key=YOUR_CLIENT_KEY&\\")
    print("     scope=research.data.basic&\\")
    print("     response_type=code&\\")
    print("     redirect_uri=http://localhost:8888/callback&\\")
    print("     state=random123")
    
    print(f"\n2. Your client_key: {settings.tiktok_client_key[:15]}...")
    print(f"\n   Full URL for you:")
    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={settings.tiktok_client_key}"
        f"&scope=research.data.basic"
        f"&response_type=code"
        f"&redirect_uri=http://localhost:8888/callback"
        f"&state=random123"
    )
    print(f"   {auth_url}")
    
    print("\n3. Open URL in browser and authorize")
    print("\n4. Copy code from redirect:")
    print("   http://localhost:8888/callback?code=CODE_HERE&state=random123")
    print("                                       ^^^^^^^^^^")
    print("\n5. Run this script with the code:")
    print("   python scripts/oauth/tiktok_exchange_token.py CODE_HERE")
    print("\n⚠️  Code expires in 10 minutes!")
    print("=" * 70 + "\n")


async def main():
    """CLI entry point."""
    
    # Check arguments
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    auth_code = sys.argv[1]
    
    # Validate code format (basic check)
    if len(auth_code) < 10:
        logger.error("❌ Authorization code seems too short. Did you copy it correctly?")
        sys.exit(1)
    
    # Exchange
    result = await exchange_code(auth_code)
    
    if result:
        logger.info("✅ Token exchange successful!")
        
        # Test the token
        print("\n" + "-" * 70)
        print("🧪 Testing token with TikTok API...")
        print("-" * 70)
        
        try:
            from src.services.ingestion.advanced_sources import TikTokCreativeCenterSource
            
            tiktok = TikTokCreativeCenterSource()
            tiktok.access_token = result["access_token"]
            
            # Try a simple request
            test_data = await tiktok.collect(regions=["US"], content_types=["hashtag"], max_results=5)
            
            if test_data:
                logger.info(f"✅ Token works! Collected {len(test_data)} sample(s)")
            else:
                logger.warning("⚠️  Token valid but no data returned (may need additional permissions)")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not test token: {e}")
            logger.info("Token was obtained successfully - test it manually later")
        
        sys.exit(0)
    else:
        logger.error("❌ Token exchange failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
