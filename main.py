#!/usr/bin/env python3
"""
Main entry point for InG AI Sales Department.
Launches all three agents and manages their lifecycle.
"""

import signal
import sys
import os
from pathlib import Path

# Auto-fix: If not running from venv, restart with venv Python
if sys.platform == "win32":
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
else:
    venv_python = Path(__file__).parent / "venv" / "bin" / "python"

# Check if we're running from venv by checking if psutil can be imported
# This is more reliable than checking sys.prefix
try:
    import psutil
    # If we got here, psutil is available - we're good to go
except ImportError:
    # psutil not available - try to restart with venv Python
    if venv_python.exists():
        import subprocess
        print("Auto-switching to venv Python...")
        sys.exit(subprocess.run([str(venv_python), __file__] + sys.argv[1:]).returncode)
    else:
        print(f"ERROR: venv Python not found at {venv_python}")
        print("Please ensure venv is set up correctly.")
        sys.exit(1)

# psutil is now imported (from the try block above)
from multiprocessing import Process, Queue, set_start_method
from pathlib import Path
from src.agents.sales_manager_agent import SalesManagerAgent

# Set start method to 'spawn' for Windows compatibility with multiprocessing.Queue
# This must be done before creating any processes
if sys.platform == "win32":
    try:
        set_start_method('spawn', force=True)
    except RuntimeError:
        # Already set, ignore
        pass
from src.agents.lead_finder_agent import LeadFinderAgent
from src.agents.outreach_agent import OutreachAgent
from src.communication.message_queue import MessageQueue
from src.communication.state_manager import StateManager
from src.integrations.llm_client import LLMClient
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

