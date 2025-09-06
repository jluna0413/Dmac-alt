@echo off
REM =======================================================================
REM AUTONOMOUS CODING ECOSYSTEM ORCHESTRATOR
REM TASK-002 Implementation - Phase 1: Core Orchestrator
REM =======================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM Configuration
set "PROJECT_ROOT=%~dp0.."
set "DB_PATH=%PROJECT_ROOT%\autonomous_ecosystem.db"
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "PORT_MCP=8051"
set "PORT_MCP_CONTROL=8052"
set "PORT_N8N=5678"
set "PORT_SUPABASE=54321"

REM Create logs directory
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Colors for output
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

:header
echo ===================================================================
echo   🔧 AUTONOMOUS CODING ECOSYSTEM ORCHESTRATOR v1.0
echo ===================================================================
echo.
echo 🎯 Starting Autonomous Coding Ecosystem...
echo 📋 Current time: %time%
echo 🗂️  Project root: %PROJECT_ROOT%
echo 📊 Database: %DB_PATH%
echo.
goto :main

:main
echo 🚀 PHASE 1: INFRASTRUCTURE VALIDATION
echo ────────────────────────────────────────────────────────

REM Check prerequisites
echo ✅ Checking prerequisites...
call :check_node || goto :error
call :check_python || goto :error
call :check_docker || goto :error
echo.

REM Initialize database
echo 🗄️ PHASE 2: DATABASE INITIALIZATION
echo ────────────────────────────────────────────────────────
call :init_database || goto :error
echo.

REM Start core services
echo 🌐 PHASE 3: CORE SERVICES STARTUP
echo ────────────────────────────────────────────────────────
call :start_mcp_server || goto :error
call :start_mcp_control || goto :error
call :start_archon_services || goto :error
call :start_agent_services || goto :error
echo.

REM Start user interfaces
echo 🖥️ PHASE 4: USER INTERFACE STARTUP
echo ────────────────────────────────────────────────────────
call :start_dashboards || goto :error
echo.

REM Health checks
echo ❤️  PHASE 5: HEALTH VERIFICATION
echo ────────────────────────────────────────────────────────
call :verify_services || goto :error
echo.

REM Display status
echo 🎉 PHASE 6: SYSTEM READY
echo ────────────────────────────────────────────────────────
call :display_system_status
echo.

REM Keep running
echo 🔥 Ecosystem running! Services are active.
echo 📊 Monitoring logs at: %LOGS_DIR%
echo 🚪 Press Ctrl+C to stop all services
echo.
echo 🌐 Access Points:
echo    • MCP Server: http://localhost:%PORT_MCP%
echo    • MCP Control: http://localhost:%PORT_MCP_CONTROL%
echo    • Deep-Wiki: Will be available in dashboard
echo    • Archon UI: http://localhost:3000
echo.

REM Monitor services
call :monitor_services

goto :infinity

REM =======================================================================
REM FUNCTIONS
REM =======================================================================

:check_node
echo Checking Node.js...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Node.js not found! Please install Node.js first.%RESET%
    goto :error
)
echo ✅ Node.js found
goto :eof

:check_python
echo Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Python not found! Please install Python 3.8+ first.%RESET%
    goto :error
)
echo ✅ Python found
goto :eof

:check_docker
echo Checking Docker (optional)...
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW%⚠️  Docker not found - some services may not work%RESET%
) else (
    echo ✅ Docker found
)
goto :eof

:init_database
echo Initializing database...
cd /d "%PROJECT_ROOT%"

REM Create database if it doesn't exist
python -c "from database.models.base import init_db; init_db(); print('✅ Database initialized successfully!')" 2>>"%LOGS_DIR%\db_init.log"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Database initialization failed!%RESET%
    goto :error
)

echo ✅ Database ready at: %DB_PATH%
goto :eof

:start_mcp_server
echo Starting MCP Server...
cd /d "%PROJECT_ROOT%\Archon\python"

REM Check if MCP server directory exists
if not exist "src\mcp_server" (
    echo %YELLOW%⚠️  MCP server directory not found - skipping%RESET%
    goto :eof
)

REM Start MCP server in background
start /B python src\mcp_server\mcp_server.py --port %PORT_MCP% >>"%LOGS_DIR%\mcp_server.log" 2>&1
timeout /t 3 /nobreak >nul

REM Verify MCP server started
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%PORT_MCP%/health' -TimeoutSec 5; Write-Host '✅ MCP Server online' } catch { Write-Host '%YELLOW%⚠️  MCP Server may still be starting...%RESET%' }"
goto :eof

:start_mcp_control
echo Starting MCP-Control Server...
cd /d "%PROJECT_ROOT%\MCPControl"

REM Check if MCP-Control exists
if not exist "package.json" (
    echo %YELLOW%⚠️  MCP-Control not found - skipping%RESET%
    goto :eof
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing MCP-Control dependencies...
    npm install >>"%LOGS_DIR%\mcp_control_deps.log" 2>&1
)

