# Deployment and Running Guide

## Document Information
- **Document Type**: Deployment and Operations Guide
- **Target Audience**: DevOps, Developers, System Administrators
- **Version**: 1.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

**Один главный скрипт** (`main.py`) запускает все три агента параллельно. Агенты работают как фоновые процессы/потоки, общаются через файловую очередь и работают 24/7 до остановки.

---

## Architecture Overview

### Запуск: Один скрипт, три агента

```
python main.py
    │
    ├── Sales Manager Agent (thread/process)
    │   └── Работает по расписанию (9:00 AM координация, 9:15 AM отчет)
    │
    ├── Lead Finder Agent (thread/process)
    │   └── Работает по расписанию (10:00 AM) или по запросу
    │
    └── Outreach Agent (thread/process)
        └── Работает постоянно, проверяет очередь и отправляет сообщения
```

**Принцип**: Один процесс Python, три параллельных агента внутри.

---

## Main Entry Point: main.py

### Структура main.py

```python
#!/usr/bin/env python3
"""
Main entry point for InG AI Sales Department.
Launches all three agents and manages their lifecycle.
"""

import signal
import sys
from multiprocessing import Process
from src.agents.sales_manager_agent import SalesManagerAgent
from src.agents.lead_finder_agent import LeadFinderAgent
from src.agents.outreach_agent import OutreachAgent
from src.communication.message_queue import MessageQueue
from src.communication.state_manager import StateManager
from src.integrations.llm_client import LLMClient
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

class AgentOrchestrator:
    """Manages all agents lifecycle"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logger()
        self.agents = []
        self.processes = []
        
    def start_all_agents(self):
        """Start all three agents in separate processes"""
        # Initialize shared components
        state_manager = StateManager(self.config)
        message_queue = MessageQueue(self.config)
        llm_client = LLMClient(self.config)
        
        # Create agents
        sales_manager = SalesManagerAgent(
            config=self.config,
            state_manager=state_manager,
            message_queue=message_queue,
            llm_client=llm_client
        )
        
        lead_finder = LeadFinderAgent(
            config=self.config,
            state_manager=state_manager,
            message_queue=message_queue,
            llm_client=llm_client
        )
        
        outreach = OutreachAgent(
            config=self.config,
            state_manager=state_manager,
            message_queue=message_queue,
            llm_client=llm_client
        )
        
        # Start agents in separate processes
        agents = [
            (sales_manager, "SalesManager"),
            (lead_finder, "LeadFinder"),
            (outreach, "Outreach")
        ]
        
        for agent, name in agents:
            process = Process(target=self._run_agent, args=(agent, name))
            process.start()
            self.processes.append(process)
            self.logger.info(f"Started {name} agent (PID: {process.pid})")
        
        self.agents = [sales_manager, lead_finder, outreach]
    
    def _run_agent(self, agent, name):
        """Run agent in separate process"""
        try:
            agent.start()
            agent.run()  # Blocking call - agent runs until stopped
        except Exception as e:
            self.logger.error(f"{name} agent error: {e}")
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

if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    
    try:
        orchestrator.start_all_agents()
        
        # Keep main process alive
        while True:
            # Check if all processes are alive
            for process in orchestrator.processes:
                if not process.is_alive():
                    orchestrator.logger.error(f"Agent process died: {process.pid}")
                    # Optionally restart or exit
                    orchestrator.stop_all_agents()
                    sys.exit(1)
            
            import time
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        orchestrator.stop_all_agents()
    except Exception as e:
        orchestrator.logger.error(f"Fatal error: {e}")
        orchestrator.stop_all_agents()
        sys.exit(1)
```

---

## Agent Lifecycle

### Как работает каждый агент

#### Sales Manager Agent
- **Запуск**: Автоматически при старте `main.py`
- **Расписание**: 
  - 9:00 AM - координация операций
  - 9:15 AM - генерация ежедневного отчета
- **Работа**: Использует APScheduler для планирования задач
- **Состояние**: Работает постоянно, выполняет задачи по расписанию

#### Lead Finder Agent
- **Запуск**: Автоматически при старте `main.py`
- **Расписание**: 10:00 AM - обработка новых лидов
- **Работа**: Читает лиды из Google Sheets, классифицирует, обновляет
- **Состояние**: Работает постоянно, обрабатывает лиды по расписанию

