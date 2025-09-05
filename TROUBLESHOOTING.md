# Archon MCP Integration - Troubleshooting Guide

## Common Issues and Solutions

### 1. Database Connection Errors

**Problem**: `relation "public.archon_settings" does not exist`
**Solution**: 
```sql
-- Execute complete_setup.sql in Supabase SQL Editor
-- File: A:\Projects\Archon\migration\complete_setup.sql
```

**Problem**: `connection timeout` to Supabase
**Solution**: 
- Verify SUPABASE_URL in .env file
- Check SUPABASE_SERVICE_KEY is the legacy (longer) key
- Ensure Supabase project is not paused

### 2. MCP Server Issues

**Problem**: `404 Not Found` for MCP endpoints
**Solution**: 
- Use correct MCP endpoint: `http://localhost:8051/mcp` (note `/mcp` path)
- Ensure AI client uses SSE transport, not stdio
- Check `Accept: text/event-stream` header

**Problem**: `Not Acceptable: Client must accept text/event-stream`
**Solution**: 
```bash
# Correct curl command:
curl -H "Accept: text/event-stream" http://localhost:8051/mcp
```

### 3. Container Health Issues

**Problem**: Services showing `unhealthy` status
**Solution**: 
```powershell
# Check logs for specific errors
docker compose logs archon-server --tail=20
docker compose logs archon-mcp --tail=20

# Restart unhealthy services
docker compose restart
```

**Problem**: Port conflicts (8051, 8181, 3737 in use)
**Solution**: 
- Check what's using ports: `netstat -ano | findstr :8051`
- Update .env file with different ports if needed
- Restart containers after port changes

### 4. AI Client Integration

**Problem**: AI client can't connect to MCP server
**Solution**: 
```json
// Correct Cursor configuration:
{
  "mcpServers": {
    "archon": {
      "uri": "http://localhost:8051/mcp"
    }
  }
}
```

**Problem**: MCP tools not appearing in AI client
**Solution**: 
- Verify AI client supports SSE transport
- Check MCP server logs for connection attempts
- Ensure no firewall blocking port 8051

### 5. Performance Issues

**Problem**: Slow response times
**Solution**: 
- Check Docker resource allocation (CPU/Memory)
- Monitor container stats: `docker stats`
- Optimize batch sizes in archon_settings table

**Problem**: High memory usage
**Solution**: 
- Adjust `MEMORY_THRESHOLD_PERCENT` setting
- Reduce `CRAWL_MAX_CONCURRENT` workers
- Monitor with: `docker compose top`

### 6. Development Workflow

**Problem**: Need to reset entire setup
**Solution**: 
```powershell
# Complete reset
docker compose down -v
docker compose up --build -d

# Re-execute database schema if needed
# Run complete_setup.sql in Supabase SQL Editor
```

**Problem**: Testing integration changes
**Solution**: 
```powershell
# Quick restart without rebuilding
docker compose restart archon-mcp

# Check specific service logs
docker compose logs archon-mcp --follow
```

## Diagnostic Commands

### Check System Status
```powershell
# All services status
docker compose ps

# Resource usage
docker stats --no-stream

# Network connectivity
curl -I http://localhost:8051/mcp
curl -I http://localhost:8181/health
curl -I http://localhost:3737
```

### Verify Database
```sql
-- Check tables exist in Supabase SQL Editor
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'archon_%';

-- Check settings loaded
SELECT key, category, description FROM archon_settings LIMIT 10;
```

### Test MCP Tools
```bash
# List available tools (requires proper MCP client)
# This would be done through AI client connection
# Expected: 14 tools (7 RAG + 7 Project management)
```

## Configuration Files

### Critical Environment Variables (.env)
```env
SUPABASE_URL=https://nbuakvajqjxaotmnnjyr.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### Port Mappings
- **8051**: MCP Server (SSE endpoint)
- **8181**: Main Archon API
- **3737**: Web UI
- **5432**: Supabase PostgreSQL (hosted)

## Getting Help

1. **Check service logs**: Always start with `docker compose logs <service>`
2. **Verify configuration**: Ensure .env file has correct credentials
3. **Test connectivity**: Use curl commands to verify endpoints
4. **Database validation**: Check Supabase dashboard for table creation
5. **AI client setup**: Verify MCP configuration matches transport type

---

**For additional support**: Check Archon GitHub issues or discussions
