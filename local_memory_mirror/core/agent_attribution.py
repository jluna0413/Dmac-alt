"""
Agent attribution system for Local Byterover Memory Mirror
Tracks and analyzes agent contributions, performance, and collaboration patterns
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from .database import get_database_manager

logger = logging.getLogger(__name__)

class AgentAttributionEngine:
    """Tracks and analyzes agent contributions and performance"""

    def __init__(self):
        self.db = get_database_manager()

    def track_contribution(self, agent_context: str, action_data: Dict[str, Any]) -> bool:
        """Track agent contribution with intelligent analysis"""

        # Extract agent information from context
        agent_info = self._identify_agent(agent_context)

        if not agent_info:
            logger.warning(f"Could not identify agent from context: {agent_context}")
            return False

        # Prepare attribution record
        attribution_record = {
            'agent_id': agent_info['agent_id'],
            'action_type': self._classify_action(action_data),
            'target_type': self._identify_target_type(action_data),
            'target_id': self._extract_target_id(action_data),
            'context': self._extract_context_data(action_data),
            'quality_score': self._assess_contribution_quality(action_data),
            'metadata': self._extract_metadata(action_data)
        }

        # Log the attribution
        success = self.db.log_attribution(attribution_record)

        if success:
            # Update agent profile statistics
            self._update_agent_statistics(agent_info['agent_id'], attribution_record)

        return success

    def get_agent_contributions(self, agent_id: str,
                              time_range: Optional[str] = None,
                              action_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get comprehensive contribution history for an agent"""

        base_query = "SELECT * FROM attribution_logs WHERE agent_id = ?"
        params = [agent_id]

        # Add time range filter
        if time_range:
            timestamp_filter = self._get_timestamp_filter(time_range)
            if timestamp_filter:
                base_query += " AND timestamp >= ?"
                params.append(str(timestamp_filter))  # Convert to string for list

        # Add action type filter
        if action_types:
            placeholders = ', '.join('?' * len(action_types))
            base_query += f" AND action_type IN ({placeholders})"
            params.extend(action_types)

        base_query += " ORDER BY timestamp DESC LIMIT 100"

        results = self.db.execute_query(base_query, tuple(params))
        return results

    def get_agent_performance_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for an agent"""

        contributions = self.get_agent_contributions(agent_id)

        if not contributions:
            return self._get_empty_metrics()

        # Analyze contribution patterns
        action_counts = Counter(c['action_type'] for c in contributions)
        quality_scores = [c['quality_score'] for c in contributions if c['quality_score']]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).timestamp()
        recent_count = sum(1 for c in contributions if c['timestamp'] > week_ago)

        # Target type distribution
        target_distribution = Counter(c['target_type'] for c in contributions)

        return {
            'total_contributions': len(contributions),
            'action_distribution': dict(action_counts),
            'average_quality_score': round(avg_quality, 2),
            'recent_activity_count': recent_count,
            'target_type_distribution': dict(target_distribution),
            'contribution_velocity': self._calculate_velocity(contributions),
            'specialization_score': self._calculate_specialization_score(target_distribution),
            'consistency_score': self._calculate_consistency_score(quality_scores)
        }

    def get_collaboration_patterns(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze collaboration patterns between agents"""

        # Get attribution data for all agents
        collaboration_data = {}
        for agent_id in agent_ids:
            contributions = self.get_agent_contributions(agent_id, time_range='7days')
            collaboration_data[agent_id] = contributions

        # Find overlapping activities and shared targets
        overlaps = self._analyze_overlaps(collaboration_data)
        shared_targets = self._find_shared_targets(collaboration_data)

        return {
            'agent_pairs': overlaps,
            'shared_targets': shared_targets,
            'collaboration_efficiency': self._calculate_collaboration_efficiency(overlaps),
            'complementary_specializations': self._identify_complementarities(collaboration_data)
        }

    def generate_attribution_report(self,
                                  report_type: str = 'comprehensive',
                                  time_range: str = '30days') -> Dict[str, Any]:
        """Generate comprehensive attribution reports"""

        timestamp_filter = self._get_timestamp_filter(time_range)

        if report_type == 'agent_performance':
            return self._generate_performance_report(timestamp_filter)
        elif report_type == 'collaboration':
            return self._generate_collaboration_report(timestamp_filter)
        elif report_type == 'content_quality':
            return self._generate_quality_report(timestamp_filter)
        else:  # comprehensive
            return self._generate_comprehensive_report(timestamp_filter)

    def _identify_agent(self, agent_context: str) -> Optional[Dict[str, Any]]:
        """Identify agent from context string or metadata"""

        # Try to identify from context strings like "cline: added function"
        agent_keywords = {
            'cline': {'agent_id': 'cline', 'type': 'coding_assistant', 'confidence': 0.9},
            'documentation': {'agent_id': 'docs_agent', 'type': 'documentation', 'confidence': 0.8},
            'testing': {'agent_id': 'test_agent', 'type': 'quality_assurance', 'confidence': 0.8},
            'codegen': {'agent_id': 'codegen_agent', 'type': 'code_generation', 'confidence': 0.8}
        }

        for keyword, agent_info in agent_keywords.items():
            if keyword.lower() in agent_context.lower():
                return agent_info

        # Check agent profiles in database
        agent_profiles = self.db.execute_query("SELECT * FROM agent_profiles")
        for profile in agent_profiles:
            if profile['name'].lower() in agent_context.lower():
                return {
                    'agent_id': profile['agent_id'],
                    'type': profile['agent_type'],
                    'confidence': 0.7
                }

        return None

    def _classify_action(self, action_data: Dict[str, Any]) -> str:
        """Classify the type of action performed"""

        action_indicators = {
            'create': ['add', 'create', 'new', 'generate', 'build'],
            'modify': ['update', 'edit', 'change', 'alter', 'fix'],
            'delete': ['remove', 'delete', 'clear'],
            'query': ['search', 'find', 'get', 'retrieve', 'lookup'],
            'review': ['review', 'analyze', 'examine', 'check']
        }

        for action_type, indicators in action_indicators.items():
            for indicator in indicators:
                if indicator in str(action_data).lower():
                    return action_type

        return 'unknown'

    def _identify_target_type(self, action_data: Dict[str, Any]) -> str:
        """Identify the type of target affected"""

        # This could be enhanced with ML pattern recognition
        data_str = str(action_data).lower()

        if 'memory' in data_str:
            return 'memory'
        elif 'task' in data_str:
            return 'task'
        elif 'agent' in data_str:
            return 'agent'
        elif any(word in data_str for word in ['file', 'code', 'function']):
            return 'code'
        elif any(word in data_str for word in ['doc', 'document', 'readme']):
            return 'documentation'
        else:
            return 'general'

    def _extract_target_id(self, action_data: Dict[str, Any]) -> Optional[str]:
        """Extract target identifier from action data"""
        # Look for IDs, hashes, or names in the action data
        if 'target_id' in action_data:
            return str(action_data['target_id'])
        return None

    def _extract_context_data(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context information"""
        context = {}
        if 'file' in action_data:
            context['affected_file'] = action_data['file']
        if 'project' in action_data:
            context['project'] = action_data['project']
        if 'component' in action_data:
            context['component'] = action_data['component']
        return context

    def _assess_contribution_quality(self, action_data: Dict[str, Any]) -> float:
        """Assess the quality of a contribution"""
        # Basic quality assessment - can be enhanced with ML
        quality_score = 0.5  # Default

        # Increase for certain positive indicators
        positive_indicators = ['test', 'review', 'document', 'validate']
        for indicator in positive_indicators:
            if indicator in str(action_data).lower():
                quality_score += 0.2

        # Decrease for potential issues
        negative_indicators = ['error', 'fail', 'bug', 'fix']
        for indicator in negative_indicators:
            if indicator in str(action_data).lower():
                quality_score -= 0.1

        return max(0.0, min(1.0, quality_score))  # Clamp between 0-1

    def _extract_metadata(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional metadata for analysis"""
        return {
            'timestamp': datetime.now().timestamp(),
            'data_size': len(str(action_data)),
            'action_complexity': self._assess_complexity(action_data)
        }

    def _update_agent_statistics(self, agent_id: str, attribution_record: Dict[str, Any]):
        """Update agent profile statistics based on new attribution"""
        # This would update performance metrics in the agent profile
        # For now, we just update the last activity timestamp
        self.db.execute_update(
            "UPDATE agent_profiles SET last_active = ? WHERE agent_id = ?",
            (datetime.now().timestamp(), agent_id)
        )

    def _assess_complexity(self, action_data: Dict[str, Any]) -> int:
        """Assess action complexity (simple heuristic)"""
        complexity = 1
        data_str = str(action_data)

        if len(data_str) > 1000:
            complexity += 1
        if 'file' in action_data:
            complexity += 1
        if 'complex' in data_str.lower() or 'advanced' in data_str.lower():
            complexity += 1

        return complexity

    def _get_timestamp_filter(self, time_range: str) -> Optional[float]:
        """Convert time range string to timestamp"""
        now = datetime.now().timestamp()

        if time_range == '24hours':
            return now - (24 * 3600)
        elif time_range == '7days':
            return now - (7 * 24 * 3600)
        elif time_range == '30days':
            return now - (30 * 24 * 3600)
        else:
            return None

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'total_contributions': 0,
            'action_distribution': {},
            'average_quality_score': 0.0,
            'recent_activity_count': 0,
            'target_type_distribution': {},
            'contribution_velocity': 0,
            'specialization_score': 0,
            'consistency_score': 0
        }

    def _calculate_velocity(self, contributions: List[Dict[str, Any]]) -> float:
        """Calculate contribution velocity (contributions per day)"""
        if not contributions:
            return 0.0

        # Get time span
        timestamps = [c['timestamp'] for c in contributions]
        time_span_days = (max(timestamps) - min(timestamps)) / (24 * 3600)

        if time_span_days < 1:
            return len(contributions)  # Contributions per day minimum

        return len(contributions) / max(time_span_days, 1)

    def _calculate_specialization_score(self, target_distribution: Counter) -> float:
        """Calculate how specialized an agent is (0-1 scale)"""
        if not target_distribution:
            return 0.0

        total = sum(target_distribution.values())
        max_category = target_distribution.most_common(1)[0][1]

        # Score based on how concentrated contributions are
        concentration_ratio = max_category / total
        return min(1.0, concentration_ratio * 2)  # Scale to make it more sensitive

    def _calculate_consistency_score(self, quality_scores: List[float]) -> float:
        """Calculate quality consistency (0-1 scale)"""
        if not quality_scores:
            return 0.0

        # Use coefficient of variation (lower = more consistent)
        mean = sum(quality_scores) / len(quality_scores)
        if mean == 0:
            return 0.0

        variance = sum((score - mean) ** 2 for score in quality_scores) / len(quality_scores)
        std_dev = variance ** 0.5
        cv = std_dev / mean

        # Lower coefficient of variation = higher consistency
        return max(0.0, 1.0 - cv)

    # Additional helper methods for collaboration analysis would go here
    def _analyze_overlaps(self, collaboration_data: Dict[str, List]) -> Dict[str, Any]:
        """Analyze temporal overlaps in agent activities"""
        return {}  # Placeholder

    def _find_shared_targets(self, collaboration_data: Dict[str, List]) -> Dict[str, Any]:
        """Find targets worked on by multiple agents"""
        return {}  # Placeholder

    def _calculate_collaboration_efficiency(self, overlaps: Dict) -> float:
        """Calculate efficiency of agent collaborations"""
        return 0.5  # Placeholder

    def _identify_complementarities(self, collaboration_data: Dict[str, List]) -> Dict[str, Any]:
        """Identify complementary agent specializations"""
        return {}  # Placeholder

    def _generate_performance_report(self, timestamp_filter: Optional[float]) -> Dict[str, Any]:
        """Generate agent performance report"""
        return {}  # Placeholder

    def _generate_collaboration_report(self, timestamp_filter: Optional[float]) -> Dict[str, Any]:
        """Generate collaboration analysis report"""
        return {}  # Placeholder

    def _generate_quality_report(self, timestamp_filter: Optional[float]) -> Dict[str, Any]:
        """Generate content quality report"""
        return {}  # Placeholder

    def _generate_comprehensive_report(self, timestamp_filter: Optional[float]) -> Dict[str, Any]:
        """Generate comprehensive attribution report"""
        return {}  # Placeholder

# Global attribution engine instance
_attribution_instance = None

def get_attribution_engine() -> AgentAttributionEngine:
    """Get singleton attribution engine instance"""
    global _attribution_instance
    if _attribution_instance is None:
        _attribution_instance = AgentAttributionEngine()
    return _attribution_instance