class AgentOrchestrator:
    """Manages all agents lifecycle"""
    
    def __init__(self, log_queue: Queue = None):
        self.config = load_config()
        # Create shared log queue for multiprocessing
        self.log_queue = log_queue or Queue(-1)
        self.logger = setup_logger("Orchestrator", log_queue=self.log_queue)
        self.agents = []
        self.processes = []
        
    def start_all_agents(self):
        """Start all three agents in separate processes"""
        # Start agents in separate processes
        # Agents are created inside each process to avoid scheduler serialization issues
        # Pass config as dict to avoid serialization issues
        import copy
        config_dict = copy.deepcopy(self.config)
        
        agent_configs = [
            ("SalesManager", SalesManagerAgent),
            ("LeadFinder", LeadFinderAgent),
            ("Outreach", OutreachAgent)
        ]
        
        for name, agent_class in agent_configs:
            process = Process(target=self._run_agent, args=(name, agent_class, config_dict, self.log_queue))
            process.start()
            self.processes.append(process)
            self.logger.info(f"Started {name} agent (PID: {process.pid})")
    
    @staticmethod
    def _run_agent(agent_name, agent_class, config_dict, log_queue):
        """Run agent in separate process - static method to avoid pickling issues"""
        # Setup logger for this process with shared queue
        logger = setup_logger(f"{agent_name}_Process", log_queue=log_queue)
        logger.info(f"Initializing process for agent: {agent_name}")
        
        try:
            # Initialize shared components inside the process
            logger.info(f"Initializing shared components for {agent_name}...")
            state_manager = StateManager(config_dict)
            message_queue = MessageQueue(config_dict)
            llm_client = LLMClient(config_dict)
            logger.info(f"Shared components initialized for {agent_name}")
            
            # Create agent inside the process
            logger.info(f"Creating agent instance: {agent_name}")
            agent = agent_class(
                agent_name=agent_name,
                config=config_dict,
                state_manager=state_manager,
                message_queue=message_queue,
                llm_client=llm_client
            )
            
            logger.info(f"Starting agent loop: {agent_name}")
            agent.start()
            agent.run()  # Blocking call - agent runs until stopped
        except Exception as e:
            import traceback
            error_msg = f"{agent_name} agent error: {e}\n{traceback.format_exc()}"
            # Use both logger and print to ensure output
            if 'logger' in locals():
                logger.error(error_msg)
            print(f"❌ FATAL ERROR in {agent_name}: {error_msg}")
            raise
    
    def stop_all_agents(self):
        """Gracefully stop all agents"""
        self.logger.info("Stopping all agents...")
        for agent in self.agents:
            try:
                agent.stop()
            except Exception as e:
                self.logger.error(f"Error stopping agent: {e}")
        
        # Wait for processes to finish
        for process in self.processes:
            process.join(timeout=10)
            if process.is_alive():
                process.terminate()
                self.logger.warning(f"Force terminated process {process.pid}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global orchestrator
    orchestrator.stop_all_agents()
    sys.exit(0)

def check_existing_process(lock_file_path="data/state/main.pid"):
    """Check if another instance is already running"""
    if os.path.exists(lock_file_path):
        try:
            with open(lock_file_path, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still alive
            if psutil.pid_exists(pid):
                try:
                    process = psutil.Process(pid)
                    cmdline = ' '.join(process.cmdline())
                    # Check if it's our process
                    if 'python' in process.name().lower() and ('main.py' in cmdline or 'InG_agents' in cmdline):
                        return True, pid  # Process is running
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # PID file exists but process is dead - remove stale lock
            print(f"🧹 Removing stale lock file (PID {pid} is not running)")
            os.remove(lock_file_path)
        except (ValueError, FileNotFoundError) as e:
            print(f"⚠️ Error reading lock file: {e}, removing it")
            try:
                os.remove(lock_file_path)
            except:
                pass
    
    return False, None

def create_lock_file(lock_file_path="data/state/main.pid"):
    """Create lock file with current PID"""
    Path(lock_file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file_path, 'w') as f:
        f.write(str(os.getpid()))

def remove_lock_file(lock_file_path="data/state/main.pid"):
    """Remove lock file"""
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)

if __name__ == "__main__":
    # Print startup message immediately
    print("Starting InG AI Sales Department Agents...", flush=True)
    print(f"Working directory: {os.getcwd()}", flush=True)
    
    lock_file = "data/state/main.pid"
    
    # Force cleanup of stale PID files
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                old_pid = f.read().strip()
            pid_int = int(old_pid)
            
            # Check if process exists
            if psutil.pid_exists(pid_int):
                try:
                    process = psutil.Process(pid_int)
                    cmdline = ' '.join(process.cmdline())
                    # Check if it's actually our process
                    if 'main.py' not in cmdline and 'InG_agents' not in cmdline:
                        # PID exists but it's not our process - remove stale lock
                        print(f"🧹 Removing stale PID file (PID {old_pid} is not our process)", flush=True)
                        os.remove(lock_file)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process doesn't exist or is zombie - remove stale lock
                    print(f"🧹 Removing stale PID file (PID {old_pid} not accessible)", flush=True)
                    os.remove(lock_file)
            else:
                # Process doesn't exist - remove stale lock
                print(f"🧹 Removing stale PID file (PID {old_pid} not running)", flush=True)
                os.remove(lock_file)
        except (ValueError, FileNotFoundError):
            # Invalid PID file - remove it
            print(f"🧹 Removing invalid PID file", flush=True)
            try:
                os.remove(lock_file)
            except:
                pass
    
    # Check if another instance is running
    is_running, existing_pid = check_existing_process(lock_file)
    if is_running:
        print(f"Another instance is already running (PID: {existing_pid}). Exiting.", flush=True)
        sys.exit(0)
    
    # Create lock file
    create_lock_file(lock_file)
    print(f"Lock file created: {lock_file} (PID: {os.getpid()})", flush=True)
    
    try:
        print("Loading configuration...")
        orchestrator = AgentOrchestrator()
        print("Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        import traceback
        traceback.print_exc()
        remove_lock_file(lock_file)
        sys.exit(1)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    
    try:
        print("Starting all agents...")
        orchestrator.start_all_agents()
        print("All agents started successfully")
        print("Agents are now running. Check data/logs/agents.log for details.")
        
        # Keep main process alive
        while True:
            # Check if all processes are alive
            for process in orchestrator.processes:
                if not process.is_alive():
                    orchestrator.logger.error(f"Agent process died: {process.pid}")
                    # Optionally restart or exit
                    orchestrator.stop_all_agents()
                    remove_lock_file(lock_file)
                    sys.exit(1)
            
            import time
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        orchestrator.stop_all_agents()
        remove_lock_file(lock_file)
    except Exception as e:
        orchestrator.logger.error(f"Fatal error: {e}")
        orchestrator.stop_all_agents()
        remove_lock_file(lock_file)
        sys.exit(1)
    finally:
        remove_lock_file(lock_file)

