"""
Facebook OAuth: Exchange short-lived token for long-lived token (60 days)

Usage:
    python scripts/oauth/facebook_long_lived_token.py SHORT_LIVED_TOKEN

Where to get short-lived token:
    1. Go to: https://developers.facebook.com/tools/explorer/
    2. Select your app
    3. Click "Get Token" → "Get User Access Token"
    4. Select permissions: pages_read_engagement, pages_show_list, public_profile
    5. Click "Generate Access Token"
    6. Copy the token (starts with EAAD...)
    7. Run this script with the token

Author: GitHub Copilot (autonomous mode)
Date: 5 novembre 2025
"""

import sys
from pathlib import Path

import httpx
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


def exchange_token(short_token: str):
    """
    Exchange Facebook short-lived token for long-lived token (60 days).
    
    Args:
        short_token: Short-lived user access token from Graph API Explorer
    
    Returns:
        dict with access_token and expires_in
    """
    
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.facebook_app_id,
        "client_secret": settings.facebook_app_secret,
        "fb_exchange_token": short_token
    }
    
    logger.info("🔄 Exchanging short-lived token for long-lived token...")
    logger.debug(f"App ID: {settings.facebook_app_id}")
    
    try:
        response = httpx.get(url, params=params, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            long_token = data.get("access_token")
            expires_in = data.get("expires_in", 5184000)  # 60 days default
            token_type = data.get("token_type", "bearer")
            
            if not long_token:
                logger.error(f"❌ No access_token in response: {data}")
                return None
            
            # Success display
            print("\n" + "=" * 70)
            print("✅ Facebook Long-Lived Token obtenu avec succès !")
            print("=" * 70)
            print(f"\nACCESS_TOKEN: {long_token[:80]}...")
            print(f"Token Type: {token_type}")
            print(f"Expire dans: {expires_in} secondes ({expires_in//86400} jours)")
            print("\n" + "-" * 70)
            print("📝 Remplacez cette ligne dans votre .env :")
            print("-" * 70)
            print(f'FACEBOOK_ACCESS_TOKEN="{long_token}"')
            print("\n" + "=" * 70)
            
            # Optionally get Page token (never expires)
            print("\n💡 CONSEIL: Pour un token permanent (Page Token):")
            print("-" * 70)
            print("1. Utilisez ce token pour obtenir vos Pages:")
            print(f'\n   curl "https://graph.facebook.com/v18.0/me/accounts?access_token={long_token[:30]}..."')
            print("\n2. Copiez le 'access_token' de votre Page")
            print("3. Ce token ne expire JAMAIS (sauf révocation manuelle)")
            print("=" * 70 + "\n")
            
            return {
                "access_token": long_token,
                "expires_in": expires_in,
                "token_type": token_type
            }
            
        else:
            logger.error(f"❌ Facebook API Error (HTTP {response.status_code})")
            logger.error(f"Response: {response.text}")
            
            # Parse error details if JSON
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_info = error_data["error"]
                    logger.error(f"Error type: {error_info.get('type')}")
                    logger.error(f"Error message: {error_info.get('message')}")
                    logger.error(f"Error code: {error_info.get('code')}")
            except:
                pass
            
            return None
            
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return None


def get_page_tokens(user_token: str):
    """
    Get never-expiring Page tokens using a user access token.
    
    Args:
        user_token: User access token (short or long-lived)
    
    Returns:
        list of pages with their permanent tokens
    """
    
    url = "https://graph.facebook.com/v18.0/me/accounts"
    
    params = {
        "access_token": user_token
    }
    
    logger.info("📄 Fetching your Facebook Pages and their tokens...")
    
    try:
        response = httpx.get(url, params=params, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("data", [])
            
            if not pages:
                logger.warning("⚠️  No Pages found for this account")
                logger.info("Create a Facebook Page first to get a permanent token")
                return []
            
            print("\n" + "=" * 70)
            print(f"✅ Found {len(pages)} Facebook Page(s)")
            print("=" * 70)
            
            for i, page in enumerate(pages, 1):
                page_id = page.get("id")
                page_name = page.get("name")
                page_token = page.get("access_token")
                category = page.get("category")
                
                print(f"\n{i}. {page_name}")
                print(f"   ID: {page_id}")
                print(f"   Category: {category}")
                print(f"   Token: {page_token[:50]}...")
                print(f"\n   📝 Use this in .env (NEVER EXPIRES):")
                print(f'   FACEBOOK_ACCESS_TOKEN="{page_token}"')
            
            print("\n" + "=" * 70 + "\n")
            
            return pages
            
        else:
            logger.error(f"❌ Failed to get pages (HTTP {response.status_code})")
            logger.error(f"Response: {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return []


def print_help():
    """Print usage instructions."""
    print("\n" + "=" * 70)
    print("📘 Facebook Long-Lived Token Exchange")
    print("=" * 70)
    print("\nUsage:")
    print("    python scripts/oauth/facebook_long_lived_token.py SHORT_TOKEN")
    print("\nOptional flags:")
    print("    --pages    Also fetch Page tokens (never expire)")
    print("\nSteps to get short-lived token:")
    print("\n1. Go to Graph API Explorer:")
    print("   https://developers.facebook.com/tools/explorer/")
    
    print(f"\n2. Select your app (App ID: {settings.facebook_app_id})")
    
    print("\n3. Click 'Get Token' → 'Get User Access Token'")
    
    print("\n4. Select permissions:")
    print("   ☑ pages_read_engagement")
    print("   ☑ pages_show_list")
    print("   ☑ public_profile")
    
    print("\n5. Click 'Generate Access Token'")
    
    print("\n6. Copy the token (starts with EAAD...)")
    
    print("\n7. Run this script:")
    print("   python scripts/oauth/facebook_long_lived_token.py EAAD...")
    
    print("\n⚠️  Short token expires in 1 hour!")
    print("=" * 70 + "\n")


def main():
    """CLI entry point."""
    
    # Check arguments
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0 if len(sys.argv) > 1 else 1)
    
    short_token = sys.argv[1]
    get_pages = '--pages' in sys.argv
    
    # Validate token format (basic check)
    if not short_token.startswith("EAAD"):
        logger.warning("⚠️  Token doesn't start with 'EAAD'. Are you sure it's a Facebook token?")
    
    if len(short_token) < 50:
        logger.error("❌ Token seems too short. Did you copy it correctly?")
        sys.exit(1)
    
    # Exchange for long-lived token
    result = exchange_token(short_token)
    
    if not result:
        logger.error("❌ Token exchange failed!")
        sys.exit(1)
    
    logger.info("✅ Long-lived token obtained successfully!")
    
    # Optionally get Page tokens
    if get_pages:
        print("\n" + "-" * 70)
        pages = get_page_tokens(result["access_token"])
        
        if pages:
            logger.info(f"✅ Found {len(pages)} page(s) with permanent tokens!")
        else:
            logger.warning("⚠️  No pages found or failed to fetch")
    
    # Test the token
    print("\n" + "-" * 70)
    print("🧪 Testing token with Facebook Graph API...")
    print("-" * 70)
    
    try:
        # Test token validity
        test_url = "https://graph.facebook.com/v18.0/me"
        test_response = httpx.get(test_url, params={"access_token": result["access_token"]}, timeout=30.0)
        
        if test_response.status_code == 200:
            user_data = test_response.json()
            user_name = user_data.get("name", "Unknown")
            user_id = user_data.get("id", "Unknown")
            
            logger.info(f"✅ Token valid! User: {user_name} (ID: {user_id})")
        else:
            logger.warning(f"⚠️  Token obtained but validation failed: {test_response.text}")
            
    except Exception as e:
        logger.warning(f"⚠️  Could not test token: {e}")
        logger.info("Token was obtained successfully - test it manually later")
    
    print("\n" + "=" * 70)
    print("✅ All done! Update your .env and restart your services.")
    print("=" * 70 + "\n")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
