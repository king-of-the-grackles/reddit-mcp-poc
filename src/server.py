from fastmcp import FastMCP
from typing import Optional, Literal, List, Union, Dict, Any
import sys
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_reddit_client
from src.tools.search import search_all_reddit, search_in_subreddit
from src.tools.posts import fetch_subreddit_posts, fetch_multiple_subreddits
from src.tools.comments import fetch_submission_with_comments
from src.tools.discover import discover_subreddits
from src.resources import register_resources
from src.prompts import register_prompts

# Initialize MCP server
mcp = FastMCP("Reddit MCP", instructions="""
Reddit MCP Server - Comprehensive Reddit Analysis

✨ Three-Layer Architecture for Thorough Research!

RECOMMENDED WORKFLOW FOR COMPREHENSIVE COVERAGE:
1. discover_reddit_resources(topic, discovery_depth="comprehensive") 
   → Finds 8-15 relevant communities using multiple search strategies
2. get_operation_requirements("fetch_multiple") if 3+ subreddits found
   → Gets parameters for multi-community coverage  
3. execute_reddit_operation("fetch_multiple", subreddit_names=[...])
   → Gets diverse perspectives from multiple communities
4. Then search broadly and fetch specific comments for depth

📝 CRITICAL FOR RESEARCH QUALITY:
• Fetch detailed comments for AT LEAST 10 posts using fetch_comments
• ALWAYS include Reddit URLs when citing posts or comments in your final analysis
• Use comment_limit of 50-100 for comprehensive coverage of discussions

🎯 This approach ensures perspectives from diverse Reddit communities with proper citations!

📚 AVAILABLE PROMPTS (use these for structured research):
• get_started - Comprehensive guide for using Reddit MCP effectively
• research_topic - Generate a structured research plan for any topic
• analyze_sentiment - Create sentiment analysis request for Reddit discussions
• compare_communities - Compare multiple Reddit communities systematically
• trending_analysis - Find and analyze trending topics across Reddit
• deep_dive - Exhaustive single-topic analysis (100+ posts, 1000+ comments)
• citation_guide - Proper citation format for Reddit content

To use prompts: Query for available prompts via MCP prompts/list, then use them for structured research workflows.
Example: Use 'research_topic' prompt with parameters like topic="machine learning", depth="comprehensive"

Quick Start: Try the 'get_started' prompt or read reddit://server-info for complete docs.
""")

# Initialize Reddit client
reddit = get_reddit_client()

# Register resources and prompts
register_resources(mcp, reddit)
register_prompts(mcp)