REM Start MCP-Control server
start /B npm run dev -- --port %PORT_MCP_CONTROL% >>"%LOGS_DIR%\mcp_control.log" 2>&1
timeout /t 3 /nobreak >nul

echo ✅ MCP-Control starting...
goto :eof

:start_archon_services
echo Starting Archon Core Services...

REM Start Archon API
cd /d "%PROJECT_ROOT%\Archon\python"
if exist "src\archon\main.py" (
    start /B python -m src.archon.main >>"%LOGS_DIR%\archon.log" 2>&1
    echo ✅ Archon API starting...
)

REM Start Archon UI if available
cd /d "%PROJECT_ROOT%\Archon\archon-ui-main"
if exist "src\main.tsx" (
    if not exist "node_modules" (
        echo Installing Archon UI dependencies...
        npm install >>"%LOGS_DIR%\archon_ui_deps.log" 2>&1
    )
    start /B npm run dev >>"%LOGS_DIR%\archon_ui.log" 2>&1
    echo ✅ Archon UI starting...
)
goto :eof

:start_agent_services
echo Starting Agent Services...

REM Start Documentation Agent
cd /d "%PROJECT_ROOT%\src\agents"
if exist "documentation_agent.py" (
    start /B python documentation_agent.py >>"%LOGS_DIR%\doc_agent.log" 2>&1
    echo ✅ Documentation Agent starting...
)

REM Start Testing Agent
if exist "testing_agent.py" (
    start /B python testing_agent.py >>"%LOGS_DIR%\test_agent.log" 2>&1
    echo ✅ Testing Agent starting...
)

REM Start CodeGen Agent
if exist "codegen_agent.py" (
    start /B python codegen_agent.py >>"%LOGS_DIR%\codegen_agent.log" 2>&1
    echo ✅ CodeGen Agent starting...
)
goto :eof

:start_dashboards
echo Starting Dashboard Services...

REM Start Deep-Wiki Dashboard
cd /d "%PROJECT_ROOT%\dashboard"
if exist "serve.py" (
    start /B python serve.py >>"%LOGS_DIR%\dashboard.log" 2>&1
    echo ✅ Deep-Wiki Dashboard starting...
)
goto :eof

:verify_services
echo Verifying service health...

REM Check MCP Server
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%PORT_MCP%/health' -TimeoutSec 10; Write-Host '✅ MCP Server: HEALTHY' } catch { Write-Host '%RED%❌ MCP Server: UNHEALTHY%RESET%' }"

REM Check MCP Control
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%PORT_MCP_CONTROL%/health' -TimeoutSec 5; Write-Host '✅ MCP Control: HEALTHY' } catch { Write-Host '%YELLOW%⚠️  MCP Control: STARTING...%RESET%' }"

echo Health verification complete
goto :eof

:display_system_status
echo.
echo 🔧 ECOSYSTEM STATUS
echo ──────────────────
echo 🌐 Services Running:
echo    • MCP Server (Intelligence Hub)
echo    • MCP-Control (Orchestration)
echo    • Archon API (Agent Management)
echo    • Documentation Agent
echo    • Testing Agent
echo    • CodeGen Agent
echo    • Deep-Wiki Dashboard
echo.
echo 📁 Logs: %LOGS_DIR%
echo 🗃️  Database: %DB_PATH%
goto :eof

:monitor_services
echo.
echo 📊 MONITORING MODE
echo ──────────────────
echo Press any key to check service status...

:infinity
timeout /t 30 >nul
call :verify_services
echo.
echo ────────────────────────────────────────────────────────
goto :infinity

:error
echo.
echo %RED%❌ ERROR: Ecosystem startup failed!%RESET%
echo Please check the logs in %LOGS_DIR% for details.
echo.
echo 🔧 TROUBLESHOOTING:
echo • Ensure all prerequisites are installed (Node.js, Python, Docker)
echo • Check if ports %PORT_MCP%, %PORT_MCP_CONTROL% are available
echo • Review service logs for specific error messages
echo.
pause
goto :cleanup

:cleanup
echo Cleaning up...
taskkill /FI "WINDOWTITLE eq Autonomous Ecosystem*" /T /F >nul 2>&1
echo ✅ Cleanup complete
goto :eof

REM =======================================================================
REM QUICK START REFERENCE
REM =======================================================================
:help
echo Usage: %0 [command]
echo.
echo Commands:
echo   /?        Show this help
echo.
echo This script starts the complete Autonomous Coding Ecosystem including:
echo • MCP Server (AI Intelligence Hub)
echo • MCP-Control (Service Orchestration)
echo • Archon (Agent Management)
echo • Multiple AI Agents (Docs, Testing, CodeGen)
echo • Deep-Wiki Dashboard (Knowledge Base)
echo • Database and monitoring services
echo.
exit /b 0
