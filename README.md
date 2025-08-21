# 🔍 Reddit Research MCP Server

> **Transform Reddit into your personal research assistant** - Semantic search across 20,000+ communities with AI-powered analysis

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/Built%20with-FastMCP-orange.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Why This Server?

**Stop manually searching through Reddit.** This MCP server transforms Reddit into a structured research tool that:

- 🎯 **Discovers relevant communities you didn't know existed** - Semantic search across 22,000+ indexed subreddits
- ⚡ **Reduces API calls by 70%** - Batch operations fetch from 15 subreddits simultaneously  
- 🤖 **Automates comprehensive research** - Built-in Claude Code agent analyzes 100+ posts and comments
- 📊 **Produces professional reports** - Markdown output with full citations and sentiment analysis
- 🔗 **Provides complete traceability** - Every insight linked to its Reddit source

---

## 🚀 Quick Setup (60 Seconds)

**No credentials or configuration needed!** Connect to our hosted server:

### Claude Code
```bash
claude mcp add --scope local --transport http reddit-research-mcp https://reddit-research-mcp.fastmcp.app/mcp
```

### Cursor
```
cursor://anysphere.cursor-deeplink/mcp/install?name=reddit-research-mcp&config=eyJ1cmwiOiJodHRwczovL3JlZGRpdC1yZXNlYXJjaC1tY3AuZmFzdG1jcC5hcHAvbWNwIn0%3D
```

### OpenAI Codex CLI
```bash
codex -c 'mcp_servers.reddit-research-mcp.command=npx' \
      -c 'mcp_servers.reddit-research-mcp.args=["-y", "mcp-remote@latest", "https://reddit-research-mcp.fastmcp.app/mcp"]'
```

### Gemini CLI
```bash
gemini mcp add reddit-research-mcp https://reddit-research-mcp.fastmcp.app/mcp --transport http
```

### Direct MCP Server URL
For other AI assistants: `https://reddit-research-mcp.fastmcp.app/mcp`


## 🎨 Key Features

### 🔍 **Semantic Subreddit Discovery**
Unlike Reddit's limited native search, our vector database indexes 22,000+ active communities, understanding context and relationships to find relevant subreddits you never knew existed.

```python
# Discover communities about "sustainable living"
# Returns: ZeroWaste, BuyItForLife, Permaculture, SimpleLiving, and 10+ more
```

### ⚡ **Intelligent Batch Operations**
Fetch posts from up to 15 subreddits in a single API call - 70% more efficient than sequential requests.

```python
# One call instead of fifteen
execute_operation("fetch_multiple", {
    "subreddit_names": ["MachineLearning", "artificial", "deeplearning", ...],
    "limit_per_subreddit": 10
})
```

### 🤖 **Automated Research Agent**
A specialized Claude Code agent that conducts end-to-end research:

```bash
# In Claude Code, simply say:
"Research cryptocurrency regulation on Reddit"

# The agent automatically:
# → Discovers 15+ relevant crypto communities
# → Analyzes 100+ posts and comments
# → Generates a comprehensive report with citations
# → Saves to /reports/cryptocurrency-regulation-2025-01-19.md
```

---

## 📖 How to Use

### 🔌 Integration

Once connected via the hosted setup, the server is ready to use. Verify your connection:

```bash
# For Claude Code
claude mcp list
```

### 🛠️ Core Operations

#### Discover Communities
```python
# Find subreddits about any topic
execute_operation("discover_subreddits", {
    "topic": "machine learning",
    "limit": 15
})
```

#### Search Across Reddit
```python
# Search all of Reddit
execute_operation("search_all", {
    "query": "ChatGPT experiences",
    "time_filter": "week",
    "limit": 25
})
```

#### Batch Fetch Posts
```python
# Get posts from multiple subreddits at once
execute_operation("fetch_multiple", {
    "subreddit_names": ["technology", "programming", "coding"],
    "limit_per_subreddit": 10,
    "time_filter": "day"
})
```

