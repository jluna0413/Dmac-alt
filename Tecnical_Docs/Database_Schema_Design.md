# Database Schema Design for Autonomous Coding Ecosystem
**TASK-002: Database Schema & Migrations Implementation**

## 📋 Executive Summary

This document defines the comprehensive database schema for the Autonomous Coding Ecosystem. The schema supports multi-agent orchestration, persistent task management, knowledge base operations, and enterprise-grade scalability required for Mobile-Agent-V3 integration.

**Current Status:** ✅ READY FOR IMPLEMENTATION
**Importance:** 🔴 CRITICAL - Foundation for all agent state management
**Estimated Effort:** 3-4 days

---

## 🏗️ Architecture Overview

### **Core Entities**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     PROJECT     │    │      PLAN       │    │      TASK       │
│                 │    │                 │    │                 │
│ - id            │    │ - id            │    │ - id            │
│ - name          │    │ - project_id    │    │ - plan_id       │
│ - description   │◄───┤ - title         │◄───┤ - title         │
│ - created_at    │    │ - description   │    │ - description   │
│ - updated_at    │    │ - status        │    │ - priority      │
│ - metadata      │    │ - created_by    │    │ - assignee      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     AGENT       │    │  KNOWLEDGE_BASE │
                    │                 │    │                 │
                    │ - id            │    │ - id            │
                    │ - name          │    │ - type          │
                    │ - type          │    │ - content       │
                    │ - capabilities  │    │ - tags          │
                    │ - status        │    │ - created_by    │
                    └─────────────────┘    └─────────────────┘
```

---

## 📊 Detailed Schema Definitions

### **1. Projects Table**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT projects_status_check
        CHECK (status IN ('active', 'completed', 'archived'))
);

-- Indexes for performance
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_created_at ON projects(created_at);
```

### **2. Plans Table**
```sql
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'medium',
    created_by UUID NOT NULL,
    assigned_to UUID,
    estimated_hours DECIMAL(6,2),
    actual_hours DECIMAL(6,2),

    -- Mobile-Agent-V3 specific fields
    mobile_sync_enabled BOOLEAN DEFAULT false,
    agent_count INTEGER DEFAULT 1,
    scaling_strategy VARCHAR(50) DEFAULT 'fixed',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deadline TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT plans_status_check
        CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT plans_priority_check
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT plans_project_fk
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- Mobile-Agent-V3 specific constraints
    CONSTRAINT plans_agent_count_check CHECK (agent_count > 0),
    CONSTRAINT plans_scaling_strategy_check
        CHECK (scaling_strategy IN ('fixed', 'adaptive', 'elastic'))
);
```

### **3. Tasks Table**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',

    -- Assignment and execution
    assigned_agent_id UUID,
    assigned_agent_type VARCHAR(100),
    execution_context JSONB DEFAULT '{}',

    -- Progress tracking
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    estimated_hours DECIMAL(6,2),
    actual_hours DECIMAL(6,2),

    -- Mobile-Agent-V3 specific fields
    mobile_task_id VARCHAR(255),
    device_fingerprint VARCHAR(255),
    sync_status VARCHAR(50) DEFAULT 'local',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Dependencies and sequencing
    depends_on UUID[],
    prerequisite_tasks UUID[],

    -- Audit and versioning
    created_by UUID NOT NULL,
    version INTEGER DEFAULT 1,
    tags TEXT[],

    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT tasks_status_check
        CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled')),
    CONSTRAINT tasks_priority_check
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT tasks_progress_check
        CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT tasks_plan_fk
        FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE,

    -- Mobile-Agent-V3 constraints
    CONSTRAINT tasks_sync_status_check
        CHECK (sync_status IN ('local', 'syncing', 'synced', 'conflict'))
);
```

### **4. Agents Table**
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL, -- 'codegen', 'testing', 'documentation', 'archon'
    status VARCHAR(50) DEFAULT 'offline',

    -- Capabilities and configuration
    capabilities JSONB DEFAULT '[]', -- Array of capability strings
    configuration JSONB DEFAULT '{}', -- Agent-specific config

    -- Mobile-Agent-V3 specific fields
    mobile_capable BOOLEAN DEFAULT false,
    device_affinity VARCHAR(255), -- Preferred device type
    location_enabled BOOLEAN DEFAULT false,
    battery_aware BOOLEAN DEFAULT false,

    -- Performance and metrics
    success_rate DECIMAL(5,4) DEFAULT 0.0,
    average_response_time DECIMAL(8,3), -- milliseconds
    total_tasks_completed INTEGER DEFAULT 0,

    -- Operational fields
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    current_task_id UUID,
    ip_address INET,
    host_name VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deactivated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT agents_status_check
        CHECK (status IN ('offline', 'online', 'busy', 'maintenance')),
    CONSTRAINT agents_type_check
        CHECK (type IN ('codegen', 'testing', 'documentation', 'archon', 'mobile_controller')),

    -- Performance constraints
    CONSTRAINT agents_success_rate_check
        CHECK (success_rate >= 0.0 AND success_rate <= 1.0)
);
```

### **5. Knowledge Base Table**
```sql
CREATE TABLE knowledge_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL, -- 'code_snippet', 'adr', 'documentation', 'pattern'

    -- Content
    title VARCHAR(255) NOT NULL,
    content TEXT,
    summary TEXT,

    -- Metadata
    tags TEXT[],
    categories TEXT[],
    source VARCHAR(100) DEFAULT 'agent',

    -- Provenance
    created_by UUID NOT NULL,
    created_agent_id UUID,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00

    -- Versioning
    version INTEGER DEFAULT 1,
    previous_version_id UUID,

    -- Access control
    visibility VARCHAR(20) DEFAULT 'public', -- 'public', 'private', 'team'
    access_list UUID[], -- Array of user/agent IDs with access

    -- Mobile sync
    mobile_synced BOOLEAN DEFAULT false,
    device_fingerprint VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT knowledge_type_check
        CHECK (type IN ('code_snippet', 'adr', 'documentation', 'pattern', 'task_template')),
    CONSTRAINT knowledge_visibility_check
        CHECK (visibility IN ('public', 'private', 'team')),
    CONSTRAINT knowledge_confidence_check
        CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);
```