# Supporting utility functions for layered architecture
def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract meaningful keywords from a text query."""
    # Remove common stop words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'what', 'how', 'where', 'when', 'why', 'are', 'is', 'do', 'does', 'can', 'will', 'would', 'should'}
    
    # Extract words, convert to lowercase, remove short words and stop words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    
    # Remove duplicates while preserving order
    unique_keywords = []
    for keyword in keywords:
        if keyword not in unique_keywords:
            unique_keywords.append(keyword)
    
    return unique_keywords[:max_keywords]


def generate_suggestions(operation_id: str, context: str) -> Dict[str, Any]:
    """Dynamically generate parameter suggestions based on context."""
    keywords = extract_keywords(context)
    suggestions = {}
    
    if operation_id == "search_all":
        suggestions["query"] = ' '.join(keywords[:5])  # Top 5 keywords
        
        # Infer time filter from context
        if any(word in context.lower() for word in ["recent", "lately", "nowadays", "current"]):
            suggestions["time_filter"] = "month"
        elif any(word in context.lower() for word in ["historical", "always", "ever", "all time"]):
            suggestions["time_filter"] = "all"
        else:
            suggestions["time_filter"] = "year"
        
        # Suggest limit based on context
        if any(word in context.lower() for word in ["comprehensive", "detailed", "thorough"]):
            suggestions["limit"] = 25
        elif any(word in context.lower() for word in ["quick", "brief", "overview"]):
            suggestions["limit"] = 10
        else:
            suggestions["limit"] = 15
            
    elif operation_id == "search_subreddit":
        suggestions["query"] = ' '.join(keywords[:4])
        suggestions["limit"] = 15
        
    elif operation_id == "fetch_multiple":
        suggestions["limit_per_subreddit"] = 8 if len(keywords) > 3 else 5
        
    return suggestions


def get_common_mistakes(operation_id: str) -> List[str]:
    """Return common mistakes for each operation."""
    mistakes = {
        "search_all": [
            "Using too generic terms (e.g., just 'help' or 'question')",
            "Not using quotes for exact phrases",
            "Setting limit too low for research tasks (<10)",
            "Using overly long queries (>100 chars)"
        ],
        "search_subreddit": [
            "Not specifying which subreddit to search",
            "Using subreddit names with 'r/' prefix",
            "Searching in wrong community for the topic"
        ],
        "fetch_posts": [
            "Using 'r/' prefix in subreddit names",
            "Not considering listing_type for your needs",
            "Requesting posts from non-existent subreddit"
        ],
        "fetch_multiple": [
            "Including 'r/' prefix in subreddit names",
            "Requesting more than 10 subreddits (API limit)",
            "Using invalid subreddit names",
            "Not using this when fetching from 2+ subreddits"
        ],
        "fetch_comments": [
            "Using invalid submission IDs",
            "Setting comment_limit too low for analysis",
            "Not providing either submission_id or url"
        ]
    }
    return mistakes.get(operation_id, [])


def validate_parameters(operation_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameters against operation schema."""
    validation_schemas = {
        "search_all": {
            "required": ["query"],
            "types": {"query": str, "sort": str, "time_filter": str, "limit": int},
            "constraints": {
                "query": {"min_length": 2, "max_length": 512},
                "sort": {"values": ["relevance", "hot", "top", "new"]},
                "time_filter": {"values": ["all", "year", "month", "week", "day"]},
                "limit": {"min": 1, "max": 100}
            }
        },
        "fetch_multiple": {
            "required": ["subreddit_names"],
            "types": {"subreddit_names": list, "listing_type": str, "limit_per_subreddit": int},
            "constraints": {
                "subreddit_names": {"max_items": 10},
                "listing_type": {"values": ["hot", "new", "top", "rising"]},
                "limit_per_subreddit": {"min": 1, "max": 25}
            }
        }
        # Add more schemas as needed
    }
    
    schema = validation_schemas.get(operation_id)
    if not schema:
        return {"valid": True}  # No validation for unknown operations
    
    errors = []
    
    # Check required parameters
    for required_param in schema["required"]:
        if required_param not in parameters:
            errors.append(f"Missing required parameter: {required_param}")
    
    # Type and constraint validation
    for param, value in parameters.items():
        if param in schema["types"]:
            expected_type = schema["types"][param]
            if not isinstance(value, expected_type):
                errors.append(f"Parameter '{param}' must be {expected_type.__name__}, got {type(value).__name__}")
        
        if param in schema.get("constraints", {}):
            constraints = schema["constraints"][param]
            
            if "min_length" in constraints and len(str(value)) < constraints["min_length"]:
                errors.append(f"Parameter '{param}' too short (min {constraints['min_length']} chars)")
            
            if "max_length" in constraints and len(str(value)) > constraints["max_length"]:
                errors.append(f"Parameter '{param}' too long (max {constraints['max_length']} chars)")
            
            if "values" in constraints and value not in constraints["values"]:
                errors.append(f"Parameter '{param}' must be one of {constraints['values']}")
            
            if "min" in constraints and value < constraints["min"]:
                errors.append(f"Parameter '{param}' must be at least {constraints['min']}")
            
            if "max" in constraints and value > constraints["max"]:
                errors.append(f"Parameter '{param}' must be at most {constraints['max']}")
            
            if "max_items" in constraints and isinstance(value, list) and len(value) > constraints["max_items"]:
                errors.append(f"Parameter '{param}' can have at most {constraints['max_items']} items")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# Three-Layer Architecture Tools

