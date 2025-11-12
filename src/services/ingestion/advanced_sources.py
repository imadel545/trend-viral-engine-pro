"""
Advanced Data Sources - Production-ready API integrations.

TikTok Creative Center, Enhanced Reddit (asyncpraw), Facebook Graph API.
Includes rate limiting, retry logic, engagement metrics extraction.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import backoff
from loguru import logger

from src.core.config import settings
from src.services.ingestion.service import DataSource


class TikTokCreativeCenterSource(DataSource):
    """
    TikTok Creative Center API - Trending hashtags, sounds, videos.
    
    Official API: https://developers.tiktok.com/doc/creative-center-api
    Provides real-time trending content across regions.
    """

    def __init__(self):
        super().__init__("tiktok_creative_center")
        self.base_url = "https://open.tiktokapis.com/v2/research"
        self.client_key = settings.tiktok_client_key
        self.client_secret = settings.tiktok_client_secret
        self.access_token = None
        # Lock to avoid concurrent token fetches (race condition)
        self._token_lock = asyncio.Lock()
        self.rate_limit = settings.tiktok_rate_limit  # requests per minute

    async def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token."""
        if self.access_token:
            return self.access_token

        auth_url = "https://open.tiktokapis.com/v2/oauth/token/"
        # Ensure only one coroutine fetches token at a time
        async with self._token_lock:
            # Double-check after acquiring lock
            if self.access_token:
                return self.access_token

            async with aiohttp.ClientSession() as session:
                data = {
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                }

                async with session.post(auth_url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        # defensive access
                        token = result.get("data", {}).get("access_token")
                        if not token:
                            error = await response.text()
                            self.logger.error(f"Failed to parse access token: {error}")
                            raise Exception("TikTok auth failed: missing token")

                        self.access_token = token
                        self.logger.info("✅ TikTok access token obtained")
                        return self.access_token
                    else:
                        error = await response.text()
                        self.logger.error(f"Failed to get access token: {error}")
                        raise Exception(f"TikTok auth failed: {error}")

    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, Exception), max_tries=3)
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated API request with rate limiting."""
        token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limit exceeded - wait and retry
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.logger.warning(f"Rate limit hit - waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    raise Exception("Rate limit exceeded")
                else:
                    error = await response.text()
                    self.logger.error(f"API error {response.status}: {error}")
                    raise Exception(f"TikTok API error: {error}")

    async def collect(self, 
                     regions: Optional[List[str]] = None,
                     content_types: Optional[List[str]] = None,
                     max_results: int = 100,
                     **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Collect trending content from TikTok Creative Center.
        
        Args:
            regions: List of region codes (e.g., ['US', 'FR', 'GB'])
            content_types: ['hashtag', 'sound', 'video', 'creator']
            max_results: Maximum results per region/type
        
        Returns:
            List of trending items with engagement metrics
        """
        regions = regions or ["US", "FR", "GB", "CA", "MA"]
        content_types = content_types or ["hashtag", "video"]
        
        all_trends = []
        
        for region in regions:
            for content_type in content_types:
                try:
                    trends = await self._collect_trending(region, content_type, max_results)
                    all_trends.extend(trends)
                    
                    # Rate limiting
                    await asyncio.sleep(60 / self.rate_limit)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting {content_type} from {region}: {e}")
                    continue
        
        self.logger.info(f"Collected {len(all_trends)} TikTok trends")
        return all_trends

    async def _collect_trending(self, region: str, content_type: str, max_results: int) -> List[Dict[str, Any]]:
        """Collect specific trending content type for a region."""
        
        # TikTok Creative Center API parameters
        params = {
            "region_code": region,
            "category": "all",
            "limit": min(max_results, 100),  # API limit per request
            "cursor": 0
        }
        
        endpoint_map = {
            "hashtag": "trending/hashtag",
            "sound": "trending/music",
            "video": "trending/video",
            "creator": "trending/creator"
        }
        
        endpoint = endpoint_map.get(content_type, "trending/hashtag")
        
        try:
            response = await self._make_request(endpoint, params)
            
            trends = []
            for item in response.get("data", {}).get("list", []):
                trend_data = {
                    "content_type": content_type,
                    "region": region,
                    "topic": item.get("name") or item.get("title") or item.get("hashtag_name"),
                    "rank": item.get("rank", 0),
                    
                    # Engagement metrics (critical for TrendDynamicsExtractor)
                    "views": item.get("view_count", 0),
                    "likes": item.get("like_count", 0),
                    "shares": item.get("share_count", 0),
                    "comments": item.get("comment_count", 0),
                    "posts_count": item.get("publish_count", 0),
                    
                    # Velocity metrics
                    "growth_rate": item.get("growth_rate", 0.0),
                    "velocity_score": item.get("trend_score", 0.0),
                    
                    # Temporal data
                    "timestamp": datetime.now().isoformat(),
                    "collection_date": datetime.now().strftime("%Y-%m-%d"),
                    
                    # Raw metadata
                    "metadata": item
                }
                
                trends.append(trend_data)
            
            self.logger.info(f"✅ Collected {len(trends)} {content_type}s from {region}")
            return trends
            
        except Exception as e:
            self.logger.error(f"Failed to collect {content_type} from {region}: {e}")
            return []


