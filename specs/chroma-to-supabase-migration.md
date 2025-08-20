# Chroma DB to Supabase Vector Database Migration Specification

## Executive Summary

This document outlines the complete technical specification for migrating the Reddit MCP server's vector database from a local Chroma DB instance to Supabase's cloud-based pgvector implementation. The migration will enable API-based access to the vector database, eliminate local storage requirements, and solve the GitHub repository size limitation issue.

## Current State Analysis

### Existing Architecture

#### Chroma DB Implementation
- **Location**: `/src/tools/db/data/subreddit_vectors/`
- **Collection Name**: `reddit_subreddits`
- **Vector Dimensions**: 384 (using gte-small model)
- **Total Records**: ~20,000+ indexed subreddits
- **Storage Size**: Too large for GitHub repository
- **Access Pattern**: Local file-based, synchronous queries

#### Data Schema
```python
{
    'id': str,              # Reddit subreddit ID
    'name': str,            # Subreddit name (e.g., "Python")
    'title': str,           # Subreddit title
    'description': str,     # Public description
    'sidebar': str,         # Sidebar content (truncated to 2000 chars)
    'subscribers': int,     # Subscriber count
    'created_utc': float,   # Creation timestamp
    'over18': bool,         # NSFW flag
    'url': str,             # Full Reddit URL
    'indexed_at': str       # ISO timestamp of indexing
}
```

#### Current Usage
1. **Indexer Script** (`reddit_subreddit_indexer.py`): Discovers and indexes subreddits
2. **Discovery Tool** (`discover.py`): Performs semantic search on indexed data
3. **Server Integration** (`server.py`): Exposes discovery through MCP protocol

## Target Architecture

### Supabase pgvector Implementation