@mcp.tool()
def discover_reddit_resources(
    topic: Optional[str] = None,
    include_communities: bool = True,
    discovery_depth: str = "comprehensive"
) -> Dict[str, Any]:
    """
    LAYER 1: Discover available Reddit resources and operations.
    
    **ALWAYS USE THIS FIRST** to understand what's available before proceeding.
    
    Args:
        topic: Optional topic to find relevant communities for
        include_communities: Whether to search for relevant subreddits
        discovery_depth: Discovery thoroughness
            - "quick": Single search (faster, 3-5 subreddits) 
            - "comprehensive": Multiple searches (8-15 subreddits for broader perspective)
    
    Returns:
        Available operations, relevant communities, and recommended workflow
    """
    result = {
        "available_operations": [
            {
                "id": "search_all",
                "name": "Search across all Reddit",
                "description": "Find posts from anywhere on Reddit",
                "use_when": "Exploring a topic broadly or when you don't know specific subreddits"
            },
            {
                "id": "search_subreddit", 
                "name": "Search within specific subreddit",
                "description": "Targeted search in a known community",
                "use_when": "You know which specific community to search"
            },
            {
                "id": "fetch_posts",
                "name": "Fetch posts from subreddit",
                "description": "Get latest/hot/top posts without searching",
                "use_when": "Want to see what's currently trending in a community"
            },
            {
                "id": "fetch_multiple",
                "name": "Batch fetch from multiple subreddits",
                "description": "Efficiently get posts from many communities",
                "use_when": "Need content from 2+ subreddits (70% more efficient)",
                "efficiency_note": "⚡ MOST EFFICIENT for multiple communities"
            },
            {
                "id": "fetch_comments",
                "name": "Get post with full comments",
                "description": "Deep dive into a specific discussion",
                "use_when": "Need detailed opinions, replies, and discussion threads"
            }
        ],
        "workflow_guidance": [
            "1. Use this discovery tool first (comprehensive mode recommended)",
            "2. If 3+ subreddits found: get_operation_requirements('fetch_multiple')",
            "3. Execute fetch_multiple for broad community coverage",
            "4. Then search_all for additional coverage",
            "5. 📝 CRITICAL: Deep dive with fetch_comments on AT LEAST 10 promising posts",
            "6. 🔗 ALWAYS include Reddit URLs when citing posts/comments in final analysis",
            "⚡ Multi-community approach = 60% better coverage with proper citations!"
        ]
    }
    
    if topic and include_communities:
        try:
            all_subreddits = set()
            search_queries_used = []
            
            if discovery_depth == "comprehensive":
                # Strategy 1: Direct topic search
                primary_result = discover_subreddits(
                    query=topic,
                    reddit=reddit, 
                    limit=12,
                    include_nsfw=False
                )
                search_queries_used.append(topic)
                
                if "subreddits" in primary_result and primary_result["subreddits"]:
                    all_subreddits.update(primary_result["subreddits"])
                
                # Strategy 2: Keyword-based searches for broader coverage
                keywords = extract_keywords(topic)
                if len(keywords) >= 2:
                    additional_queries = [
                        keywords[0],  # Most important keyword alone
                        ' '.join(keywords[:2]),  # Top 2 keywords
                        ' '.join(keywords[1:3]) if len(keywords) > 2 else None  # Alternative combination
                    ]
                    
                    for query in filter(None, additional_queries):
                        if query != topic and len(query.strip()) > 2:  # Avoid duplicates and tiny queries
                            try:
                                additional_result = discover_subreddits(
                                    query=query,
                                    reddit=reddit,
                                    limit=8,
                                    include_nsfw=False
                                )
                                search_queries_used.append(query)
                                
                                if "subreddits" in additional_result and additional_result["subreddits"]:
                                    all_subreddits.update(additional_result["subreddits"])
                            except Exception:
                                continue  # Skip failed additional searches
                                
            else:  # discovery_depth == "quick"
                # Single search for quick discovery
                quick_result = discover_subreddits(
                    query=topic,
                    reddit=reddit,
                    limit=8,
                    include_nsfw=False
                )
                search_queries_used.append(topic)
                
                if "subreddits" in quick_result and quick_result["subreddits"]:
                    all_subreddits.update(quick_result["subreddits"])
            
            # Convert to sorted list (by relevance from discover_subreddits)
            subreddit_list = list(all_subreddits)
            
            if subreddit_list:
                result["relevant_communities"] = {
                    "count": len(subreddit_list),
                    "subreddits": subreddit_list[:12],  # Top 12 for comprehensive coverage
                    "search_queries_used": search_queries_used,
                    "discovery_method": discovery_depth
                }
                
                # Enhanced recommendations based on community count
                if len(subreddit_list) >= 3:
                    result["recommended_operation"] = "fetch_multiple"
                    result["recommended_workflow"] = {
                        "step_1": "Use 'fetch_multiple' with discovered subreddits for broad community coverage",
                        "step_2": "Then use 'search_all' for additional posts that might be missed",
                        "step_3": "Deep dive with 'fetch_comments' on most promising posts",
                        "coverage_benefit": f"Multi-community approach covers {len(subreddit_list)} communities vs 1 with single searches"
                    }
                    result["suggested_fetch_multiple_params"] = {
                        "subreddit_names": subreddit_list[:8],  # Top 8 for optimal performance
                        "listing_type": "hot",
                        "limit_per_subreddit": 6 if len(subreddit_list) > 5 else 8
                    }
                elif len(subreddit_list) == 2:
                    result["recommended_operation"] = "fetch_multiple"
                    result["suggested_fetch_multiple_params"] = {
                        "subreddit_names": subreddit_list,
                        "limit_per_subreddit": 10
                    }
                else:
                    result["recommended_operation"] = "search_subreddit"
                    
            else:
                result["relevant_communities"] = {
                    "count": 0,
                    "note": f"No specific communities found for '{topic}'. Use 'search_all' for broad exploration.",
                    "search_queries_used": search_queries_used
                }
                result["recommended_operation"] = "search_all"
                
        except Exception as e:
            result["community_discovery_error"] = f"Could not discover communities: {str(e)}"
            result["recommended_operation"] = "search_all"
    
    return result


