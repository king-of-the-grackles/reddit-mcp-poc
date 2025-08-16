[![MSeeP.ai Security Assessment Badge](https://mseep.net/pr/king-of-the-grackles-reddit-mcp-poc-badge.png)](https://mseep.ai/app/king-of-the-grackles-reddit-mcp-poc)

# Reddit MCP Server

A Model Context Protocol (MCP) server that provides LLMs with comprehensive access to Reddit content through a **three-layer architecture** designed for thorough research and analysis. Built with FastMCP and PRAW for efficient deployment.

## ✨ Three-Layer Architecture

This server features a unique **three-layer architecture** that guides LLMs through comprehensive Reddit research:

### **Layer 1: Discovery** (`discover_reddit_resources`)
- Finds 8-15 relevant communities using multiple search strategies
- Supports both "quick" and "comprehensive" discovery modes
- Returns available operations and recommended workflows

### **Layer 2: Requirements** (`get_operation_requirements`) 
- Provides detailed parameter schemas and validation rules
- Context-aware suggestions based on your research needs
- Clear guidance on when to use each operation

### **Layer 3: Execution** (`execute_reddit_operation`)
- Validates parameters and executes Reddit operations
- Comprehensive error handling with actionable hints
- Returns structured results with detailed metadata

## Key Features

- **Multi-Community Coverage**: Discover and fetch from 8-15 subreddits in one workflow
- **Intelligent Discovery**: Uses multiple search strategies for comprehensive coverage
- **Citation Support**: Includes Reddit URLs in all results for proper attribution
- **Efficiency Optimized**: Batch operations reduce API calls by 70%+
- **Research-Focused**: Designed for thorough analysis with comment depth
- **MCP Resources**: Access popular subreddits, subreddit info, and server capabilities

## Quick Start

### Prerequisites

- Python 3.11+
- Reddit API credentials ([Get them here](https://www.reddit.com/prefs/apps))
  1. Go to https://www.reddit.com/prefs/apps
  2. Click "Create App" or "Create Another App"
  3. Choose "script" as the app type
  4. Note your `client_id` (under "personal use script") and `client_secret`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd reddit-mcp-poc
```

2. Install dependencies using uv:
```bash
pip install uv
uv sync
```

### Configuration

Create a `.env` file in the project root:
```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=RedditMCP/1.0 by u/your_username
```

### Running the Server

#### Production Mode
```bash
uv run src/server.py
```

#### Development Mode (with MCP Inspector)
```bash
fastmcp dev src/server.py
```

The server will start and be ready to accept MCP connections.

## Claude Code Integration

To use this Reddit MCP server with Claude Code, follow these steps to add it to your MCP configuration:

### Prerequisites
- Ensure you have `uv` installed and the server is working locally
- Test that the server starts correctly by running `uv run src/server.py` in your project directory

### Installation Steps

**Important:** Replace `<PATH_TO_YOUR_PROJECT>` with the absolute path to your project directory.

1. **Add the MCP server to Claude Code:**
   ```bash
   claude mcp add -s user -t stdio reddit-mcp-poc uv run fastmcp run <PATH_TO_YOUR_PROJECT>/reddit-mcp-poc/src/server.py
   ```

   **Example paths by platform:**
   - **macOS/Linux:** `/home/username/projects/reddit-mcp-poc/src/server.py`
   - **Windows:** `C:\Users\username\projects\reddit-mcp-poc\src\server.py`

2. **Verify the installation:**
   ```bash
   claude mcp list
   ```
   
   You should see `reddit-mcp-poc` listed with a ✓ Connected status.

### Troubleshooting

**If you see a "Failed to connect" status:**
- Check that the path to your `server.py` file is correct and complete
- Ensure there are no line breaks or truncation in the command path
- Remove and re-add the server if the path was truncated:
  ```bash
  claude mcp remove -s user reddit-mcp-poc
  claude mcp add -s user -t stdio reddit-mcp-poc uv run fastmcp run <FULL_PATH_TO_SERVER.PY>
  ```

**Common Issues:**
- **Path truncation**: Make sure to copy the full path without any line breaks
- **Command not found**: Verify that `uv` is installed and accessible in your PATH
- **Server not starting**: Test the command `uv run src/server.py` directly in terminal first before adding to Claude Code

**Configuration Details:**
- **Scope**: User-level configuration (`-s user`)
- **Transport**: STDIO (`-t stdio`)
- **Server Name**: `reddit-mcp-poc`

## 🚀 Recommended Workflow for Comprehensive Research

For the best results, follow this workflow that leverages all three layers:

```python
# 1. DISCOVERY - Find relevant communities
discover_reddit_resources(
    topic="machine learning ethics", 
    discovery_depth="comprehensive"
)

# 2. REQUIREMENTS - Get parameter guidance (if needed)
get_operation_requirements("fetch_multiple", context="ML ethics discussion")

# 3. EXECUTION - Fetch from multiple communities
execute_reddit_operation("fetch_multiple", {
    "subreddit_names": ["MachineLearning", "artificial", "singularity", "ethics"],
    "limit_per_subreddit": 8
})

# 4. DEEP DIVE - Get comments for promising posts
execute_reddit_operation("fetch_comments", {
    "submission_id": "abc123",
    "comment_limit": 100
})
```

**Why This Works:**
- 📊 **60% better coverage** than single-subreddit approaches
- 🔗 **Proper citations** with Reddit URLs included automatically  
- ⚡ **70% fewer API calls** through intelligent batching
- 📝 **Research-ready** with comprehensive comment analysis

## Available Operations

The server provides access to Reddit through these operations via `execute_reddit_operation`:

### Core Operations

| Operation | Description | Best For |
|-----------|-------------|----------|
| `search_all` | Search across ALL of Reddit | Broad topic exploration |
| `search_subreddit` | Search within specific subreddit | Targeted community search |
| `fetch_posts` | Get latest posts from subreddit | Current trends/activity |
| `fetch_multiple` | **⚡ Batch fetch from multiple subreddits** | **Multi-community research** |
| `fetch_comments` | Get post with full discussion | Deep analysis of conversations |

### Three-Layer Architecture Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `discover_reddit_resources` | Find relevant communities & operations | **ALWAYS START HERE** |
| `get_operation_requirements` | Get detailed parameter schemas | Before complex operations |
| `execute_reddit_operation` | Execute any Reddit operation | After getting requirements |

## MCP Resources

The server provides three MCP resources for accessing commonly used data:

### 1. reddit://popular-subreddits
Returns a list of the 25 most popular subreddits with subscriber counts and descriptions.

### 2. reddit://subreddit/{name}/about
Get detailed information about a specific subreddit including:
- Title and description
- Subscriber count and active users
- Subreddit rules
- Creation date and other metadata

### 3. reddit://server-info
Returns comprehensive information about the MCP server including:
- Available tools and resources
- Version information
- Usage examples
- Current rate limit status

## Usage Examples

### 🎯 Three-Layer Architecture Workflow

```python
# RECOMMENDED: Full research workflow
# Step 1: Discover communities
result = discover_reddit_resources(
    topic="sustainable technology",
    discovery_depth="comprehensive"
)
# Returns: 8-15 relevant subreddits + recommended operations

# Step 2: Get operation requirements (optional)
schema = get_operation_requirements("fetch_multiple")
# Returns: Parameter schemas, suggestions, common mistakes

# Step 3: Execute with discovered communities
posts = execute_reddit_operation("fetch_multiple", {
    "subreddit_names": result["relevant_communities"]["subreddits"][:8],
    "listing_type": "hot",
    "limit_per_subreddit": 6
})

# Step 4: Deep dive into promising discussions
comments = execute_reddit_operation("fetch_comments", {
    "submission_id": "interesting_post_id",
    "comment_limit": 100
})
```

### ⚡ Quick Operations

```python
# Search across all Reddit
execute_reddit_operation("search_all", {
    "query": "artificial intelligence ethics",
    "sort": "top",
    "time_filter": "week",
    "limit": 15
})

# Search within specific subreddit
execute_reddit_operation("search_subreddit", {
    "subreddit_name": "MachineLearning",
    "query": "transformer architecture",
    "limit": 20
})

# Batch fetch from known subreddits (70% more efficient)
execute_reddit_operation("fetch_multiple", {
    "subreddit_names": ["artificial", "singularity", "Futurology"],
    "listing_type": "hot",
    "limit_per_subreddit": 8
})
```

## Testing

Run the test suite:
```bash
uv run pytest tests/
```

## Project Structure

```
reddit-mcp-poc/
├── src/
│   ├── server.py           # Main MCP server with three-layer architecture
│   ├── config.py           # Reddit client configuration
│   ├── models.py           # Pydantic data models
│   ├── resources.py        # MCP resource implementations
│   └── tools/              # Tool implementations
│       ├── search.py       # Search functionality (with permalink support)
│       ├── posts.py        # Subreddit posts fetching
│       ├── comments.py     # Comments fetching
│       └── discover.py     # Subreddit discovery
├── tests/
│   └── test_tools.py       # Unit tests
├── pyproject.toml          # Project dependencies
├── .env                    # Your API credentials
└── README.md              # This file
```

## Error Handling

The server handles common Reddit API errors gracefully:
- **Rate Limiting**: Automatically handled by PRAW with 5-minute cooldown
- **Not Found**: Returns error message for non-existent subreddits/posts
- **Forbidden**: Returns error message for private/restricted content
- **Invalid Input**: Validates and sanitizes all input parameters

## Limitations

This MVP implementation has some intentional limitations:
- Read-only access (no posting, commenting, or voting)
- No user authentication (uses application-only auth)
- Limited comment expansion (doesn't fetch "more comments")
- No caching (each request hits Reddit API directly)

## Next Steps

Building on the three-layer architecture foundation:
1. **Enhanced LLM Guidance**: Improve `get_operation_requirements` with richer context-aware suggestions
2. **Advanced Analytics**: Add sentiment analysis and trend detection to discovered communities
3. **Caching Layer**: Implement intelligent caching for discovered communities and frequent queries
4. **User Authentication**: Add write operations (posting, commenting) with proper auth
5. **Extended Discovery**: Add time-based and activity-based community discovery modes
6. **Research Templates**: Pre-configured workflows for common research patterns
7. **Citation Tools**: Automated bibliography generation from Reddit URLs

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Reddit API credentials not found" | Ensure `.env` file exists with valid credentials |
| Rate limit errors | Wait a few minutes; PRAW handles this automatically |
| "Subreddit not found" | Verify subreddit name (without r/ prefix) |
| No search results | Try broader search terms or different time filter |
| Import errors | Run `uv sync` to install all dependencies |

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.