### **6. Sessions & Context Tables**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    status VARCHAR(30) DEFAULT 'active',
    context_snapshot JSONB DEFAULT '{}',
    mobile_session_id VARCHAR(255),
    device_info JSONB DEFAULT '{}',

    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,

    duration INTERVAL,
    task_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),

    metadata JSONB DEFAULT '{}',

    CONSTRAINT sessions_status_check
        CHECK (status IN ('active', 'paused', 'completed', 'failed'))
);

CREATE TABLE context_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    vector_data REAL[], -- Array of vector components
    context_type VARCHAR(50), -- 'semantic', 'collaborative', 'task'
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT context_vectors_session_fk
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

---

## 🔗 Relationships & Indexes

### **Core Relationships**
```sql
-- Hierarchical structure
projects (1) → (N) plans
plans (1) → (N) tasks

-- Assignment relationships
agents (1) → (N) tasks (assigned_agent_id)
agents (1) → (N) tasks (created_by)

-- Context relationships
sessions (1) → (N) context_vectors
tasks (1) → (N) knowledge_entries
```

### **Performance Indexes**
```sql
-- Projects
CREATE INDEX idx_projects_status_created ON projects(status, created_at);
CREATE INDEX idx_projects_metadata_gin ON projects USING gin(metadata);

-- Plans
CREATE INDEX idx_plans_project_status ON plans(project_id, status);
CREATE INDEX idx_plans_deadline ON plans(deadline) WHERE deadline IS NOT NULL;
CREATE INDEX idx_plans_mobile_sync ON plans(mobile_sync_enabled) WHERE mobile_sync_enabled = true;

-- Tasks
CREATE INDEX idx_tasks_plan_status ON tasks(plan_id, status);
CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX idx_tasks_mobile_sync ON tasks(sync_status) WHERE sync_status != 'local';
CREATE INDEX idx_tasks_depends_on_gin ON tasks USING gin(depends_on);

-- Agents
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type_capabilities ON agents(type, capabilities);
CREATE INDEX idx_agents_mobile_capable ON agents(mobile_capable) WHERE mobile_capable = true;

-- Knowledge
CREATE INDEX idx_knowledge_type ON knowledge_entries(type);
CREATE INDEX idx_knowledge_tags_gin ON knowledge_entries USING gin(tags);
CREATE INDEX idx_knowledge_mobile_sync ON knowledge_entries(mobile_synced) WHERE mobile_synced = true;

-- Sessions
CREATE INDEX idx_sessions_agent_active ON sessions(agent_id, status) WHERE status = 'active';
CREATE INDEX idx_sessions_mobile ON sessions(mobile_session_id) WHERE mobile_session_id IS NOT NULL;
```

---

## 🔄 Migration Strategy

### **Migration Files Structure**
```
database/
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_mobile_agent_support.sql
│   ├── 003_performance_indexes.sql
│   ├── 004_context_vector_tables.sql
│   └── 005_enterprise_features.sql
├── schemas/
│   ├── projects.sql
│   ├── plans.sql
│   ├── tasks.sql
│   ├── agents.sql
│   └── knowledge.sql
├── scripts/
│   ├── init_db.sh
│   ├── migrate_db.sh
│   └── backup_db.sh
└── README.md
```

---

## 🚀 Implementation Status

### **Phase 1: Core Schema (Day 1-2)**
- [ ] ✅ Initial PostgreSQL connection setup
- [ ] 🔄 Projects, Plans, Tasks tables
- [ ] ⏳ Agents table implementation
- [ ] ⏳ Knowledge base tables

### **Phase 2: Mobile-Agent-V3 Support (Day 3)**
- [ ] ⏳ Mobile-specific fields and constraints
- [ ] ⏳ Context vector table implementation
- [ ] ⏳ Session management tables

### **Phase 3: Performance & Migration (Day 4)**
- [ ] ⏳ Performance indexes implementation
- [ ] ⏳ Migration system testing
- [ ] ⏳ Seed data and initial records

---

## 📈 Business Impact

**Database Schema Implementation Benefits:**
- ✅ **Multi-Agent State Persistence**: Essential for unlimited agent orchestration
- ✅ **Task Management Foundation**: Core business logic storage
- ✅ **Knowledge Base Scalability**: Unlimited documentation and code storage
- ✅ **Mobile Synchronization**: Real-time mobile/desktop data syncing
- ✅ **Enterprise Performance**: Indexes optimized for high-throughput operations

---

## 🎯 Next Steps

**Immediate Actions:**
1. **PostgreSQL Setup** - Environment configuration
2. **Schema Creation** - Core tables implementation
3. **Migration System** - Automated schema management
4. **Testing Framework** - Database integration tests

**Mobile-Agent-V3 Dependency:**
This database foundation is **absolutely critical** for Mobile-Agent-V3's multi-agent orchestration, persistent state management, and cross-device synchronization capabilities.

---

**Status**: 🔄 READY FOR DATABASE IMPLEMENTATION
**Timeline**: 3-4 days for complete TASK-002 delivery
**Impact**: 🔴 CRITICAL foundation for Mobile-Agent-V3 and all enterprise features