class EnhancedRedditSource(DataSource):
    """
    Enhanced Reddit Source with asyncpraw.
    
    Features:
    - Async concurrent collection from multiple subreddits
    - Hot/Top/Trending posts with engagement metrics
    - Real-time growth tracking (score, comments)
    - Rich metadata for viral prediction
    """

    def __init__(self):
        super().__init__("reddit_enhanced")
        self.reddit = None

    async def _get_reddit_client(self):
        """Get or create asyncpraw Reddit client."""
        if self.reddit is None:
            import asyncpraw
            
            self.reddit = asyncpraw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent
            )
            self.logger.info("✅ AsyncPRAW Reddit client initialized")
        
        return self.reddit

    async def collect(self,
                     subreddits: Optional[List[str]] = None,
                     sort: str = "hot",
                     limit: int = 100,
                     time_filter: str = "day",
                     **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Collect posts from Reddit with rich engagement metrics.
        
        Args:
            subreddits: List of subreddit names (default from settings)
            sort: 'hot', 'top', 'new', 'rising', 'controversial'
            limit: Posts per subreddit
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        
        Returns:
            List of posts with engagement metrics, author info, timestamps
        """
        reddit = await self._get_reddit_client()
        subreddits = subreddits or settings.reddit_subreddits
        
        all_posts = []
        
        # Collect concurrently from all subreddits
        tasks = [
            self._collect_from_subreddit(reddit, sub, sort, limit, time_filter)
            for sub in subreddits
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_posts.extend(result)
            else:
                self.logger.error(f"Subreddit collection error: {result}")
        
        self.logger.info(f"Collected {len(all_posts)} Reddit posts from {len(subreddits)} subreddits")
        return all_posts

    async def _collect_from_subreddit(self, reddit, subreddit_name: str, sort: str, limit: int, time_filter: str) -> List[Dict[str, Any]]:
        """Collect posts from single subreddit."""
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            
            # Get posts by sort type
            if sort == "hot":
                posts_list = subreddit.hot(limit=limit)
            elif sort == "top":
                posts_list = subreddit.top(limit=limit, time_filter=time_filter)
            elif sort == "new":
                posts_list = subreddit.new(limit=limit)
            elif sort == "rising":
                posts_list = subreddit.rising(limit=limit)
            else:
                posts_list = subreddit.hot(limit=limit)
            
            posts = []
            async for post in posts_list:
                try:
                    # Calculate engagement rate
                    total_engagement = post.score + post.num_comments
                    hours_since_posted = (datetime.now() - datetime.fromtimestamp(post.created_utc)).total_seconds() / 3600
                    engagement_rate = total_engagement / max(hours_since_posted, 1)
                    
                    # Enrich text with selftext + top comments
                    enriched_text = await self._enrich_reddit_text(post)
                    
                    post_data = {
                        # Core content
                        "topic": post.title,
                        "text": enriched_text,
                        "url": post.url,
                        "permalink": f"https://reddit.com{post.permalink}",
                        
                        # Subreddit info
                        "subreddit": subreddit_name,
                        "category": sort,
                        
                        # Engagement metrics (CRITICAL for dynamics)
                        "score": post.score,
                        "upvote_ratio": post.upvote_ratio,
                        "num_comments": post.num_comments,
                        "total_awards": post.total_awards_received,
                        
                        # Velocity metrics
                        "engagement_rate": engagement_rate,
                        "hours_since_posted": hours_since_posted,
                        "comments_per_hour": post.num_comments / max(hours_since_posted, 1),
                        "score_per_hour": post.score / max(hours_since_posted, 1),
                        
                        # Author & community
                        "author": str(post.author) if post.author else "[deleted]",
                        "author_flair": post.author_flair_text,
                        "is_self": post.is_self,
                        "is_video": post.is_video,
                        "is_nsfw": post.over_18,
                        
                        # Temporal data
                        "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "collected_at": datetime.now().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        
                        # Post ID for tracking
                        "post_id": post.id,
                        "content_id": f"reddit_{post.id}"
                    }
                    
                    posts.append(post_data)
                
                except Exception as e:
                    self.logger.error(f"Error processing post: {e}")
                    continue
            
            self.logger.info(f"✅ Collected {len(posts)} posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error collecting from r/{subreddit_name}: {e}")
            return []
    
    async def _enrich_reddit_text(self, post) -> str:
        """
        Enrichit le texte d'un post Reddit avec:
        - Titre du post
        - Selftext (si présent)
        - Top 5 commentaires (triés par score)
        
        Retourne un texte enrichi pour meilleure analyse ML.
        """
        parts = []
        
        # 1. Titre (toujours présent)
        parts.append(f"TITLE: {post.title}")
        
        # 2. Selftext (si post texte)
        if post.selftext and len(post.selftext.strip()) > 0:
            parts.append(f"BODY: {post.selftext[:500]}")
        
        # 3. Top 5 commentaires
        try:
            # Charger comments explicitement
            comments_list = []
            if hasattr(post, 'comments'):
                await post.comments.replace_more(limit=0)  # Flatten comment tree
                comments_list = post.comments.list() if hasattr(post.comments, 'list') else []
            
            # Trier par score et prendre top 5
            if comments_list and len(comments_list) > 0:
                sorted_comments = sorted(comments_list, key=lambda c: getattr(c, 'score', 0), reverse=True)[:5]
                
                if sorted_comments:
                    parts.append("TOP COMMENTS:")
                    for i, comment in enumerate(sorted_comments, 1):
                        comment_text = getattr(comment, 'body', '')[:200]
                        comment_score = getattr(comment, 'score', 0)
                        if comment_text:
                            parts.append(f"  [{i}] (score:{comment_score}) {comment_text}")
        
        except Exception as e:
            self.logger.debug(f"Could not fetch comments: {e}")
        
        # Joindre tout avec newlines
        enriched = "\n".join(parts)
        
        # Limiter taille totale à 2000 chars
        if len(enriched) > 2000:
            enriched = enriched[:2000] + "..."
        
        return enriched

    async def close(self):
        """Close Reddit client."""
        if self.reddit:
            await self.reddit.close()


class FacebookGraphAPISource(DataSource):
    """
    Facebook Graph API - Trending topics and hashtags.
    
    Note: Requires approved Facebook App + User Access Token.
    Limited public data available due to API restrictions.
    """

    def __init__(self):
        super().__init__("facebook_graph")
        self.app_id = settings.facebook_app_id
        self.app_secret = settings.facebook_app_secret
        self.access_token = settings.facebook_access_token or self._get_app_token()
        self.base_url = "https://graph.facebook.com/v18.0"
        
        # Generate appsecret_proof for secure API calls
        import hmac
        import hashlib
        self.appsecret_proof = hmac.new(
            self.app_secret.encode('utf-8'),
            self.access_token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _get_app_token(self) -> str:
        """Generate app access token."""
        return f"{self.app_id}|{self.app_secret}"

    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, Exception), max_tries=3)
    async def collect(self, query_topics: Optional[List[str]] = None, limit: int = 50, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Collect trending topics from Facebook.
        
        Note: Public data is limited. Consider using:
        - CrowdTangle API (for public pages/groups)
        - Approved Research API access
        
        Args:
            query_topics: List of topics to search
            limit: Results per topic
        
        Returns:
            List of trending posts/topics with engagement metrics
        """
        query_topics = query_topics or ["viral", "trending", "meme", "challenge"]
        
        all_trends = []
        
        async with aiohttp.ClientSession() as session:
            # NEW: Use /me/feed instead of deprecated /search
            # This gets the user's own posts and feed (limited but working)
            try:
                params = {
                    # Simplified fields - no extended permissions needed
                    "fields": "message,created_time,permalink_url,id",
                    "limit": limit * len(query_topics),  # Get more since we filter by topic
                    "access_token": self.access_token,
                    "appsecret_proof": self.appsecret_proof
                }
                
                url = f"{self.base_url}/me/feed"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get("data", []):
                            message = item.get("message", "")
                            
                            # Filter by topic keywords (simple matching)
                            matched_topic = None
                            for topic in query_topics:
                                if topic.lower() in message.lower():
                                    matched_topic = topic
                                    break
                            
                            # If no match, still include but mark as general
                            if not matched_topic and message:
                                matched_topic = "general"
                            
                            if message:  # Only include posts with text
                                # Note: Engagement metrics require extended permissions
                                # Using basic fields only for now
                                
                                trend_data = {
                                    "topic": message[:200],
                                    "platform": "facebook",
                                    "post_id": item.get("id"),
                                    "created_time": item.get("created_time"),
                                    "timestamp": datetime.now().isoformat(),
                                    "query_topic": matched_topic,
                                    "url": item.get("permalink_url"),
                                    "metadata": item
                                }
                                
                                all_trends.append(trend_data)
                    
                    else:
                        error = await response.text()
                        self.logger.warning(f"Facebook API error: {error}")
                
            except Exception as e:
                self.logger.error(f"Error collecting Facebook data from /me/feed: {e}")
        
        self.logger.info(f"Collected {len(all_trends)} Facebook trends")
        return all_trends
