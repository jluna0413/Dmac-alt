"""
Context Intelligence Engine for Local Byterover Memory Mirror
Advanced semantic search, relevance scoring, and context-aware retrieval
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math
from difflib import SequenceMatcher

from ..core.database import get_database_manager
from ..core.memory import get_memory_manager

logger = logging.getLogger(__name__)

class ContextIntelligenceEngine:
    """Advanced context-aware memory retrieval and semantic search"""

    def __init__(self):
        self.db = get_database_manager()
        self.memory = get_memory_manager()

    def semantic_search(self, query: str, context_type: Optional[str] = None,
                       agent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search with relevance scoring and context-aware ranking
        """
        # Extract keywords and concepts from query
        query_keywords = self._extract_semantic_keywords(query)
        query_concepts = self._extract_concepts(query)

        # Get candidate memories
        candidates = self._get_candidate_memories(query, context_type, agent_id, limit * 3)

        if not candidates:
            return []

        # Calculate semantic relevance scores
        scored_results = []
        for memory in candidates:
            relevance_score = self._calculate_semantic_relevance(
                memory, query_keywords, query_concepts
            )

            if relevance_score > 0.1:  # Filter low relevance
                scored_results.append({
                    'memory': memory,
                    'relevance_score': relevance_score,
                    'semantic_match_type': self._identify_match_type(memory, query_keywords, query_concepts)
                })

        # Sort by relevance and recency
        scored_results.sort(key=lambda x: (
            x['relevance_score'] * 0.7 +  # 70% semantic relevance
            self._calculate_recency_score(x['memory']) * 0.3  # 30% recency
        ), reverse=True)

        # Return top results with enhanced metadata
        results = []
        for item in scored_results[:limit]:
            memory = item['memory']
            results.append({
                **memory,
                'semantic_relevance': item['relevance_score'],
                'match_type': item['semantic_match_type'],
                'context_similarity': self._calculate_context_similarity(query, memory),
                'search_metadata': {
                    'query_keywords_matched': [kw for kw in query_keywords if kw.lower() in memory['content'].lower()],
                    'timestamp': datetime.now().isoformat()
                }
            })

        return results

    def find_related_memories(self, memory_id: str, max_related: int = 5) -> List[Dict[str, Any]]:
        """
        Find memories related to a given memory using content similarity and context
        """
        # Get source memory
        source_memory = self.db.get_memory_entry(memory_id)
        if not source_memory:
            return []

        # Extract key concepts from source memory
        concepts = self._extract_concepts(source_memory['content'])
        keywords = self._extract_semantic_keywords(source_memory['content'])

        # Find related memories
        related = self.semantic_search(
            query=" ".join(list(concepts) + keywords),
            limit=max_related * 2
        )

        # Filter out the source memory itself and rank by relationship strength
        related_filtered = []
        for item in related:
            if item['id'] != memory_id:
                relationship_score = self._calculate_relationship_score(source_memory, item)
                if relationship_score > 0.3:  # Strong enough relationship
                    item['relationship_strength'] = relationship_score
                    item['relationship_type'] = self._identify_relationship_type(source_memory, item)
                    related_filtered.append(item)

        # Sort by relationship strength
        related_filtered.sort(key=lambda x: x['relationship_strength'], reverse=True)

        return related_filtered[:max_related]

    def build_knowledge_graph(self, topic: str, depth: int = 2) -> Dict[str, Any]:
        """
        Build a knowledge graph around a topic with interconnected memories
        """
        # Start with topic search
        initial_memories = self.semantic_search(topic, limit=10)

        if not initial_memories:
            return {'nodes': [], 'edges': [], 'topic': topic}

        # Build graph with depth
        visited_ids = set()
        nodes = []
        edges = []

        def add_memory_to_graph(memory: Dict[str, Any], current_depth: int):
            if memory['id'] in visited_ids or current_depth > depth:
                return

            visited_ids.add(memory['id'])
            nodes.append({
                'id': memory['id'],
                'content': memory['content'][:200] + "..." if len(memory['content']) > 200 else memory['content'],
                'type': memory['content_type'],
                'timestamp': memory['timestamp'],
                'depth': current_depth
            })

            if current_depth < depth:
                related = self.find_related_memories(memory['id'], max_related=3)
                for related_memory in related:
                    edges.append({
                        'source': memory['id'],
                        'target': related_memory['id'],
                        'relationship': related_memory['relationship_type'],
                        'strength': related_memory['relationship_strength']
                    })
                    add_memory_to_graph(related_memory, current_depth + 1)

        # Build graph from initial memories
        for memory in initial_memories[:3]:  # Start with top 3 most relevant
            add_memory_to_graph(memory, 0)

        return {
            'nodes': nodes,
            'edges': edges,
            'topic': topic,
            'total_memories': len(nodes),
            'generated_at': datetime.now().isoformat()
        }

    def detect_patterns(self, agent_id: str, pattern_type: str = 'temporal') -> Dict[str, Any]:
        """
        Detect patterns in agent behavior and memory usage
        """
        # Get agent's memory history
        contributions = self.db.execute_query(
            "SELECT * FROM memory_entries WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 100",
            (agent_id,)
        )

        if not contributions:
            return {'patterns': [], 'insights': []}

        if pattern_type == 'temporal':
            patterns = self._analyze_temporal_patterns(contributions)
        elif pattern_type == 'content':
            patterns = self._analyze_content_patterns(contributions)
        elif pattern_type == 'collaboration':
            patterns = self._analyze_collaboration_patterns(contributions)
        else:
            patterns = []

        return {
            'agent_id': agent_id,
            'pattern_type': pattern_type,
            'patterns': patterns,
            'insights': self._generate_behavior_insights(patterns, pattern_type),
            'analysis_timestamp': datetime.now().isoformat()
        }

    def get_context_for_conversation(self, conversation_text: str,
                                   agent_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Provide context-aware memory suggestions for an ongoing conversation
        """
        # Analyze conversation context
        conversation_concepts = self._extract_concepts(conversation_text)
        conversation_keywords = self._extract_semantic_keywords(conversation_text)
        conversation_intent = self._infer_conversation_intent(conversation_text)

        # Build intelligent query
        search_query = " ".join(list(conversation_concepts) + [conversation_intent] + conversation_keywords)
        relevant_memories = self.semantic_search(search_query, limit=5)

        # Enhance with conversation-specific metadata
        for memory in relevant_memories:
            memory['conversation_relevance'] = self._calculate_conversation_relevance(
                conversation_text, memory, conversation_intent
            )
            memory['suggested_usage'] = self._suggest_memory_usage(memory, conversation_intent)

        # Sort by conversation relevance
        relevant_memories.sort(key=lambda x: x['conversation_relevance'], reverse=True)

        return relevant_memories[:3]  # Return top 3 most relevant

    def optimize_search_cache(self):
        """
        Optimize search performance by building intelligent caches
        """
        # This would build semantic indexes and caches in a production system
        # For now, it's a placeholder for future performance optimizations

        logger.info("Search cache optimization completed (placeholder)")

    # Private helper methods

    def _extract_semantic_keywords(self, text: str) -> List[str]:
        """Extract semantically meaningful keywords"""
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }

        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        # Weight by frequency and position
        keyword_counts = Counter(keywords)
        weighted_keywords = []
        for word, count in keyword_counts.most_common(15):
            # Boost words that appear multiple times or are at the beginning
            weight = count + (1 if words.index(word) < 5 else 0)
            weighted_keywords.extend([word] * weight)

        return weighted_keywords[:10]

    def _extract_concepts(self, text: str) -> set:
        """Extract key concepts from text"""
        # Simple concept extraction - could be enhanced with NLP
        concepts = set()

        # Look for common technical concepts
        tech_patterns = [
            r'\b(api|rest|graphql|database|query|function|module|class|object)\b',
            r'\b(memory|cache|storage|retrieval|search|semantic)\b',
            r'\b(learning|intelligence|analysis|processing)\b',
            r'\b(sync|async|real.?time|dynamic|static)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text.lower())
            concepts.update(matches)

        return concepts

    def _calculate_semantic_relevance(self, memory: Dict[str, Any],
                                    query_keywords: List[str], query_concepts: set) -> float:
        """Calculate semantic relevance score for a memory"""
        content = memory['content'].lower()

        # Keyword matching score (0-1)
        keyword_matches = sum(1 for kw in query_keywords if kw.lower() in content)
        keyword_score = min(1.0, keyword_matches * 0.2)  # Cap at 1.0

        # Concept matching score (0-1)
        concept_matches = len(query_concepts.intersection(set(self._extract_concepts(content))))
        concept_score = min(1.0, concept_matches * 0.3)  # Cap at 1.0

        # Content type relevance
        type_multiplier = 1.0
        if memory['content_type'] in ['code', 'docs', 'project']:
            type_multiplier = 1.2

        # Quality boost
        quality_boost = memory.get('quality_score', 0.5) * 0.1

        # Calculate final score with weights
        final_score = (
            keyword_score * 0.4 +     # 40% keyword match
            concept_score * 0.4 +     # 40% concept match
            type_multiplier * 0.15 +   # 15% type relevance
            quality_boost            # 5% quality boost
        )

        return min(1.0, final_score)

    def _calculate_recency_score(self, memory: Dict[str, Any]) -> float:
        """Calculate recency score (0-1 scale, more recent = higher)"""
        memory_timestamp = memory['timestamp']
        now = datetime.now().timestamp()
        hours_old = (now - memory_timestamp) / 3600

        # Exponential decay: newer memories get higher scores
        if hours_old < 1:  # Less than 1 hour
            return 1.0
        elif hours_old < 24:  # Less than 1 day
            return 0.8
        elif hours_old < 168:  # Less than 1 week
            return 0.6
        elif hours_old < 720:  # Less than 1 month
            return 0.4
        else:
            return 0.2

    def _identify_match_type(self, memory: Dict[str, Any],
                           keywords: List[str], concepts: set) -> str:
        """Identify the type of semantic match"""
        content = memory['content'].lower()
        concept_matches = concepts.intersection(self._extract_concepts(content))

        if len(concept_matches) >= 2:
            return 'concept_match'
        elif any(kw.lower() in content for kw in keywords[:3]):  # Top keywords matched
            return 'keyword_match'
        elif memory['content_type'] == 'project':
            return 'contextual_match'
        else:
            return 'general_match'

    def _calculate_context_similarity(self, query: str, memory: Dict[str, Any]) -> float:
        """Calculate similarity between query and memory contexts"""
        query_concepts = self._extract_concepts(query)
        memory_concepts = self._extract_concepts(memory['content'])

        if not query_concepts or not memory_concepts:
            return 0.0

        intersection = len(query_concepts.intersection(memory_concepts))
        union = len(query_concepts.union(memory_concepts))

        return intersection / union if union > 0 else 0.0

    def _calculate_relationship_score(self, source: Dict[str, Any], target: Dict[str, Any]) -> float:
        """Calculate relationship strength between two memories"""
        # Content overlap
        content_sim = SequenceMatcher(None, source['content'], target['content']).ratio()

        # Concept overlap
        source_concepts = self._extract_concepts(source['content'])
        target_concepts = self._extract_concepts(target['content'])
        concept_overlap = len(source_concepts.intersection(target_concepts))
        concept_sim = concept_overlap / max(len(source_concepts), len(target_concepts), 1)

        # Temporal proximity
        time_diff = abs(source['timestamp'] - target['timestamp'])
        time_sim = math.exp(-time_diff / (24 * 3600))  # Decay over 24 hours

        # Combined score
        return (content_sim * 0.4 + concept_sim * 0.4 + time_sim * 0.2)

    def _identify_relationship_type(self, source: Dict[str, Any], target: Dict[str, Any]) -> str:
        """Identify the type of relationship between memories"""
        if target['content_type'] != source['content_type']:
            return 'complementary'

        if self._calculate_context_similarity(source['content'], target) > 0.8:
            return 'similar'

        if abs(source['timestamp'] - target['timestamp']) < 3600:  # Within 1 hour
            return 'temporal'

        return 'related'

    def _infer_conversation_intent(self, text: str) -> str:
        """Infer the intent of a conversation segment"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['how', 'what', 'why', 'when', 'where', 'explain']):
            return 'question'
        elif any(word in text_lower for word in ['help', 'assist', 'please', 'need']):
            return 'request_help'
        elif any(word in text_lower for word in ['fix', 'solve', 'resolve', 'debug']):
            return 'problem_solving'
        elif any(word in text_lower for word in ['create', 'build', 'implement', 'write']):
            return 'creation'
        else:
            return 'general'

    def _calculate_conversation_relevance(self, conversation: str,
                                       memory: Dict[str, Any], intent: str) -> float:
        """Calculate how relevant a memory is for the current conversation"""
        # Base semantic relevance
        base_score = self._calculate_semantic_relevance(
            memory,
            self._extract_semantic_keywords(conversation),
            self._extract_concepts(conversation)
        )

        # Intent matching boost
        intent_boost = 0.0
        memory_content = memory['content'].lower()

        if intent == 'question' and any(word in memory_content for word in ['explanation', 'guide', 'how', 'why']):
            intent_boost = 0.3
        elif intent == 'problem_solving' and any(word in memory_content for word in ['fix', 'solve', 'issue', 'error']):
            intent_boost = 0.3
        elif intent == 'creation' and memory['content_type'] == 'code':
            intent_boost = 0.2

        return min(1.0, base_score + intent_boost)

    def _suggest_memory_usage(self, memory: Dict[str, Any], intent: str) -> str:
        """Suggest how to use a memory in the conversation"""
        if intent == 'question' and memory['content_type'] == 'docs':
            return 'reference_documentation'

        if intent == 'problem_solving' and any(word in memory['content'].lower() for word in ['fix', 'solve', 'error']):
            return 'solution_example'

        if intent == 'creation' and memory['content_type'] == 'code':
            return 'implementation_pattern'

        return 'context_reference'

    def _analyze_temporal_patterns(self, contributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze temporal patterns in contributions"""
        if not contributions:
            return []

        # Group by day
        daily_counts = {}
        for contrib in contributions:
            day = datetime.fromtimestamp(contrib['timestamp']).strftime('%Y-%m-%d')
            daily_counts[day] = daily_counts.get(day, 0) + 1

        # Find peak days
        peak_days = sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)

        patterns = []

        if len(peak_days) >= 3:
            avg_daily = sum(daily_counts.values()) / len(daily_counts)
            peak_threshold = avg_daily * 1.5

            patterns.append({
                'type': 'productivity_peaks',
                'description': f'Most productive on {", ".join([day for day, count in peak_days[:3]])}',
                'peak_days': peak_days[:3],
                'threshold': peak_threshold
            })

        return patterns

    def _analyze_content_patterns(self, contributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze content patterns in contributions"""
        content_types = Counter(c['content_type'] for c in contributions)

        patterns = []
        total = len(contributions)

        for content_type, count in content_types.most_common(3):
            percentage = (count / total) * 100
            if percentage > 30:  # More than 30% of contributions
                patterns.append({
                    'type': 'content_specialization',
                    'content_type': content_type,
                    'percentage': percentage,
                    'count': count
                })

        return patterns

    def _analyze_collaboration_patterns(self, contributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze collaboration patterns"""
        # This would analyze temporal clustering of activities
        # indicating collaboration periods
        return []

    def _generate_behavior_insights(self, patterns: List[Dict[str, Any]], pattern_type: str) -> List[str]:
        """Generate human-readable insights from patterns"""
        insights = []

        for pattern in patterns:
            if pattern['type'] == 'productivity_peaks':
                insights.append(f"📈 You are most productive on {pattern['peak_days'][0][0]} with {pattern['peak_days'][0][1]} contributions")

            elif pattern['type'] == 'content_specialization':
                insights.append(f"🛠️ You focus {pattern['percentage']:.1f}% of your work on {pattern['content_type']} content")

        return insights

# Global instance
_context_engine = None

def get_context_intelligence_engine() -> ContextIntelligenceEngine:
    """Get singleton context intelligence engine instance"""
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextIntelligenceEngine()
    return _context_engine