#### Database Schema

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Main table for Reddit subreddits
CREATE TABLE reddit_subreddits (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    sidebar TEXT,
    subscribers INTEGER DEFAULT 0,
    created_utc DOUBLE PRECISION,
    over18 BOOLEAN DEFAULT FALSE,
    url TEXT,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedding vector(384),
    
    -- Additional metadata for tracking
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    update_count INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_reddit_subreddits_name ON reddit_subreddits(name);
CREATE INDEX idx_reddit_subreddits_subscribers ON reddit_subreddits(subscribers DESC);
CREATE INDEX idx_reddit_subreddits_indexed_at ON reddit_subreddits(indexed_at DESC);
CREATE INDEX idx_reddit_subreddits_nsfw ON reddit_subreddits(over18);

-- HNSW index for vector similarity search
CREATE INDEX idx_reddit_subreddits_embedding 
ON reddit_subreddits 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Function for semantic search
CREATE OR REPLACE FUNCTION match_subreddits(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    include_nsfw boolean DEFAULT false
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    subscribers INTEGER,
    confidence FLOAT,
    url TEXT,
    over18 BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rs.id,
        rs.name,
        rs.subscribers,
        1 - (rs.embedding <=> query_embedding) as confidence,
        rs.url,
        rs.over18
    FROM reddit_subreddits rs
    WHERE 
        1 - (rs.embedding <=> query_embedding) > match_threshold
        AND (include_nsfw OR NOT rs.over18)
    ORDER BY rs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function for batch semantic search
CREATE OR REPLACE FUNCTION batch_match_subreddits(
    query_embeddings vector(384)[],
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    include_nsfw boolean DEFAULT false
)
RETURNS TABLE (
    query_index INTEGER,
    id TEXT,
    name TEXT,
    subscribers INTEGER,
    confidence FLOAT,
    url TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 1..array_length(query_embeddings, 1) LOOP
        RETURN QUERY
        SELECT 
            i as query_index,
            m.id,
            m.name,
            m.subscribers,
            m.confidence,
            m.url
        FROM match_subreddits(
            query_embeddings[i],
            match_threshold,
            match_count,
            include_nsfw
        ) m;
    END LOOP;
END;
$$;

-- Metadata table for tracking migration status
CREATE TABLE migration_metadata (
    id SERIAL PRIMARY KEY,
    migration_name TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    records_migrated INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB
);
```

## Migration Process

### Phase 1: Preparation (Day 1)

#### 1.1 Supabase Project Setup
```python
# Required environment variables
SUPABASE_URL = "https://[PROJECT_ID].supabase.co"
SUPABASE_ANON_KEY = "eyJ..."  # Public anon key
SUPABASE_SERVICE_KEY = "eyJ..."  # Service role key for admin operations
```

#### 1.2 Database Setup Script
```python
# setup_supabase_db.py
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_database():
    # Initialize Supabase client
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Execute schema creation SQL
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute via Supabase SQL editor or migration
    result = supabase.rpc('exec_sql', {'query': schema_sql}).execute()
    
    return result

if __name__ == "__main__":
    asyncio.run(setup_database())
```

### Phase 2: Data Export (Day 1-2)

#### 2.1 Export Script
```python
# export_from_chroma.py
import chromadb
from chromadb.config import Settings
import json
import os
from pathlib import Path
from datetime import datetime

def export_chroma_data():
    """Export all data from Chroma DB to JSON format"""
    
    # Initialize Chroma client
    db_path = Path(__file__).parent / "src/tools/db/data/subreddit_vectors"
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection("reddit_subreddits")
    
    # Get all data from collection
    all_data = collection.get(
        include=["metadatas", "embeddings", "documents"]
    )
    
    # Prepare export data
    export_data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "total_records": len(all_data['ids']),
            "collection_name": "reddit_subreddits",
            "vector_dimensions": 384
        },
        "records": []
    }
    
    # Process each record
    for i, id_val in enumerate(all_data['ids']):
        record = {
            "id": id_val,
            "metadata": all_data['metadatas'][i] if all_data['metadatas'] else {},
            "embedding": all_data['embeddings'][i] if all_data['embeddings'] else None,
            "document": all_data['documents'][i] if all_data['documents'] else None
        }
        export_data["records"].append(record)
    
    # Save to file (split into chunks if needed)
    chunk_size = 5000
    total_chunks = (len(export_data["records"]) + chunk_size - 1) // chunk_size
    
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min((chunk_idx + 1) * chunk_size, len(export_data["records"]))
        
        chunk_data = {
            "metadata": export_data["metadata"],
            "chunk_info": {
                "chunk_index": chunk_idx,
                "total_chunks": total_chunks,
                "records_in_chunk": end_idx - start_idx
            },
            "records": export_data["records"][start_idx:end_idx]
        }
        
        filename = export_dir / f"chroma_export_chunk_{chunk_idx:03d}.json"
        with open(filename, 'w') as f:
            json.dump(chunk_data, f, indent=2)
        
        print(f"Exported chunk {chunk_idx + 1}/{total_chunks} to {filename}")
    
    return export_dir

if __name__ == "__main__":
    export_dir = export_chroma_data()
    print(f"Export completed. Files saved to: {export_dir}")
```

### Phase 3: Data Migration (Day 2-3)

#### 3.1 Migration Script
```python
# migrate_to_supabase.py
import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
from tqdm import tqdm
import time

load_dotenv()

class SupabaseMigrator:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        self.batch_size = 100  # Optimal batch size for Supabase
        
    async def migrate_chunk(self, chunk_file: Path) -> Dict[str, Any]:
        """Migrate a single chunk file to Supabase"""
        
        with open(chunk_file, 'r') as f:
            chunk_data = json.load(f)
        
        records = chunk_data["records"]
        successful = 0
        failed = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            # Prepare batch for insertion
            supabase_records = []
            for record in batch:
                metadata = record["metadata"]
                
                # Transform record to Supabase format
                supabase_record = {
                    "id": record["id"],
                    "name": metadata.get("name"),
                    "title": metadata.get("title"),
                    "description": metadata.get("description"),
                    "sidebar": metadata.get("sidebar"),
                    "subscribers": metadata.get("subscribers", 0),
                    "created_utc": metadata.get("created", 0),
                    "over18": metadata.get("nsfw", False),
                    "url": metadata.get("url"),
                    "indexed_at": metadata.get("indexed_at"),
                    "embedding": record["embedding"]
                }
                supabase_records.append(supabase_record)
            
            # Insert batch
            try:
                result = self.supabase.table("reddit_subreddits").upsert(
                    supabase_records,
                    on_conflict="id"
                ).execute()
                successful += len(batch)
            except Exception as e:
                failed += len(batch)
                errors.append({
                    "batch_start": i,
                    "batch_end": i + len(batch),
                    "error": str(e)
                })
                print(f"Error migrating batch {i}-{i+len(batch)}: {e}")
            
            # Rate limiting
            time.sleep(0.1)  # Avoid overwhelming the API
        
        return {
            "chunk_file": str(chunk_file),
            "total_records": len(records),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    async def migrate_all(self, export_dir: Path) -> Dict[str, Any]:
        """Migrate all exported chunks to Supabase"""
        
        chunk_files = sorted(export_dir.glob("chroma_export_chunk_*.json"))
        
        if not chunk_files:
            raise ValueError(f"No export files found in {export_dir}")
        
        print(f"Found {len(chunk_files)} chunk files to migrate")
        
        # Track migration progress
        migration_results = []
        total_successful = 0
        total_failed = 0
        
        # Create migration metadata entry
        migration_meta = self.supabase.table("migration_metadata").insert({
            "migration_name": "chroma_to_supabase_initial",
            "status": "in_progress",
            "metadata": {
                "total_chunks": len(chunk_files),
                "source": "chroma_db",
                "target": "supabase_pgvector"
            }
        }).execute()
        
        migration_id = migration_meta.data[0]["id"]
        
        # Process each chunk
        for chunk_file in tqdm(chunk_files, desc="Migrating chunks"):
            result = await self.migrate_chunk(chunk_file)
            migration_results.append(result)
            total_successful += result["successful"]
            total_failed += result["failed"]
            
            # Update progress
            self.supabase.table("migration_metadata").update({
                "records_migrated": total_successful,
                "metadata": {
                    "processed_chunks": len(migration_results),
                    "total_chunks": len(chunk_files),
                    "failed_records": total_failed
                }
            }).eq("id", migration_id).execute()
        
        # Finalize migration
        self.supabase.table("migration_metadata").update({
            "completed_at": "now()",
            "status": "completed" if total_failed == 0 else "completed_with_errors",
            "records_migrated": total_successful,
            "error_message": f"{total_failed} records failed" if total_failed > 0 else None
        }).eq("id", migration_id).execute()
        
        return {
            "total_chunks": len(chunk_files),
            "total_successful": total_successful,
            "total_failed": total_failed,
            "migration_id": migration_id,
            "results": migration_results
        }
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify the migration was successful"""
        
        # Count total records
        count_result = self.supabase.table("reddit_subreddits").select(
            "id", count="exact"
        ).execute()
        
        total_records = count_result.count
        
        # Test semantic search
        test_queries = ["python programming", "machine learning", "gaming"]
        search_results = []
        
        for query in test_queries:
            # Generate embedding for query (using existing method)
            # This would use the same embedding model as the original system
            embedding = await self.generate_test_embedding(query)
            
            result = self.supabase.rpc("match_subreddits", {
                "query_embedding": embedding,
                "match_threshold": 0.7,
                "match_count": 5
            }).execute()
            
            search_results.append({
                "query": query,
                "results_count": len(result.data),
                "top_match": result.data[0]["name"] if result.data else None
            })
        
        return {
            "total_records": total_records,
            "search_tests": search_results,
            "status": "verified" if total_records > 0 else "failed"
        }
    
    async def generate_test_embedding(self, text: str) -> List[float]:
        """Generate a test embedding (placeholder - use actual model)"""
        # This should use the same embedding model as the original system
        # For testing, return a random vector
        return np.random.randn(384).tolist()

async def main():
    migrator = SupabaseMigrator()
    
    # Step 1: Migrate data
    export_dir = Path("exports")
    print("Starting migration...")
    migration_result = await migrator.migrate_all(export_dir)
    print(f"Migration completed: {migration_result}")
    
    # Step 2: Verify migration
    print("Verifying migration...")
    verification = await migrator.verify_migration()
    print(f"Verification result: {verification}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 4: Code Integration (Day 3-4)

#### 4.1 New Discovery Module
```python
# src/tools/discover_supabase.py
"""Subreddit discovery using Supabase pgvector search."""

import os
import json
from typing import Dict, List, Optional, Union, Any
from supabase import create_client, Client
import numpy as np

class SupabaseDiscovery:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
    def discover_subreddits(
        self,
        query: Optional[str] = None,
        queries: Optional[Union[List[str], str]] = None,
        limit: int = 10,
        include_nsfw: bool = False
    ) -> Dict[str, Any]:
        """
        Search for subreddits using semantic similarity search via Supabase.
        """
        
        # Handle batch queries
        if queries:
            if isinstance(queries, str):
                try:
                    if queries.strip().startswith('[') and queries.strip().endswith(']'):
                        queries = json.loads(queries)
                    else:
                        queries = [queries]
                except (json.JSONDecodeError, ValueError):
                    queries = [queries]
            
            batch_results = {}
            
            for search_query in queries:
                # Generate embedding for query
                embedding = self._generate_embedding(search_query)
                
                # Search via Supabase
                result = self._search_supabase(
                    embedding, limit, include_nsfw
                )
                batch_results[search_query] = result
            
            return {
                "batch_mode": True,
                "total_queries": len(queries),
                "results": batch_results
            }
        
        # Handle single query
        elif query:
            embedding = self._generate_embedding(query)
            return self._search_supabase(embedding, limit, include_nsfw)
        
        else:
            return {
                "error": "Either 'query' or 'queries' parameter must be provided",
                "subreddits": [],
                "summary": {
                    "total_found": 0,
                    "returned": 0,
                    "coverage": "error"
                }
            }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using the same model as indexing"""
        # This should use the same embedding generation as the indexer
        # For now, placeholder - integrate with actual embedding model
        # Options:
        # 1. Use OpenAI API
        # 2. Use local model (sentence-transformers)
        # 3. Use Supabase Edge Function
        
        # Placeholder: return random vector for testing
        return np.random.randn(384).tolist()
    
    def _search_supabase(
        self,
        embedding: List[float],
        limit: int,
        include_nsfw: bool
    ) -> Dict[str, Any]:
        """Perform semantic search via Supabase RPC"""
        
        try:
            # Call Supabase RPC function
            result = self.supabase.rpc("match_subreddits", {
                "query_embedding": embedding,
                "match_threshold": 0.7,
                "match_count": limit,
                "include_nsfw": include_nsfw
            }).execute()
            
            # Process results
            subreddits = []
            for row in result.data:
                subreddits.append({
                    "name": row["name"],
                    "subscribers": row["subscribers"],
                    "confidence": round(row["confidence"], 3),
                    "url": row["url"]
                })
            
            return {
                "subreddits": subreddits,
                "summary": {
                    "total_found": len(subreddits),
                    "returned": len(subreddits),
                    "has_more": False
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to search Supabase: {str(e)}",
                "subreddits": [],
                "summary": {
                    "total_found": 0,
                    "returned": 0,
                    "has_more": False
                }
            }

# Global instance for backward compatibility
_discovery = None

def get_discovery():
    global _discovery
    if _discovery is None:
        _discovery = SupabaseDiscovery()
    return _discovery

# Wrapper function for backward compatibility
def discover_subreddits(
    query: Optional[str] = None,
    queries: Optional[Union[List[str], str]] = None,
    limit: int = 10,
    include_nsfw: bool = False
) -> Dict[str, Any]:
    """Backward compatible wrapper for Supabase discovery"""
    discovery = get_discovery()
    return discovery.discover_subreddits(query, queries, limit, include_nsfw)
```

#### 4.2 Configuration Updates
```python
# src/config.py updates
import os
from typing import Optional, Dict

def get_supabase_config(config: Optional[Dict] = None) -> Dict:
    """Get Supabase configuration from environment or config"""
    
    supabase_config = {
        "url": None,
        "anon_key": None,
        "service_key": None,
        "use_supabase": False
    }
    
    # Check config parameter first
    if config:
        supabase_config["url"] = config.get("SUPABASE_URL")
        supabase_config["anon_key"] = config.get("SUPABASE_ANON_KEY")
        supabase_config["service_key"] = config.get("SUPABASE_SERVICE_KEY")
    
    # Fall back to environment variables
    if not supabase_config["url"]:
        supabase_config["url"] = os.getenv("SUPABASE_URL")
    if not supabase_config["anon_key"]:
        supabase_config["anon_key"] = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_config["service_key"]:
        supabase_config["service_key"] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Enable Supabase if configuration is complete
    if supabase_config["url"] and supabase_config["anon_key"]:
        supabase_config["use_supabase"] = True
    
    return supabase_config

# Add to existing config initialization
SUPABASE_CONFIG = get_supabase_config()
USE_SUPABASE_DISCOVERY = SUPABASE_CONFIG["use_supabase"]
```

#### 4.3 Server Integration
```python
# Update src/server.py
from src.config import USE_SUPABASE_DISCOVERY

if USE_SUPABASE_DISCOVERY:
    from src.tools.discover_supabase import discover_subreddits
else:
    from src.tools.discover import discover_subreddits

# Rest of the server code remains the same
# The discover_subreddits function signature is identical
```

### Phase 5: Testing & Validation (Day 4-5)

#### 5.1 Test Suite
```python
# tests/test_supabase_migration.py
import pytest
import asyncio
from src.tools.discover_supabase import SupabaseDiscovery
from src.tools.discover import discover_subreddits as chroma_discover

class TestSupabaseMigration:
    
    @pytest.fixture
    def supabase_discovery(self):
        return SupabaseDiscovery()
    
    def test_single_query(self, supabase_discovery):
        """Test single query search"""
        result = supabase_discovery.discover_subreddits(
            query="python programming",
            limit=10
        )
        
        assert "subreddits" in result
        assert len(result["subreddits"]) <= 10
        assert result["summary"]["total_found"] >= 0
    
    def test_batch_query(self, supabase_discovery):
        """Test batch query search"""
        queries = ["python", "javascript", "rust"]
        result = supabase_discovery.discover_subreddits(
            queries=queries,
            limit=5
        )
        
        assert result["batch_mode"] == True
        assert len(result["results"]) == 3
    
    def test_nsfw_filtering(self, supabase_discovery):
        """Test NSFW filtering"""
        result_without = supabase_discovery.discover_subreddits(
            query="general",
            limit=20,
            include_nsfw=False
        )
        
        result_with = supabase_discovery.discover_subreddits(
            query="general",
            limit=20,
            include_nsfw=True
        )
        
        # Should have same or more results with NSFW included
        assert len(result_with["subreddits"]) >= len(result_without["subreddits"])
    
    def test_compare_with_chroma(self):
        """Compare results between Chroma and Supabase"""
        test_queries = [
            "python programming",
            "machine learning",
            "web development",
            "gaming",
            "cooking"
        ]
        
        for query in test_queries:
            chroma_result = chroma_discover(query=query, limit=10)
            supabase_result = supabase_discovery.discover_subreddits(
                query=query, limit=10
            )
            
            # Check that both return results
            assert len(chroma_result["subreddits"]) > 0
            assert len(supabase_result["subreddits"]) > 0
            
            # Check for overlap in top results
            chroma_names = {s["name"] for s in chroma_result["subreddits"][:5]}
            supabase_names = {s["name"] for s in supabase_result["subreddits"][:5]}
            
            overlap = chroma_names & supabase_names
            assert len(overlap) > 0, f"No overlap for query: {query}"
```

#### 5.2 Performance Testing
```python
# tests/test_performance.py
import time
import statistics

def test_query_performance(discovery):
    """Test query response times"""
    
    queries = ["python", "java", "rust", "go", "javascript"] * 10
    times = []
    
    for query in queries:
        start = time.time()
        result = discovery.discover_subreddits(query=query, limit=10)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
    
    print(f"Average response time: {avg_time:.3f}s")
    print(f"Median response time: {median_time:.3f}s")
    print(f"95th percentile: {p95_time:.3f}s")
    
    # Assert performance requirements
    assert avg_time < 1.0, "Average response time should be under 1 second"
    assert p95_time < 2.0, "95th percentile should be under 2 seconds"
```

### Phase 6: Deployment (Day 5)

#### 6.1 Environment Configuration
```bash
# .env.production
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...  # Only for admin operations

# Feature flags
USE_SUPABASE_DISCOVERY=true
CHROMA_FALLBACK_ENABLED=true  # Enable fallback during transition

# Reddit API (unchanged)
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=xxx
```

#### 6.2 Deployment Checklist
- [ ] Supabase database schema created
- [ ] Data migration completed successfully
- [ ] Environment variables configured
- [ ] Code updates deployed
- [ ] Tests passing
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Rollback plan ready

#### 6.3 Rollback Plan
```python
# rollback.py
import os

def rollback_to_chroma():
    """Emergency rollback to Chroma DB"""
    
    # Update environment variable
    os.environ["USE_SUPABASE_DISCOVERY"] = "false"
    
    # Restart server
    os.system("systemctl restart reddit-mcp-server")
    
    print("Rolled back to Chroma DB")
    
    # Alert team
    send_alert("Rolled back to Chroma DB due to issues")
```

## Post-Migration Tasks

### Cleanup
1. Remove Chroma DB files from repository
2. Update `.gitignore` to exclude local vector data
3. Remove Chroma DB dependencies from `pyproject.toml`
4. Archive export files

### Documentation Updates
1. Update README with Supabase setup instructions
2. Document new environment variables
3. Update API documentation
4. Create troubleshooting guide

### Monitoring
1. Set up Supabase dashboard alerts
2. Monitor query performance
3. Track API usage and costs
4. Set up error logging

## Cost Analysis

### Supabase Costs
- **Free Tier**: 500MB database, 2GB bandwidth
- **Pro Tier** ($25/month): 8GB database, 50GB bandwidth
- **Estimated Usage**: ~100MB for 20,000 records with vectors

### Comparison
- **Chroma DB**: Free but requires local storage
- **Supabase**: Free tier sufficient for current scale

## Risk Mitigation

### Identified Risks
1. **API Rate Limits**: Mitigated by batch operations
2. **Network Latency**: Mitigated by caching
3. **Data Loss**: Mitigated by backups and gradual migration
4. **Service Downtime**: Mitigated by fallback to Chroma

### Contingency Plans
1. **Parallel Operation**: Run both systems during transition
2. **Gradual Rollout**: Test with subset of users first
3. **Backup Strategy**: Daily exports from Supabase
4. **Fallback Logic**: Automatic switch to Chroma if Supabase fails

## Success Metrics

### Technical Metrics
- [ ] 100% data migration success
- [ ] Query response time < 500ms (p50)
- [ ] Query response time < 1s (p95)
- [ ] 99.9% uptime

### Business Metrics
- [ ] Zero service disruption during migration
- [ ] Reduced repository size by >90%
- [ ] Enabled cloud deployment capability
- [ ] Improved scalability for future growth

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Preparation | 1 day | Supabase setup, schema creation |
| Data Export | 1 day | Export from Chroma, validation |
| Migration | 1 day | Transfer to Supabase, verification |
| Integration | 1 day | Code updates, testing |
| Deployment | 1 day | Production deployment, monitoring |
| **Total** | **5 days** | **Complete migration** |

## Appendix

### A. Embedding Model Integration
The system currently uses embeddings with 384 dimensions. Integration options:

1. **OpenAI API**: Use text-embedding-3-small
2. **Local Model**: Use sentence-transformers (all-MiniLM-L6-v2)
3. **Supabase Edge Function**: Deploy embedding generation to edge

### B. Security Considerations
- Use row-level security (RLS) for multi-tenant access
- Implement API key rotation
- Audit log all administrative operations
- Encrypt sensitive metadata

### C. Future Enhancements
1. **Real-time Updates**: Use Supabase realtime for live indexing
2. **Advanced Search**: Implement hybrid search (vector + keyword)
3. **Analytics**: Track search patterns and popular queries
4. **Caching**: Implement Redis caching for frequent queries
5. **Multi-region**: Deploy to multiple regions for lower latency

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Author: Claude Code Migration Assistant*