"""Reddit MCP Prompts - Research-focused prompt templates for Reddit analysis."""

from typing import List, Optional, Dict, Any
from fastmcp.prompts.prompt import Message, PromptMessage


def register_prompts(mcp) -> None:
    """Register all Reddit research prompts with the MCP server."""
    
    @mcp.prompt(
        description="Get started with Reddit MCP - learn how to conduct comprehensive research",
        tags={"getting-started", "tutorial", "guide"}
    )
    def get_started() -> List[Message]:
        """Generate a comprehensive guide for using Reddit MCP effectively."""
        return [
            Message(
                "Welcome to Reddit MCP! I'll help you conduct thorough Reddit research. "
                "Here's the recommended workflow for comprehensive analysis:",
                role="assistant"
            ),
            Message(
                "First, let me discover relevant communities for your topic using "
                "discover_reddit_resources with discovery_depth='comprehensive'. "
                "This will find 8-15 relevant subreddits using multiple search strategies."
            ),
            Message(
                "Next, I'll use fetch_multiple to efficiently get posts from the top communities. "
                "This is 70% more efficient than individual calls and ensures diverse perspectives."
            ),
            Message(
                "Then, I'll search broadly using search_all for additional coverage beyond "
                "the discovered communities."
            ),
            Message(
                "CRITICAL: I'll fetch detailed comments for AT LEAST 10 posts using fetch_comments "
                "with comment_limit of 50-100 for comprehensive discussion analysis."
            ),
            Message(
                "Finally, I'll compile findings with proper Reddit URL citations for every "
                "post and comment referenced. What topic would you like to research?"
            )
        ]
    
    @mcp.prompt(
        description="Generate a comprehensive research plan for any topic on Reddit",
        tags={"research", "planning", "analysis"}
    )
    def research_topic(
        topic: str,
        depth: str = "comprehensive",
        time_range: str = "year",
        include_nsfw: bool = False
    ) -> str:
        """Create a structured research plan for investigating a topic on Reddit."""
        nsfw_note = "including NSFW communities" if include_nsfw else "excluding NSFW content"
        
        return f"""I'll conduct a {depth} Reddit research analysis on '{topic}' covering the past {time_range}, {nsfw_note}.

## Research Plan:

### Phase 1: Community Discovery
- Use discover_reddit_resources('{topic}', discovery_depth='{depth}') to find 8-15 relevant subreddits
- Document confidence scores and community sizes for prioritization

### Phase 2: Multi-Community Data Collection  
- Fetch posts from top 8 communities using fetch_multiple_subreddits_tool
- Parameters: listing_type='hot' for current discussions, limit_per_subreddit=8
- Expected coverage: ~64 posts from diverse perspectives

### Phase 3: Broad Search Expansion
- Execute search_all_reddit('{topic}', time_filter='{time_range}', limit=25)
- Capture posts that might not appear in discovered communities

### Phase 4: Deep Comment Analysis (CRITICAL)
- Fetch full comment trees for top 15 posts using fetch_comments
- Use comment_limit=75 for comprehensive discussion coverage
- Focus on posts with high engagement (50+ comments)

### Phase 5: Synthesis & Citation
- Compile findings with themes, sentiment patterns, and key insights
- Include Reddit URLs for EVERY cited post and comment
- Structure: Executive summary → Community analysis → Key themes → Notable discussions

This approach ensures ~100+ posts and ~1000+ comments analyzed across diverse communities.
Shall I proceed with this research plan?"""

    @mcp.prompt(
        description="Create a sentiment analysis request for Reddit discussions",
        tags={"sentiment", "analysis", "emotions"}
    )
    def analyze_sentiment(
        subreddit_or_topic: str,
        is_subreddit: bool = False,
        aspects: Optional[List[str]] = None
    ) -> str:
        """Generate a sentiment analysis request for Reddit content."""
        target = f"r/{subreddit_or_topic}" if is_subreddit else f"topic '{subreddit_or_topic}'"
        aspects_text = f" focusing on aspects: {', '.join(aspects)}" if aspects else ""
        
        return f"""Please analyze the sentiment and emotional tone in Reddit discussions about {target}{aspects_text}.

## Analysis Framework:

1. **Overall Sentiment Distribution**
   - Positive, negative, neutral percentages
   - Emotional intensity levels
   - Sentiment trends over time

2. **Key Themes by Sentiment**
   - What drives positive sentiment?
   - Common complaints and frustrations
   - Neutral/informational discussions

3. **Community-Specific Patterns**
   - How sentiment varies across different subreddits
   - Differences between casual vs expert communities
   - Impact of community rules on discussion tone

4. **Notable Emotional Indicators**
   - Frequently used emotional language
   - Sarcasm and humor patterns
   - Support vs criticism ratios

5. **Engagement Correlation**
   - How sentiment affects upvotes/downvotes
   - Relationship between sentiment and comment depth
   - Controversial (mixed sentiment) topics

Please fetch at least 50 posts and analyze top comments (fetch_comments with limit=50) for accurate sentiment assessment. Include specific examples with Reddit URLs."""

    @mcp.prompt(
        description="Generate a comparison analysis between multiple Reddit communities",
        tags={"comparison", "communities", "analysis"}
    )
    def compare_communities(
        subreddits: List[str],
        comparison_aspects: Optional[List[str]] = None
    ) -> str:
        """Create a structured comparison request for multiple subreddits."""
        if not comparison_aspects:
            comparison_aspects = [
                "content focus", "community culture", "moderation style",
                "expertise level", "engagement patterns"
            ]
        
        subreddit_list = ", ".join([f"r/{s}" for s in subreddits])
        aspects_list = "\n".join([f"   - {aspect}" for aspect in comparison_aspects])
        
        return f"""Please conduct a comprehensive comparison analysis of these Reddit communities: {subreddit_list}

## Comparison Framework:

### Data Collection Phase:
1. Use fetch_multiple_subreddits_tool(subreddit_names={subreddits}, limit_per_subreddit=15)
2. Fetch subreddit metadata using reddit://subreddit/{{name}}/about for each
3. Analyze top 5 posts from each with fetch_comments(comment_limit=30)

### Comparison Dimensions:
{aspects_list}

### Analysis Structure:

1. **Community Profiles**
   - Size and activity metrics
   - Stated purpose and rules
   - Typical post types

2. **Content Analysis**
   - Common topics and themes
   - Content quality and depth
   - Original content vs shares/links

3. **Engagement Patterns**
   - Average upvotes/comments
   - Response time and activity peaks
   - User retention indicators

4. **Cultural Differences**
   - Tone and communication style
   - Newcomer friendliness
   - Inside jokes and community norms

5. **Unique Value Propositions**
   - What each community offers uniquely
   - Overlaps and differentiators
   - Recommended use cases for each

Provide specific examples with Reddit URLs demonstrating each community's characteristics."""

    @mcp.prompt(
        description="Find and analyze trending topics across Reddit",
        tags={"trending", "discovery", "current-events"}
    )
    def trending_analysis(
        category: Optional[str] = None,
        time_window: str = "day",
        min_engagement: int = 100
    ) -> str:
        """Generate a request to identify and analyze trending topics on Reddit."""
        category_filter = f" in {category}" if category else " across all topics"
        
        return f"""Please identify and analyze trending discussions on Reddit{category_filter} from the past {time_window}.

## Trending Analysis Protocol:

### Phase 1: Trend Discovery
1. Fetch hot posts from popular subreddits using fetch_multiple_subreddits_tool
2. Search for rapidly rising topics: search_all_reddit(sort='hot', time_filter='{time_window}')
3. Focus on posts with {min_engagement}+ upvotes/comments

### Phase 2: Trend Categorization
- Breaking news and current events
- Viral content and memes
- Emerging discussions and debates
- Technology and product launches
- Community-specific trends

### Phase 3: Momentum Analysis
For each trending topic:
- Growth rate (upvotes/hour)
- Cross-subreddit spread
- Comment velocity and engagement depth
- Sentiment trajectory

### Phase 4: Deep Dive (Top 5 Trends)
Use fetch_comments(comment_limit=100) on the top post for each trend to understand:
- Why it's trending
- Community reaction patterns
- Key discussion points
- Potential longevity

### Phase 5: Predictive Insights
- Topics likely to continue trending
- Emerging topics to watch
- Sentiment shifts to monitor

Include Reddit URLs for all referenced posts and highlight the single most impactful trend."""

    @mcp.prompt(
        description="Create a deep dive research plan for exhaustive single-topic analysis",
        tags={"deep-dive", "research", "comprehensive"}
    )
    def deep_dive(
        topic: str,
        historical_range: str = "year",
        min_posts_to_analyze: int = 100,
        min_comments_to_analyze: int = 1000
    ) -> str:
        """Generate an exhaustive research plan for deep topic investigation."""
        return f"""I'll conduct an exhaustive deep-dive analysis on '{topic}' covering {historical_range} of Reddit history.

## Deep Dive Research Protocol:

### Phase 1: Comprehensive Community Mapping
1. discover_reddit_resources('{topic}', discovery_depth='comprehensive') - find ALL relevant communities
2. Batch discover with related terms to ensure no community is missed
3. Document all communities, even tangentially related ones

### Phase 2: Systematic Data Collection
Target: Minimum {min_posts_to_analyze} posts and {min_comments_to_analyze} comments

**Wave 1 - Primary Communities (Top 5)**
- fetch_multiple_subreddits_tool with limit_per_subreddit=20
- Cover hot, top, and new to get temporal diversity

**Wave 2 - Secondary Communities (Next 10)**  
- fetch_multiple_subreddits_tool with limit_per_subreddit=10
- Focus on specialized/niche perspectives

**Wave 3 - Historical Mining**
- search_all_reddit('{topic}', time_filter='year', limit=50)
- search_all_reddit('{topic}', time_filter='month', limit=25) for recent
- search_all_reddit('{topic}', sort='top', limit=25) for influential posts

### Phase 3: Comment Deep Dive
- Fetch comments for ALL posts with 100+ upvotes (fetch_comments, limit=100)
- Fetch comments for posts with 50+ comments regardless of upvotes
- Total target: {min_comments_to_analyze}+ comments across all discussions

### Phase 4: Multi-Dimensional Analysis
1. **Temporal Evolution**: How has discussion changed over time?
2. **Community Perspectives**: How do different communities view this topic?
3. **Expertise Levels**: Beginner vs expert discussions
4. **Controversy Mapping**: Divisive aspects and debate points
5. **Solution Patterns**: Common advice and recommendations
6. **Myth Busting**: Misconceptions vs factual consensus

### Phase 5: Comprehensive Synthesis
- Executive summary with key findings
- Detailed thematic analysis with examples
- Community-by-community breakdown
- Timeline of major developments
- FAQ compiled from common questions
- Expert insights from highly upvoted technical comments
- EVERY claim backed by Reddit URL citations

This exhaustive approach ensures no significant perspective is missed. Proceed?"""

    @mcp.prompt(
        description="Generate proper citation format for Reddit content",
        tags={"citation", "reference", "documentation"},
        meta={"version": "1.0", "style": "academic"}
    )
    def citation_guide(
        include_examples: bool = True,
        citation_style: str = "inline"
    ) -> List[Message]:
        """Create a guide for properly citing Reddit content in research."""
        messages = [
            Message(
                f"Here's how to properly cite Reddit content using {citation_style} citations:",
                role="assistant"
            ),
            Message(
                "## Citation Requirements:\n\n"
                "1. **Every factual claim** must include the source Reddit URL\n"
                "2. **User attribution** format: u/username or [u/username]\n"
                "3. **Subreddit references** format: r/subreddit\n"
                "4. **Upvote counts** provide credibility context\n"
                "5. **Timestamps** for temporal context\n"
                "6. **Comment permalinks** for specific discussions"
            )
        ]
        
        if include_examples:
            messages.append(Message(
                "## Citation Examples:\n\n"
                "**For posts:**\n"
                "> According to a highly upvoted analysis [↑2,451] in r/science, "
                "the study shows... ([u/ResearcherName](https://reddit.com/r/science/comments/abc123/))\n\n"
                "**For comments:**\n"
                "> As [u/ExpertUser] explains in their detailed response [↑342]: "
                "\"Quote from comment...\" ([permalink](https://reddit.com/r/tech/comments/xyz789/comment/def456/))\n\n"
                "**For community consensus:**\n"
                "> The r/python community generally agrees (based on 15+ posts analyzed) "
                "that... [r/python search results](https://reddit.com/r/python/search?q=topic)\n\n"
                "**For controversial topics:**\n"
                "> This remains debated, with r/politics [↑1,234] arguing X "
                "([link](https://reddit.com/...)) while r/economics [↑892] contends Y ([link](https://reddit.com/...))"
            ))
            
        messages.append(Message(
            "Remember: Credibility comes from transparent sourcing. "
            "Always provide enough context for readers to evaluate the source's reliability. "
            "Include URLs for EVERY Reddit reference made."
        ))
        
        return messages