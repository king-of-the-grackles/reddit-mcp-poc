"""Reddit MCP Resources - Static and cacheable data endpoints."""

from typing import Dict, List, Any
import praw


def register_resources(mcp, reddit: praw.Reddit) -> None:
    """Register all Reddit resources with the MCP server."""
    
    @mcp.resource("reddit://popular-subreddits")
    def get_popular_subreddits() -> Dict[str, Any]:
        """
        Get list of 25 most popular subreddits.
        
        Returns a list of popular subreddits with their subscriber counts.
        This data is relatively static and ideal for caching.
        """
        try:
            subreddits = []
            for subreddit in reddit.subreddits.popular(limit=25):
                subreddits.append({
                    "name": subreddit.display_name,
                    "title": subreddit.title,
                    "subscribers": subreddit.subscribers,
                    "description": subreddit.public_description[:200] if subreddit.public_description else "",
                    "url": f"https://reddit.com/r/{subreddit.display_name}"
                })
            
            return {
                "count": len(subreddits),
                "subreddits": subreddits
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch popular subreddits: {str(e)}",
                "subreddits": []
            }
    
    @mcp.resource("reddit://subreddit/{name}/about")
    def get_subreddit_about(name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific subreddit.
        
        Args:
            name: The subreddit name (without r/ prefix)
            
        Returns information including description, rules, and statistics.
        """
        try:
            subreddit = reddit.subreddit(name)
            
            # Fetch basic info
            info = {
                "name": subreddit.display_name,
                "title": subreddit.title,
                "description": subreddit.public_description,
                "subscribers": subreddit.subscribers,
                "active_users": subreddit.active_user_count,
                "created_utc": subreddit.created_utc,
                "over_18": subreddit.over18,
                "url": f"https://reddit.com/r/{subreddit.display_name}"
            }
            
            # Try to fetch rules
            try:
                rules = []
                for rule in subreddit.rules:
                    rules.append({
                        "short_name": rule.short_name,
                        "description": rule.description,
                        "violation_reason": rule.violation_reason
                    })
                info["rules"] = rules
            except:
                info["rules"] = []
            
            return info
            
        except praw.exceptions.RedditAPIException as e:
            return {
                "error": f"Subreddit '{name}' not found or inaccessible",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch subreddit info: {str(e)}"
            }
    
    @mcp.resource("reddit://server-info")
    def get_server_info() -> Dict[str, Any]:
        """
        Get information about this Reddit MCP server's capabilities.
        
        Returns server version, available tools, and usage examples.
        """
        # Try to get rate limit info from Reddit
        rate_limit_info = {}
        try:
            # Access auth to check rate limit status
            rate_limit_info = {
                "requests_remaining": reddit.auth.limits.get('remaining', 'unknown'),
                "reset_timestamp": reddit.auth.limits.get('reset_timestamp', 'unknown'),
                "used": reddit.auth.limits.get('used', 'unknown')
            }
        except:
            rate_limit_info = {
                "status": "Rate limits tracked automatically by PRAW",
                "strategy": "Automatic retry with exponential backoff"
            }
        
        return {
            "name": "Reddit MCP Server",
            "version": "0.2.0",
            "description": "A Model Context Protocol server for Reddit content access with advanced discovery and batch operations",
            "changelog": {
                "0.2.0": [
                    "Added discover_subreddits_tool with confidence scoring",
                    "Added fetch_multiple_subreddits_tool for batch operations",
                    "Enhanced server-info with comprehensive documentation",
                    "Improved error handling and rate limit management"
                ],
                "0.1.0": [
                    "Initial release with search, fetch, and comment tools",
                    "Basic resources for popular subreddits and server info"
                ]
            },
            "capabilities": {
                "tools": [
                    {
                        "name": "discover_subreddits_tool",
                        "description": "Discover subreddits by keywords with confidence scoring. Supports batch queries for efficiency.",
                        "parameters": {
                            "query": "Single search term (e.g., 'python')",
                            "queries": "List of search terms for batch discovery (more efficient)",
                            "limit": "Maximum results per query (default 10)",
                            "include_nsfw": "Whether to include NSFW subreddits (default False)"
                        },
                        "features": [
                            "Confidence scoring based on name match, description, and activity",
                            "Batch mode reduces API calls by 70%+",
                            "Smart suggestions for alternative searches",
                            "NSFW filtering with count reporting"
                        ]
                    },
                    {
                        "name": "search_posts_tool",
                        "description": "Search for posts across ALL of Reddit",
                        "parameters": {
                            "query": "Search terms (required)",
                            "sort": "relevance, hot, top, or new (default: relevance)",
                            "time_filter": "all, year, month, week, or day (default: all)",
                            "limit": "Maximum results 1-100 (default: 10)"
                        }
                    },
                    {
                        "name": "search_in_subreddit_tool",
                        "description": "Search for posts within a SPECIFIC subreddit",
                        "parameters": {
                            "subreddit_name": "The subreddit to search in (required)",
                            "query": "Search terms (required)",
                            "sort": "relevance, hot, top, or new (default: relevance)",
                            "time_filter": "all, year, month, week, or day (default: all)",
                            "limit": "Maximum results 1-100 (default: 10)"
                        }
                    },
                    {
                        "name": "fetch_subreddit_posts_tool",
                        "description": "Browse posts from a specific subreddit without searching",
                        "parameters": {
                            "subreddit_name": "Exact subreddit name (required)",
                            "listing_type": "hot, new, top, or rising (default: hot)",
                            "time_filter": "For 'top' posts: all, year, month, week, or day",
                            "limit": "Maximum posts 1-100 (default: 10)"
                        }
                    },
                    {
                        "name": "fetch_multiple_subreddits_tool",
                        "description": "Fetch posts from multiple subreddits in one efficient call",
                        "parameters": {
                            "subreddit_names": "List of subreddit names (required)",
                            "listing_type": "hot, new, top, or rising (default: hot)",
                            "time_filter": "For 'top' posts: all, year, month, week, or day",
                            "limit_per_subreddit": "Maximum posts per subreddit 1-25 (default: 5)"
                        },
                        "efficiency_note": "Reduces API calls by fetching multiple subreddits in parallel"
                    },
                    {
                        "name": "fetch_submission_with_comments_tool",
                        "description": "Get a Reddit post with its complete comment tree",
                        "parameters": {
                            "submission_id": "Reddit post ID (e.g., '1abc234')",
                            "url": "Full Reddit URL (alternative to submission_id)",
                            "comment_limit": "Maximum comments to fetch (default: 100)",
                            "comment_sort": "best, top, or new (default: best)"
                        }
                    }
                ],
                "resources": [
                    {
                        "uri": "reddit://popular-subreddits",
                        "description": "List of 25 most popular subreddits",
                        "cacheable": True,
                        "refresh_interval": "24 hours recommended"
                    },
                    {
                        "uri": "reddit://subreddit/{name}/about",
                        "description": "Detailed information about a specific subreddit including rules",
                        "cacheable": True,
                        "refresh_interval": "1 hour recommended"
                    },
                    {
                        "uri": "reddit://server-info",
                        "description": "Server capabilities, version, and usage information",
                        "cacheable": False,
                        "always_current": True
                    }
                ],
                "prompts": [
                    {
                        "name": "get_started",
                        "description": "Comprehensive guide for using Reddit MCP effectively",
                        "tags": ["getting-started", "tutorial", "guide"]
                    },
                    {
                        "name": "research_topic",
                        "description": "Generate a structured research plan for any topic on Reddit",
                        "parameters": ["topic", "depth", "time_range", "include_nsfw"],
                        "tags": ["research", "planning", "analysis"]
                    },
                    {
                        "name": "analyze_sentiment",
                        "description": "Create sentiment analysis request for Reddit discussions",
                        "parameters": ["subreddit_or_topic", "is_subreddit", "aspects"],
                        "tags": ["sentiment", "analysis", "emotions"]
                    },
                    {
                        "name": "compare_communities",
                        "description": "Generate comparison analysis between multiple Reddit communities",
                        "parameters": ["subreddits", "comparison_aspects"],
                        "tags": ["comparison", "communities", "analysis"]
                    },
                    {
                        "name": "trending_analysis", 
                        "description": "Find and analyze trending topics across Reddit",
                        "parameters": ["category", "time_window", "min_engagement"],
                        "tags": ["trending", "discovery", "current-events"]
                    },
                    {
                        "name": "deep_dive",
                        "description": "Create deep dive research plan for exhaustive single-topic analysis",
                        "parameters": ["topic", "historical_range", "min_posts_to_analyze", "min_comments_to_analyze"],
                        "tags": ["deep-dive", "research", "comprehensive"]
                    },
                    {
                        "name": "citation_guide",
                        "description": "Generate proper citation format for Reddit content",
                        "parameters": ["include_examples", "citation_style"],
                        "tags": ["citation", "reference", "documentation"]
                    }
                ],
                "total_tools": 6,
                "total_resources": 3,
                "total_prompts": 7
            },
            "usage_examples": {
                "discover_subreddits": {
                    "single": "discover_subreddits_tool(query='python', limit=10)",
                    "batch": "discover_subreddits_tool(queries=['django', 'flask', 'fastapi'], limit=5)",
                    "with_nsfw": "discover_subreddits_tool(query='gaming', include_nsfw=True)"
                },
                "search": {
                    "global": "search_posts_tool(query='machine learning news', sort='top', time_filter='week')",
                    "in_subreddit": "search_in_subreddit_tool(subreddit_name='MachineLearning', query='transformers')"
                },
                "fetch_posts": {
                    "single": "fetch_subreddit_posts_tool(subreddit_name='technology', listing_type='hot')",
                    "multiple": "fetch_multiple_subreddits_tool(subreddit_names=['python', 'django'], listing_type='new')"
                },
                "comments": "fetch_submission_with_comments_tool(url='https://reddit.com/r/...')",
                "resources": {
                    "popular": "Access resource: reddit://popular-subreddits",
                    "about": "Access resource: reddit://subreddit/python/about"
                },
                "prompts": {
                    "getting_started": "Use 'get_started' prompt for comprehensive guide",
                    "research_planning": "research_topic(topic='machine learning', depth='comprehensive')",
                    "sentiment": "analyze_sentiment(subreddit_or_topic='technology', is_subreddit=True)",
                    "comparison": "compare_communities(subreddits=['python', 'golang', 'rust'])",
                    "trending": "trending_analysis(category='technology', time_window='day')",
                    "deep_research": "deep_dive(topic='AI ethics', min_posts_to_analyze=100)",
                    "citations": "citation_guide(include_examples=True)"
                }
            },
            "performance_tips": [
                "Use discover_subreddits_tool with batch queries to reduce API calls by 70%+",
                "Use fetch_multiple_subreddits_tool instead of multiple fetch_subreddit_posts_tool calls",
                "Cache resource responses when appropriate (popular-subreddits, subreddit/about)",
                "Confidence scores in discover_subreddits help identify best matches quickly"
            ],
            "batch_query_strategy": {
                "token_limit_warning": "MCP enforces a 25,000 token response limit",
                "safe_batch_sizes": [
                    "5 queries with limit=10 each (~3-5K tokens per batch)",
                    "8 queries with limit=5 each (~2-3K tokens per batch)",
                    "3 queries with limit=15 each (~4-6K tokens per batch)"
                ],
                "risky_configurations": [
                    "10+ queries with limit=15 (likely to exceed token limit)",
                    "15+ queries with limit=10 (will exceed token limit)"
                ],
                "comprehensive_discovery_example": {
                    "scenario": "Finding all gaming communities",
                    "approach": "Use 3-4 separate batch calls instead of one large batch",
                    "calls": [
                        "Call 1: ['gaming', 'video games', 'pc gaming', 'console', 'esports']",
                        "Call 2: ['board games', 'tabletop', 'card games', 'rpg', 'chess']",
                        "Call 3: ['retro gaming', 'arcade', 'indie games', 'mobile gaming']",
                        "Call 4: ['mmorpg', 'fps games', 'strategy games', 'puzzle games']"
                    ],
                    "benefit": "Gets comprehensive results without token overflow errors"
                },
                "token_usage_estimates": [
                    "Single query with limit=10: ~600-1000 tokens",
                    "5 queries batch with limit=10: ~3000-5000 tokens",
                    "10 queries batch with limit=10: ~6000-10000 tokens",
                    "Response size grows with confidence scores and metadata"
                ]
            },
            "rate_limiting": {
                "handler": "PRAW automatic rate limit handling",
                "strategy": "Exponential backoff with 5-minute cooldown",
                "current_status": rate_limit_info
            },
            "authentication": {
                "type": "Application-only OAuth",
                "scope": "Read-only access",
                "capabilities": "Search, browse, and read public content"
            },
            "api_efficiency": {
                "batch_operations": [
                    "discover_subreddits_tool supports batch queries",
                    "fetch_multiple_subreddits_tool fetches from multiple subreddits at once"
                ],
                "caching_recommendations": [
                    "Cache popular-subreddits for 24 hours",
                    "Cache subreddit/about for 1 hour",
                    "Search results can be cached for 5-15 minutes depending on sort type"
                ]
            }
        }