#### Outreach Agent
- **Запуск**: Автоматически при старте `main.py`
- **Работа**: 
  - Постоянно проверяет очередь выделенных лидов
  - Отправляет сообщения с учетом rate limiting
  - Каждые 2 часа проверяет ответы
- **Состояние**: Работает постоянно, обрабатывает очередь

---

## Запуск и Остановка

### Запуск системы

```bash
# 1. Активировать виртуальное окружение (если используется)
source venv/bin/activate

# 2. Запустить все агенты одной командой
python main.py
```

**Что происходит**:
1. Загружается конфигурация
2. Инициализируются общие компоненты (StateManager, MessageQueue, LLMClient)
3. Запускаются три агента в отдельных процессах
4. Главный процесс остается живым и мониторит агентов

### Остановка системы

**Вариант 1**: Graceful shutdown (рекомендуется)
```bash
# Нажать Ctrl+C в терминале где запущен main.py
# Или отправить SIGTERM сигнал
kill <PID>
```

**Вариант 2**: Принудительная остановка
```bash
kill -9 <PID>
```

### Проверка статуса

```bash
# Проверить что процессы запущены
ps aux | grep python | grep main.py

# Проверить логи
tail -f data/logs/agents.log

# Проверить статус агентов (если реализован health check endpoint)
# или через SQLite
sqlite3 data/state/agents.db "SELECT * FROM agent_state;"
```

---

## Альтернативные варианты запуска

### Вариант 1: Отдельные скрипты (не рекомендуется)

Можно запустить каждый агент отдельно:
```bash
python -m src.agents.sales_manager_agent
python -m src.agents.lead_finder_agent
python -m src.agents.outreach_agent
```

**Минусы**:
- Нужно запускать три команды
- Сложнее управлять
- Нет централизованного мониторинга

### Вариант 2: Systemd service (для production)

Создать systemd service для автоматического запуска:

```ini
# /etc/systemd/system/ing-agents.service
[Unit]
Description=InG AI Sales Department Agents
After=network.target

[Service]
Type=simple
User=ing-user
WorkingDirectory=/path/to/InG_agents
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl start ing-agents
sudo systemctl enable ing-agents  # Автозапуск при загрузке
```

### Вариант 3: Docker (опционально, для будущего)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## Мониторинг и Логирование

### Логи

Все агенты пишут логи в:
- `data/logs/agents.log` - общий лог
- `data/logs/{agent_name}.log` - лог конкретного агента

### Health Checks

Каждый агент периодически обновляет свой статус в SQLite:
```sql
SELECT agent_name, state_data, last_updated 
FROM agent_state;
```

### Мониторинг очереди

Проверить количество событий в очереди:
```bash
# Подсчитать pending события
ls -1 data/queue/pending/*.json | wc -l

# Посмотреть последние события
ls -t data/queue/pending/*.json | head -5
```

---

## Troubleshooting

### Агент не запускается

1. Проверить логи: `tail -f data/logs/agents.log`
2. Проверить конфигурацию: `config/agents.yaml`
3. Проверить переменные окружения: `.env`
4. Проверить права доступа к `data/` директории

### Агент упал (crashed)

1. Проверить логи на ошибки
2. Проверить доступность внешних сервисов (Google Sheets, Gemini API)
3. Перезапустить: `python main.py`

### Сообщения не отправляются

1. Проверить rate limiter в SQLite: `SELECT * FROM rate_limiter;`
2. Проверить очередь: `ls data/queue/pending/`
3. Проверить логи Outreach агента

---

## Best Practices

1. **Всегда используйте один main.py** - проще управлять и мониторить
2. **Используйте graceful shutdown** - агенты корректно сохранят состояние
3. **Мониторьте логи** - регулярно проверяйте `data/logs/`
4. **Делайте бэкапы** - периодически копируйте `data/state/agents.db`
5. **Используйте systemd для production** - автоматический перезапуск при сбоях

---

## Summary

**Ответ на вопрос**: Запускается **один скрипт** (`python main.py`), который сам запускает все три агента параллельно. Агенты работают постоянно до остановки скрипта.

**Преимущества**:
- ✅ Простота: одна команда для запуска
- ✅ Управление: централизованный контроль
- ✅ Мониторинг: единая точка наблюдения
- ✅ Надежность: главный процесс следит за агентами

---

## Document Approval

- **DevOps Lead**: _________________ Date: _______
- **Technical Lead**: _________________ Date: _______

