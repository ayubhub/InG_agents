#!/usr/bin/env python3
"""
Pre-flight check for InG AI Sales Department application.
Verifies all requirements before starting the application.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def check_file_exists(filepath: str, description: str) -> tuple[bool, str]:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        return True, f"✅ {description}: {filepath}"
    else:
        return False, f"❌ {description} missing: {filepath}"

def check_env_var(var_name: str, required: bool = True) -> tuple[bool, str]:
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if "KEY" in var_name or "PASSWORD" in var_name or "SECRET" in var_name:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            return True, f"✅ {var_name}: {masked} (length: {len(value)})"
        else:
            return True, f"✅ {var_name}: {value[:50]}"
    else:
        if required:
            return False, f"❌ {var_name}: NOT SET (required)"
        else:
            return True, f"⚠️  {var_name}: NOT SET (optional)"

def check_python_package(package_name: str, import_name: str = None) -> tuple[bool, str]:
    """Check if Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, f"✅ {package_name}: installed"
    except ImportError:
        return False, f"❌ {package_name}: NOT INSTALLED"

def check_directory(dirpath: str, create_if_missing: bool = False) -> tuple[bool, str]:
    """Check if directory exists."""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        return True, f"✅ Directory exists: {dirpath}"
    elif create_if_missing:
        path.mkdir(parents=True, exist_ok=True)
        return True, f"✅ Directory created: {dirpath}"
    else:
        return False, f"❌ Directory missing: {dirpath}"

