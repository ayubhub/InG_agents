#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Limits Monitor and Reset Tool
Показывает текущее состояние лимитов и позволяет их сбросить
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def load_state():
    """Загрузить состояние аккаунтов из файла."""
    state_file = project_root / "data" / "state" / "multi_account_state.json"
    
    if not state_file.exists():
        print(f"❌ Файл состояния не найден: {state_file}")
        return None
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки состояния: {e}")
        return None

def format_time_remaining(cooldown_until_str):
    """Форматировать оставшееся время до сброса."""
    if not cooldown_until_str:
        return "Нет"
    
    try:
        cooldown_until = datetime.fromisoformat(cooldown_until_str)
        now = datetime.now()
        
        if now >= cooldown_until:
            return "Истек"
        
        remaining = cooldown_until - now
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    except:
        return "Ошибка"

def format_last_used(last_used_str):
    """Форматировать время последнего использования."""
    if not last_used_str:
        return "Никогда"
    
    try:
        last_used = datetime.fromisoformat(last_used_str)
        now = datetime.now()
        diff = now - last_used
        
        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ч. назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} м. назад"
        else:
            return "Только что"
    except:
        return last_used_str

def show_status():
    """Показать текущий статус всех аккаунтов."""
    state = load_state()
    if not state:
        return
    
    account_stats = state.get("account_stats", {})
    current_index = state.get("current_account_index", 0)
    global_cooldown = state.get("global_cooldown_until")
    
    print("\n" + "="*80)
    print("📊 СТАТУС ЛИМИТОВ LINKEDIN")
    print("="*80)
    
    # Global cooldown
    if global_cooldown:
        remaining = format_time_remaining(global_cooldown)
        print(f"\n⚠️  ГЛОБАЛЬНЫЙ COOLDOWN: {remaining} до сброса")
        print("   (Все аккаунты временно недоступны)")
    else:
        print("\n✅ Глобальный cooldown: Нет")
    
    print(f"\n📌 Текущий активный аккаунт: Account_{current_index + 1}")
    print("\n" + "-"*80)
    
    # Load limits from environment or defaults
    daily_limit = int(os.getenv("LINKEDIN_DAILY_LIMIT", "50"))
    hourly_limit = int(os.getenv("LINKEDIN_HOURLY_LIMIT", "10"))
    
    for account_name in sorted(account_stats.keys()):
        stats = account_stats[account_name]
        
        # Check if counters need reset
        now = datetime.now()
        last_reset_date = stats.get("last_reset_date")
        last_reset_hour = stats.get("last_reset_hour")
        
        daily_sent = stats.get("daily_sent", 0)
        hourly_sent = stats.get("hourly_sent", 0)
        error_count = stats.get("error_count", 0)
        cooldown_until = stats.get("cooldown_until")
        last_used = stats.get("last_used")
        last_error = stats.get("last_error")
        
        # Calculate if daily reset needed
        needs_daily_reset = False
        if last_reset_date:
            try:
                reset_date = datetime.fromisoformat(last_reset_date).date() if isinstance(last_reset_date, str) else datetime.strptime(last_reset_date, "%Y-%m-%d").date()
                if reset_date != now.date():
                    needs_daily_reset = True
            except:
                pass
        
        # Status indicator
        is_current = account_name == f"Account_{current_index + 1}"
        status_icon = "👉" if is_current else "  "
        
        print(f"\n{status_icon} {account_name}")
        print(f"   {'─'*76}")
        
        # Daily limit
        daily_percent = (daily_sent / daily_limit * 100) if daily_limit > 0 else 0
        daily_bar = "█" * int(daily_percent / 5) + "░" * (20 - int(daily_percent / 5))
        daily_status = "✅" if daily_sent < daily_limit else "❌"
        if needs_daily_reset:
            daily_status = "🔄 (сброс сегодня)"
        
        print(f"   📅 Дневной лимит: {daily_status} {daily_sent}/{daily_limit} ({daily_percent:.1f}%)")
        print(f"      [{daily_bar}]")
        
        # Hourly limit
        hourly_percent = (hourly_sent / hourly_limit * 100) if hourly_limit > 0 else 0
        hourly_bar = "█" * int(hourly_percent / 5) + "░" * (20 - int(hourly_percent / 5))
        hourly_status = "✅" if hourly_sent < hourly_limit else "❌"
        
        print(f"   ⏰ Часовой лимит: {hourly_status} {hourly_sent}/{hourly_limit} ({hourly_percent:.1f}%)")
        print(f"      [{hourly_bar}]")
        
        # Cooldown
        cooldown_remaining = format_time_remaining(cooldown_until)
        if cooldown_until:
            print(f"   ⏳ Cooldown: {cooldown_remaining} до сброса")
        else:
            print(f"   ✅ Cooldown: Нет")
        
        # Error count
        error_icon = "⚠️" if error_count > 0 else "✅"
        print(f"   {error_icon} Ошибок: {error_count}")
        
        # Last used
        last_used_formatted = format_last_used(last_used)
        print(f"   🕐 Последнее использование: {last_used_formatted}")
        
        # Total sent
        total_sent = stats.get("total_sent", 0)
        print(f"   📊 Всего отправлено: {total_sent}")
        
        # Last error (if any)
        if last_error:
            error_preview = last_error[:100] + "..." if len(last_error) > 100 else last_error
            print(f"   ⚠️  Последняя ошибка: {error_preview}")
        
        # Availability
        available = daily_sent < daily_limit and hourly_sent < hourly_limit and not cooldown_until
        if global_cooldown:
            available = False
        
        status_text = "✅ Доступен" if available else "❌ Недоступен"
        print(f"   📍 Статус: {status_text}")
    
    print("\n" + "="*80)
    print(f"🕐 Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def reset_limits(account_name=None):
    """Сбросить лимиты для указанного аккаунта или всех аккаунтов."""
    state = load_state()
    if not state:
        return False
    
    account_stats = state.get("account_stats", {})
    now = datetime.now()
    
    if account_name:
        # Reset specific account
        if account_name in account_stats:
            stats = account_stats[account_name]
            stats["daily_sent"] = 0
            stats["hourly_sent"] = 0
            stats["last_reset_date"] = now.date().isoformat()
            stats["last_reset_hour"] = now.hour
            stats["error_count"] = 0
            stats["cooldown_until"] = None
            stats["last_error"] = None
            print(f"✅ Сброшены лимиты для {account_name}")
        else:
            print(f"❌ Аккаунт {account_name} не найден")
            return False
    else:
        # Reset all accounts
        for acc_name in account_stats:
            stats = account_stats[acc_name]
            stats["daily_sent"] = 0
            stats["hourly_sent"] = 0
            stats["last_reset_date"] = now.date().isoformat()
            stats["last_reset_hour"] = now.hour
            stats["error_count"] = 0
            stats["cooldown_until"] = None
            stats["last_error"] = None
        print("✅ Сброшены лимиты для всех аккаунтов")
    
    # Clear global cooldown
    state["global_cooldown_until"] = None
    state["last_updated"] = now.isoformat()
    
    # Save state
    state_file = project_root / "data" / "state" / "multi_account_state.json"
    try:
        os.makedirs(state_file.parent, exist_ok=True)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print("✅ Состояние сохранено")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "reset":
            account_name = sys.argv[2] if len(sys.argv) > 2 else None
            reset_limits(account_name)
        elif command == "status" or command == "show":
            show_status()
        elif command == "help" or command == "--help" or command == "-h":
            print("""
Использование: python tools/monitor_linkedin_limits.py [команда] [опции]

Команды:
  status, show    - Показать текущий статус лимитов (по умолчанию)
  reset [account] - Сбросить лимиты для указанного аккаунта или всех
  help            - Показать эту справку

Примеры:
  python tools/monitor_linkedin_limits.py              # Показать статус
  python tools/monitor_linkedin_limits.py status       # Показать статус
  python tools/monitor_linkedin_limits.py reset        # Сбросить все аккаунты
  python tools/monitor_linkedin_limits.py reset Account_1  # Сбросить Account_1
            """)
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Используйте 'help' для справки")
    else:
        # Default: show status
        show_status()

if __name__ == "__main__":
    main()