#### Deep Dive with Comments
```python
# Analyze full discussions
execute_operation("fetch_comments", {
    "submission_id": "abc123",
    "comment_limit": 200,
    "sort": "best"
})
```

---

## 🗂️ Project Structure

```
reddit-research-mcp/
├── 📁 src/
│   ├── 🚀 server.py          # FastMCP server
│   ├── 🔧 config.py          # Reddit configuration
│   ├── 📊 chroma_client.py   # Vector database proxy client
│   ├── 📚 resources.py       # MCP resources
│   ├── 🎭 models.py          # Data models
│   └── 🛠️ tools/
│       ├── 🔍 search.py      # Search operations
│       ├── 📝 posts.py       # Post fetching
│       ├── 💬 comments.py    # Comment retrieval
│       └── 🎯 discover.py    # Subreddit discovery (20k+ indexed)
├── 🧪 tests/                 # Test suite
├── 📊 reports/               # Generated research reports
├── 📋 specs/                 # Architecture documentation
│   ├── agentic-discovery-architecture.md
│   ├── reddit-research-agent-spec.md
│   ├── deep-research-reddit-architecture.md
│   └── chroma-proxy-architecture.md
```

---

## 🎯 Use Cases

### 📊 Market Research
```bash
"Analyze consumer sentiment about electric vehicles across Reddit"
```

### 🔬 Academic Research
```bash
"Research how Reddit communities discuss climate change solutions"
```

### 💼 Competitive Analysis
```bash
"What are developers saying about Next.js vs Remix?"
```

### 📈 Trend Discovery
```bash
"Find emerging AI tools being discussed on Reddit this week"
```

---

## 🗄️ Vector Database Architecture

This server includes a **pre-indexed database** with 22,000+ subreddits for semantic search:

- **Zero Setup**: Works automatically via our authenticated proxy server
- **Secure Access**: Protected by API key authentication
- **Instant Discovery**: Find relevant communities using semantic similarity

---

## 🔧 Configuration

**No configuration required!** The hosted server handles all credentials and settings automatically.

### MCP Resources

Access comprehensive server documentation:

- 📖 `reddit://server-info` - Complete server capabilities, tools, prompts, and usage examples

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 🔴 "Authentication failed" | The hosted service handles authentication automatically |
| ⏱️ Rate limit errors | Automatic retry after 60 seconds |
| 🚫 "Subreddit not found" | Check spelling (use "technology" not "r/technology") |
| 🔌 MCP connection failed | Verify full path in Claude Code command |

---

## 📚 Documentation

- 📖 [Architecture Overview](specs/agentic-discovery-architecture.md)
- 🤖 [Research Agent Details](specs/reddit-research-agent-spec.md)
- 🔍 [Deep Research Architecture](specs/deep-research-reddit-architecture.md)
- 🗄️ [ChromaDB Proxy Architecture](specs/chroma-proxy-architecture.md)

---

## 🧪 Development

### For Contributors

If you're contributing to this project:

1. **Clone the repository**
   ```bash
   git clone https://github.com/king-of-the-grackles/reddit-research-mcp.git
   cd reddit-research-mcp
   ```

2. **Install dependencies**
   ```bash
   pip install uv
   uv sync
   ```

3. **Set up authentication** (contact maintainers for access)
   ```bash
   export CHROMA_PROXY_API_KEY="your-api-key"
   ```

4. **Run tests**
   ```bash
   uv run pytest tests/
   ```

**Note**: The vector database proxy requires authentication. Contact the maintainers for API access if you're contributing.

### Tech Stack

Contributions welcome! This project uses:
- 🐍 Python 3.11+ with type hints
- 📦 uv for package management
- 🚀 FastMCP for the server framework
- 🗄️ Vector search via authenticated proxy
- 🧪 Tests required for new features

---

---

<div align="center">
  
**Built with ❤️ for Reddit researchers and data enthusiasts**

[Report Issues] • [Request Features] • [Star on GitHub]

</div>