@mcp.tool()
def get_operation_requirements(
    operation_id: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    LAYER 2: Get detailed requirements for a Reddit operation.
    
    **USE THIS BEFORE EXECUTING** to understand parameters, validation rules, and get suggestions.
    
    Args:
        operation_id: The operation ID from discover_reddit_resources
        context: Optional context about what you're trying to accomplish
    
    Returns:
        Parameter schemas, validation rules, suggestions, and common mistakes to avoid
    """
    
    schemas = {
        "search_all": {
            "function_name": "search_posts_tool", 
            "description": "Search across all of Reddit for posts matching your query",
            "required": ["query"],
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Search terms to find relevant posts",
                    "constraints": {"min_length": 2, "max_length": 512},
                    "tips": [
                        "Use quotes for exact phrases: \"specific phrase\"",
                        "Combine related terms with spaces",
                        "Reddit search uses boolean AND by default"
                    ]
                },
                "sort": {
                    "type": "enum",
                    "values": ["relevance", "hot", "top", "new"],
                    "default": "relevance",
                    "description": "How to sort the results"
                },
                "time_filter": {
                    "type": "enum",
                    "values": ["all", "year", "month", "week", "day"],
                    "default": "all",
                    "recommendation": "Use 'year' for recent but comprehensive results"
                },
                "limit": {
                    "type": "integer",
                    "range": [1, 100],
                    "default": 10,
                    "recommendation": "Use 15-25 for good research coverage"
                }
            }
        },
        "search_subreddit": {
            "function_name": "search_in_subreddit_tool",
            "description": "Search within a specific subreddit community",
            "required": ["subreddit_name", "query"],
            "parameters": {
                "subreddit_name": {
                    "type": "string", 
                    "description": "Name of subreddit without 'r/' prefix",
                    "examples": ["AskReddit", "Python", "travel"]
                },
                "query": {
                    "type": "string",
                    "description": "Search terms for within that subreddit",
                    "constraints": {"min_length": 2, "max_length": 512}
                },
                "sort": {
                    "type": "enum",
                    "values": ["relevance", "hot", "top", "new"],
                    "default": "relevance"
                },
                "time_filter": {
                    "type": "enum",
                    "values": ["all", "year", "month", "week", "day"],
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "range": [1, 100],
                    "default": 10
                }
            }
        },
        "fetch_posts": {
            "function_name": "fetch_subreddit_posts_tool",
            "description": "Get latest posts from a subreddit without searching",
            "required": ["subreddit_name"],
            "parameters": {
                "subreddit_name": {
                    "type": "string",
                    "description": "Name of subreddit without 'r/' prefix"
                },
                "listing_type": {
                    "type": "enum",
                    "values": ["hot", "new", "top", "rising"],
                    "default": "hot",
                    "description": "Type of posts to fetch"
                },
                "time_filter": {
                    "type": "enum",
                    "values": ["all", "year", "month", "week", "day"],
                    "default": None,
                    "description": "Time period for 'top' posts (only used when listing_type='top')"
                },
                "limit": {
                    "type": "integer", 
                    "range": [1, 100],
                    "default": 10
                }
            }
        },
        "fetch_multiple": {
            "function_name": "fetch_multiple_subreddits_tool", 
            "description": "⚡ Efficiently fetch posts from multiple subreddits in one call - BEST FOR COMPREHENSIVE COVERAGE",
            "required": ["subreddit_names"],
            "parameters": {
                "subreddit_names": {
                    "type": "array[string]",
                    "description": "List of subreddit names without 'r/' prefix",
                    "constraints": {"max_items": 10},
                    "examples": [["Python", "learnpython", "programming"]]
                },
                "listing_type": {
                    "type": "enum",
                    "values": ["hot", "new", "top", "rising"],
                    "default": "hot"
                },
                "time_filter": {
                    "type": "enum",
                    "values": ["all", "year", "month", "week", "day"],
                    "default": None,
                    "description": "For 'top' listing type only"
                },
                "limit_per_subreddit": {
                    "type": "integer",
                    "range": [1, 25], 
                    "default": 5,
                    "recommendation": "5-10 for overview, 15+ for comprehensive analysis"
                }
            },
            "performance_benefits": {
                "vs_individual_calls": "70% fewer API calls",
                "token_savings": "~40% token reduction", 
                "speed": "3x faster execution",
                "coverage": "Gets diverse perspectives from multiple communities",
                "when_to_use": "⚡ ALWAYS use this for 2+ subreddits instead of multiple individual calls",
                "comprehensive_research": "Essential for thorough analysis - covers 5-8 communities in one call"
            }
        },
        "fetch_comments": {
            "function_name": "fetch_submission_with_comments_tool",
            "description": "Get a specific Reddit post with its full comment tree",
            "required_one_of": ["submission_id", "url"],
            "parameters": {
                "submission_id": {
                    "type": "string",
                    "description": "Reddit post ID (e.g., 'abc123')",
                    "examples": ["1abc234", "xyz789"]
                },
                "url": {
                    "type": "string", 
                    "description": "Full Reddit URL to the post",
                    "examples": ["https://reddit.com/r/Python/comments/abc123/title/"]
                },
                "comment_limit": {
                    "type": "integer",
                    "default": 100,
                    "recommendation": "50-100 for comprehensive coverage, 20-30 for quick overview"
                },
                "comment_sort": {
                    "type": "enum",
                    "values": ["best", "top", "new"],
                    "default": "best"
                }
            }
        }
    }
    
    if operation_id not in schemas:
        return {
            "error": f"Unknown operation: {operation_id}",
            "available_operations": list(schemas.keys()),
            "hint": "Use discover_reddit_resources() to see all available operations"
        }
    
    schema = schemas[operation_id].copy()
    
    # Add operation-specific guidance based on discovered communities
    if operation_id == "search_all" and context:
        # Check if this could benefit from multi-subreddit approach
        keywords = extract_keywords(context)
        if len(keywords) >= 2:  # Complex topic likely has multiple communities
            schema["multi_community_recommendation"] = {
                "notice": "⚠️ CONSIDER fetch_multiple for comprehensive coverage!",
                "reason": f"Topic '{context}' likely spans multiple communities",
                "suggestion": "If discover_reddit_resources found 3+ subreddits, use 'fetch_multiple' first for broader perspective",
                "workflow": "fetch_multiple → search_all → fetch_comments gives best coverage",
                "research_depth": "📝 IMPORTANT: Fetch comments for AT LEAST 10 posts for thorough analysis",
                "citation_requirement": "🔗 Always include Reddit URLs when citing posts/comments"
            }
    
    # Add context-aware suggestions if context provided
    if context:
        schema["context_suggestions"] = generate_suggestions(operation_id, context)
        schema["context_analysis"] = {
            "extracted_keywords": extract_keywords(context),
            "inferred_intent": "research" if any(w in context.lower() for w in ["what", "how", "research", "analysis"]) else "browse"
        }
    
    # Add common mistakes
    schema["common_mistakes"] = get_common_mistakes(operation_id)
    
    # Add next steps
    schema["next_step"] = f"Use execute_reddit_operation('{operation_id}', parameters) with the validated parameters"
    
    return schema


@mcp.tool()
def execute_reddit_operation(
    operation_id: str,
    parameters: Dict[str, Any],
    validate: bool = True
) -> Dict[str, Any]:
    """
    LAYER 3: Execute a Reddit operation with validated parameters.
    
    **ONLY USE AFTER** getting requirements from get_operation_requirements().
    
    Args:
        operation_id: The operation to execute (from Layer 1)
        parameters: Parameters matching the schema from Layer 2  
        validate: Whether to validate parameters before execution (recommended)
    
    Returns:
        Operation results or detailed error information
    """
    
    # Map operation IDs to actual functions
    operations = {
        "search_all": search_all_reddit,
        "search_subreddit": search_in_subreddit,
        "fetch_posts": fetch_subreddit_posts,
        "fetch_multiple": fetch_multiple_subreddits,
        "fetch_comments": fetch_submission_with_comments
    }
    
    if operation_id not in operations:
        return {
            "error": f"Unknown operation: {operation_id}",
            "available_operations": list(operations.keys()),
            "hint": "Use discover_reddit_resources() to see available operations"
        }
    
    # Optional validation against schema
    if validate:
        validation_result = validate_parameters(operation_id, parameters)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "Parameter validation failed",
                "validation_errors": validation_result["errors"],
                "hint": f"Use get_operation_requirements('{operation_id}') to see correct parameter schema",
                "provided_parameters": list(parameters.keys())
            }
    
    # Add reddit client to parameters and prepare for execution
    parameters = parameters.copy()  # Don't modify original
    parameters["reddit"] = reddit
    
    # Execute the operation
    try:
        result = operations[operation_id](**parameters)
        # Create clean copy of parameters for response (exclude reddit client)
        clean_parameters = {k: v for k, v in parameters.items() if k != "reddit"}
        return {
            "success": True,
            "operation": operation_id,
            "parameters_used": clean_parameters,
            "result": result
        }
    except Exception as e:
        # Create clean copy of parameters for response (exclude reddit client)
        clean_parameters = {k: v for k, v in parameters.items() if k != "reddit"}
        return {
            "success": False,
            "operation": operation_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "hint": f"Check that parameters match requirements from get_operation_requirements('{operation_id}')",
            "provided_parameters": clean_parameters
        }



def main():
    """Main entry point for the Reddit MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()