def main():
    """Run pre-flight checks."""
    print("=" * 70)
    print("InG AI Sales Department - Pre-Flight Check")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    issues = []
    warnings = []
    
    # 1. Check configuration files
    print("1. Configuration Files:")
    print("-" * 70)
    
    config_checks = [
        ("config/agents.yaml", "Main configuration file"),
        (".env", "Environment variables file"),
    ]
    
    for filepath, desc in config_checks:
        exists, msg = check_file_exists(filepath, desc)
        print(f"  {msg}")
        if not exists:
            all_checks_passed = False
            issues.append(msg)
    
    # Check optional config files
    optional_configs = [
        ("config/google-credentials.json", "Google Sheets credentials (if using Google Sheets)"),
    ]
    
    for filepath, desc in optional_configs:
        exists, msg = check_file_exists(filepath, desc)
        if not exists:
            print(f"  ⚠️  {desc}: {filepath} (optional)")
            warnings.append(f"Optional file missing: {filepath}")
    
    print()
    
    # 2. Load environment variables
    print("2. Environment Variables:")
    print("-" * 70)
    
    # Try to load .env file
    env_loaded = False
    try:
        from dotenv import load_dotenv
        load_dotenv()
        env_loaded = True
        print("  ✅ .env file loaded via python-dotenv")
    except ImportError:
        # If dotenv not available, parse .env file manually
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            os.environ[key] = value
                env_loaded = True
                print("  ✅ .env file loaded (manual parsing)")
            except Exception as e:
                print(f"  ⚠️  Error parsing .env file: {e}")
                warnings.append(f"Error parsing .env: {e}")
        else:
            print("  ⚠️  .env file not found")
    except Exception as e:
        print(f"  ⚠️  Error loading .env: {e}")
        warnings.append(f"Error loading .env: {e}")
    
    # Required environment variables
    required_env_vars = [
        "GEMINI_API_KEY",
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        "GOOGLE_SHEETS_CREDENTIALS_PATH",
    ]
    
    for var in required_env_vars:
        ok, msg = check_env_var(var, required=True)
        print(f"  {msg}")
        if not ok:
            all_checks_passed = False
            issues.append(msg)
    
    # Optional but recommended environment variables
    optional_env_vars = [
        ("UNIPILE_DSN", False),
        ("UNIPILE_API_KEY", False),
        ("UNIPILE_ACCOUNT_ID", False),
        ("LOG_LEVEL", False),
    ]
    
    for var, required in optional_env_vars:
        ok, msg = check_env_var(var, required=required)
        print(f"  {msg}")
        if not ok and required:
            all_checks_passed = False
            issues.append(msg)
    
    print()
    
    # 3. Check Python packages
    print("3. Python Dependencies:")
    print("-" * 70)
    
    required_packages = [
        ("psutil", "psutil"),
        ("google.generativeai", "google-generativeai"),
        ("gspread", "gspread"),
        ("yaml", "PyYAML"),
        ("dotenv", "python-dotenv"),
        ("colorlog", "colorlog"),
        ("requests", "requests"),
    ]
    
    for import_name, package_name in required_packages:
        ok, msg = check_python_package(package_name, import_name)
        print(f"  {msg}")
        if not ok:
            all_checks_passed = False
            issues.append(msg)
    
    print()
    
    # 4. Check directory structure
    print("4. Directory Structure:")
    print("-" * 70)
    
    required_dirs = [
        ("data", True),
        ("data/logs", True),
        ("data/state", True),
        ("data/cache", True),
        ("src", False),
        ("config", False),
    ]
    
    for dirpath, create in required_dirs:
        ok, msg = check_directory(dirpath, create_if_missing=create)
        print(f"  {msg}")
        if not ok and not create:
            all_checks_passed = False
            issues.append(msg)
    
    print()
    
    # 5. Test configuration loading
    print("5. Configuration Loading:")
    print("-" * 70)
    
    try:
        from src.utils.config_loader import load_config
        config = load_config()
        print("  ✅ Configuration loaded successfully")
        print(f"  ✅ Found {len(config.get('agents', {}))} agent configurations")
    except FileNotFoundError as e:
        print(f"  ❌ Configuration file not found: {e}")
        all_checks_passed = False
        issues.append(f"Config file missing: {e}")
    except Exception as e:
        print(f"  ❌ Error loading configuration: {e}")
        all_checks_passed = False
        issues.append(f"Config loading error: {e}")
    
    print()
    
    # 6. Test API keys (quick check)
    print("6. API Key Validation:")
    print("-" * 70)
    
    # Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            # Try to list models (lightweight check)
            try:
                models = list(genai.list_models())
                print("  ✅ GEMINI_API_KEY: Valid (can connect to API)")
            except Exception as e:
                error_msg = str(e).lower()
                if "invalid" in error_msg or "api_key" in error_msg:
                    print(f"  ❌ GEMINI_API_KEY: Invalid key")
                    all_checks_passed = False
                    issues.append("GEMINI_API_KEY is invalid")
                else:
                    print(f"  ⚠️  GEMINI_API_KEY: Connection issue (may be network/quota): {str(e)[:50]}")
                    warnings.append(f"Gemini API connection issue: {str(e)[:50]}")
        except ImportError:
            print("  ⚠️  Cannot test GEMINI_API_KEY: google-generativeai not installed")
        except Exception as e:
            print(f"  ⚠️  Error testing GEMINI_API_KEY: {str(e)[:50]}")
            warnings.append(f"Gemini API test error: {str(e)[:50]}")
    else:
        print("  ❌ GEMINI_API_KEY: Not set")
        all_checks_passed = False
    
    # Check Google Sheets credentials
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    if creds_path:
        creds_file = Path(creds_path)
        if creds_file.exists():
            print(f"  ✅ Google Sheets credentials file exists: {creds_path}")
        else:
            print(f"  ⚠️  Google Sheets credentials file not found: {creds_path}")
            warnings.append(f"Google Sheets credentials missing: {creds_path}")
    else:
        print("  ⚠️  GOOGLE_SHEETS_CREDENTIALS_PATH not set")
        warnings.append("GOOGLE_SHEETS_CREDENTIALS_PATH not set")
    
    print()
    
    # 7. Check for running instances
    print("7. Process Check:")
    print("-" * 70)
    
    pid_file = Path("data/state/main.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = f.read().strip()
            print(f"  ⚠️  PID file exists: data/state/main.pid (PID: {old_pid})")
            print(f"  💡 If application is not running, this is a stale lock file")
            warnings.append(f"PID file exists: {old_pid}")
        except Exception:
            print(f"  ⚠️  PID file exists but cannot be read")
            warnings.append("PID file exists but unreadable")
    else:
        print("  ✅ No existing PID file (application not running)")
    
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if all_checks_passed and not warnings:
        print("✅ All checks passed! Application is ready to run.")
        print()
        print("To start the application:")
        print("  python run_main.py")
        return 0
    elif all_checks_passed:
        print("✅ All critical checks passed, but there are warnings:")
        print()
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print()
        print("Application should work, but review warnings above.")
        print("To start the application:")
        print("  python run_main.py")
        return 0
    else:
        print("❌ Some critical checks failed:")
        print()
        for issue in issues:
            print(f"  ❌ {issue}")
        if warnings:
            print()
            print("Warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        print()
        print("Please fix the issues above before starting the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

