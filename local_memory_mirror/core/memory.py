"""
Memory management for Local Byterover Memory Mirror
Handles content storage, retrieval, and context management
"""

import logging
from typing import Optional, Dict, List, Any, Set
from datetime import datetime, timedelta
from .database import get_database_manager

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages memory entries and content retrieval"""

    def __init__(self):
        self.db = get_database_manager()

    def store_memory(self, content: str, content_type: str = 'general',
                    agent_id: Optional[str] = None, tags: Optional[List[str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store new memory entry with deduplication"""

        entry = {
            'content': content,
            'content_type': content_type,
            'agent_id': agent_id,
            'tags': tags or [],
            'metadata': metadata or {},
            'timestamp': datetime.now().timestamp()
        }

        memory_id = self.db.insert_memory_entry(entry)

        # Log attribution if agent provided
        if agent_id:
            self.db.log_attribution({
                'agent_id': agent_id,
                'action_type': 'create',
                'target_type': 'memory',
                'target_id': memory_id,
                'quality_score': 0.5
            })

        logger.info(f"Stored memory entry: {memory_id} (type: {content_type})")
        return memory_id

    def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific memory entry"""
        result = self.db.get_memory_entry(memory_id)
        if result:
            # Log retrieval attribution
            agent_context = getattr(self, '_current_agent', None)
            if agent_context:
                self.db.log_attribution({
                    'agent_id': agent_context,
                    'action_type': 'query',
                    'target_type': 'memory',
                    'target_id': memory_id
                })
        return result

    def search_memories(self, query: str = "", content_type: Optional[str] = None,
                       agent_id: Optional[str] = None, tags: Optional[List[str]] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories with various filters"""

        base_query = "SELECT * FROM memory_entries WHERE 1=1"
        params = []
        conditions = []

        # Content search (simple text matching for now)
        if query:
            conditions.append("content LIKE ?")
            params.append(f"%{query}%")

        # Type filter
        if content_type:
            conditions.append("content_type = ?")
            params.append(content_type)

        # Agent filter
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        # Tags filter (JSON array search)
        if tags:
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")

        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Order by relevance/timestamp and limit
        base_query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        results = self.db.execute_query(base_query, tuple(params))

        # Log search attribution
        agent_context = getattr(self, '_current_agent', None)
        if agent_context and results:
            self.db.log_attribution({
                'agent_id': agent_context,
                'action_type': 'search',
                'target_type': 'memory_batch',
                'target_id': 'multiple',
                'context': {'query': query, 'results_count': len(results)}
            })

        return results

    def get_context_for_task(self, task_description: str,
                           agent_capabilities: Optional[Dict[str, Any]] = None,
                           max_memories: int = 5) -> List[Dict[str, Any]]:
        """Get relevant memories for a specific task"""

        # Extract keywords from task description
        keywords = self._extract_keywords(task_description)

        # Build search terms
        search_terms = []
        for keyword in keywords:
            if len(keyword) > 3:  # Skip very short words
                search_terms.append(keyword)

        # Search for relevant memories
        context_memories = []
        for term in search_terms[:3]:  # Limit to top 3 keywords
            memories = self.search_memories(
                query=term,
                limit=max_memories // len(search_terms) + 1
            )
            context_memories.extend(memories)

        # Remove duplicates and sort by relevance
        seen_ids = set()
        unique_memories = []
        for memory in context_memories:
            if memory['id'] not in seen_ids:
                seen_ids.add(memory['id'])
                unique_memories.append(memory)

        # Sort by timestamp (most recent first) and limit results
        unique_memories.sort(key=lambda x: x['timestamp'], reverse=True)
        return unique_memories[:max_memories]

    def update_memory_quality(self, memory_id: str, quality_score: float,
                             feedback: Optional[str] = None) -> bool:
        """Update memory quality score based on usage feedback"""

        query = "UPDATE memory_entries SET quality_score = ? WHERE id = ?"
        params = (quality_score, memory_id)

        success = bool(self.db.execute_update(query, params))

        if success and feedback:
            # Store feedback as metadata
            metadata_query = "UPDATE memory_entries SET metadata = json_patch(metadata, ?) WHERE id = ?"
            self.db.execute_update(metadata_query, (f'{{"feedback": "{feedback}"}}', memory_id))

        return success

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""

        # Get total count
        total_query = "SELECT COUNT(*) as total FROM memory_entries"
        total_result = self.db.execute_query(total_query)[0]

        # Get type breakdown
        type_query = "SELECT content_type, COUNT(*) as count FROM memory_entries GROUP BY content_type"
        type_results = self.db.execute_query(type_query)

        # Get recent activity
        recent_query = "SELECT COUNT(*) as recent FROM memory_entries WHERE timestamp > ?"
        week_ago = (datetime.now() - timedelta(days=7)).timestamp()
        recent_result = self.db.execute_query(recent_query, (week_ago,))[0]

        # Get agent contributions
        agent_query = "SELECT agent_id, COUNT(*) as contributions FROM memory_entries WHERE agent_id IS NOT NULL GROUP BY agent_id ORDER BY contributions DESC LIMIT 5"
        agent_results = self.db.execute_query(agent_query)

        return {
            'total_memories': total_result['total'],
            'memories_by_type': {row['content_type']: row['count'] for row in type_results},
            'recent_memories': recent_result['recent'],
            'top_contributors': agent_results
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = text.lower().split()
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Return top 10 keywords

    def set_current_agent(self, agent_id: str):
        """Set the current agent context for attribution"""
        self._current_agent = agent_id

# Global memory manager instance
_memory_instance = None

def get_memory_manager() -> MemoryManager:
    """Get singleton memory manager instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryManager()
    return _memory_instance
