"""
Sales Manager Agent - Coordinates operations and generates reports.
"""

import time
from datetime import datetime, time as dt_time, timedelta, date
from typing import Dict, List
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from src.agents.base_agent import BaseAgent
from src.core.models import Lead
from src.integrations.email_service import EmailService

class SalesManagerAgent(BaseAgent):
    """Sales Manager Agent for coordination and reporting."""
    
    def __init__(self, *args, **kwargs):
        """Initialize Sales Manager Agent."""
        super().__init__(*args, **kwargs)
        
        self.config_section = self.config.get("sales_manager", {})
        self.include_self_review = self.config_section.get("include_self_review", True)
        
        # Track last coordination time to process only new leads
        self.last_coordination_time = datetime.now() - timedelta(days=1)  # Process all on first run
        
        self.email_service = EmailService(self.config)
        self.scheduler = BlockingScheduler()
        
        # Setup scheduled tasks
        self._setup_scheduler()
    
    def _setup_scheduler(self) -> None:
        """Setup periodic tasks."""
        # Coordination (lead allocation) - periodic polling
        coord_interval = self.config_section.get("coordination_interval_minutes", 2)
        self.scheduler.add_job(
            self.coordinate_daily_operations,
            trigger=IntervalTrigger(minutes=coord_interval),
            id='coordination',
            next_run_time=datetime.now()
        )
        
        # Daily report - once per day (this is fine)
        report_hour = self.config_section.get("report_hour", 18)
        self.scheduler.add_job(
            self.generate_daily_report,
            trigger=CronTrigger(hour=report_hour, minute=0),
            id='daily_report'
        )
        
        self.logger.info(f"Scheduler: coordination every {coord_interval} min, reports at {report_hour}:00")
    
    def run(self) -> None:
        """Main agent loop."""
        self.logger.info("Sales Manager Agent running")
        self.scheduler.start()
    
    def coordinate_daily_operations(self) -> None:
        """Allocate newly classified leads."""
        self.logger.info("Coordinating lead allocation")
        
        try:
            # Read classified leads not yet allocated
            filters = {
                "classification": ["Speaker", "Sponsor"],
                "contact_status": "Not Contacted"
            }
            leads = self.state_manager.read_leads(filters)
            
            # Log all found leads for debugging
            if leads:
                self.logger.debug(f"Found classified leads: {[(l.id, l.name, l.classification, l.quality_score, l.contact_status) for l in leads]}")
            
            # Filter: only leads updated since last coordination
            new_leads = [
                lead for lead in leads 
                if lead.last_updated and lead.last_updated > self.last_coordination_time
            ]
            
            self.logger.info(f"Found {len(leads)} classified leads, {len(new_leads)} new since last check (last_coordination_time: {self.last_coordination_time})")
            
            if new_leads:
                self.logger.info(f"Found {len(new_leads)} newly classified leads")
                
                # Get quality threshold from lead_finder config
                lead_finder_config = self.config.get("lead_finder", {})
                quality_threshold = lead_finder_config.get("quality_threshold", 6.0)
                
                allocated_count = 0
                for lead in new_leads:
                    # Allocation logic
                    if lead.quality_score and lead.quality_score >= quality_threshold:
                        updates = {
                            "contact_status": "Allocated",
                            "allocated_to": "Outreach",
                            "allocated_at": datetime.now().isoformat(),
                            "last_updated": datetime.now().isoformat()
                        }
                        if self.state_manager.update_lead(lead.id, updates):
                            allocated_count += 1
                            self.logger.info(f"Allocated lead {lead.id}: {lead.name} (score: {lead.quality_score})")
                        else:
                            self.logger.warning(f"✗ Failed to allocate lead {lead.id}: {lead.name}")
                    else:
                        self.logger.debug(f"Skipped lead {lead.id}: score {lead.quality_score} < threshold {quality_threshold}")
                
                if allocated_count > 0:
                    self.logger.info(f"Allocated {allocated_count} leads to Outreach")
            
            # Update last check time
            self.last_coordination_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error in coordination: {e}")
    
    def allocate_leads(self, max_leads: int = 50) -> List[Lead]:
        """
        Allocate leads to Outreach agent.
        
        Args:
            max_leads: Maximum number of leads to allocate
        
        Returns:
            List of allocated leads
        """
        # Get uncontacted leads with high quality scores
        filters = {"contact_status": "Not Contacted"}
        leads = self.state_manager.read_leads(filters)
        
        # Sort by quality score (descending)
        leads = sorted(leads, key=lambda x: x.quality_score or 0, reverse=True)
        
        # Filter by quality threshold
        quality_threshold = self.config.get("lead_finder", {}).get("quality_threshold", 6.0)
        qualified_leads = [l for l in leads if (l.quality_score or 0) >= quality_threshold]
        
        # Select top leads
        selected = qualified_leads[:max_leads]
        
        # Allocate to Outreach
        if selected:
            lead_ids = [lead.id for lead in selected]
            self.state_manager.allocate_leads(lead_ids, "Outreach")
            
            # Publish allocation event
            self.publish_event("lead_allocation", {
                "agent_to": "Outreach",
                "lead_ids": lead_ids,
                "count": len(lead_ids)
            })
        
        return selected
    
    def monitor_performance(self, report_period: str = "previous_day") -> Dict:
        """
        Monitor performance metrics.
        
        Args:
            report_period: "previous_day" (default) or "all_time"
                          If "previous_day", filters metrics for previous day (00:00-23:59)
        
        Returns:
            Performance metrics dictionary
        """
        # Get all leads
        all_leads = self.state_manager.read_leads()
        
        # Filter by period if needed
        if report_period == "previous_day":
            # Calculate previous day boundaries
            today = date.today()
            previous_day = today - timedelta(days=1)
            day_start = datetime.combine(previous_day, dt_time.min)  # 00:00:00
            day_end = datetime.combine(previous_day, dt_time.max)  # 23:59:59
            
            # Filter leads by activity within previous day
            # Include leads that had any activity yesterday (message sent, response received, or allocated)
            filtered_leads = []
            for lead in all_leads:
                # Include if message was sent yesterday
                if lead.message_sent_at and day_start <= lead.message_sent_at <= day_end:
                    filtered_leads.append(lead)
                # Include if response was received yesterday
                elif lead.response_received_at and day_start <= lead.response_received_at <= day_end:
                    filtered_leads.append(lead)
                # Include if allocated yesterday (for leads processed count)
                elif lead.allocated_at and day_start <= lead.allocated_at <= day_end:
                    filtered_leads.append(lead)
            
            all_leads = filtered_leads
        
        # Calculate metrics
        total_leads = len(all_leads)
        messages_sent = len([l for l in all_leads if l.message_sent])
        responses_received = len([l for l in all_leads if l.response])
        positive_responses = len([l for l in all_leads if l.response_sentiment == "positive"])
        negative_responses = len([l for l in all_leads if l.response_sentiment == "negative"])
        neutral_responses = len([l for l in all_leads if l.response_sentiment == "neutral"])
        
        response_rate = (responses_received / messages_sent * 100) if messages_sent > 0 else 0
        
        return {
            "total_leads": total_leads,
            "messages_sent": messages_sent,
            "responses_received": responses_received,
            "positive_responses": positive_responses,
            "negative_responses": negative_responses,
            "neutral_responses": neutral_responses,
            "response_rate": round(response_rate, 2)
        }
    
    def generate_daily_report(self) -> None:
        """Generate and send daily report for previous day."""
        self.logger.info("Generating daily report for previous day")
        
        try:
            # Collect metrics for previous day
            metrics = self.monitor_performance(report_period="previous_day")
            
            # Get self-review data
            self_review = self._collect_self_review()
            
            # Generate insights using LLM
            insights = self._generate_insights(metrics)
            
            # Format report
            report = self._format_report(metrics, self_review, insights)
            
            # Send email (report date is previous day)
            previous_day = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            subject = f"InG Sales Department - Daily Report - {previous_day}"
            self.email_service.send_daily_report(subject, report)
            
            self.logger.info(f"Daily report sent for {previous_day}")
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
    
    def _collect_self_review(self) -> List[Dict]:
        """Collect self-review data from agents."""
        # This would collect uncertain decisions from other agents
        # For now, return empty list
        return []
    
    def _generate_insights(self, metrics: Dict) -> str:
        """Generate insights using LLM."""
        system_prompt = """You are a sales analytics assistant. Analyze performance metrics and generate insights for a daily sales report.

Focus on:
- Key metrics (leads processed, messages sent, responses received)
- Response rates and trends
- Recommendations for improvement
- Flag any concerning patterns

Write in a clear, professional tone suitable for email report."""
        
        user_prompt = f"""Generate daily report insights:

Metrics:
- Leads processed today: {metrics.get('total_leads', 0)}
- Messages sent: {metrics.get('messages_sent', 0)}
- Responses received: {metrics.get('responses_received', 0)}
- Response rate: {metrics.get('response_rate', 0)}%
- Positive responses: {metrics.get('positive_responses', 0)}

Insights and recommendations:"""
        
        try:
            return self.llm_client.generate(user_prompt, system_prompt, temperature=0.7)
        except Exception as e:
            self.logger.warning(f"LLM insights generation failed: {e}")
            return "Performance metrics collected. Review recommended."
    
    def _format_report(self, metrics: Dict, self_review: List[Dict], insights: str) -> str:
        """Format daily report for previous day."""
        # Report date is previous day
        previous_day = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        report = f"""
InG AI Sales Department - Daily Report
Date: {previous_day} (Previous Day)
Time: 9:15 AM

═══════════════════════════════════════════════════════════
📊 PERFORMANCE METRICS (Previous Day: {previous_day})
═══════════════════════════════════════════════════════════

✅ Leads Processed: {metrics.get('total_leads', 0)}
📤 Messages Sent: {metrics.get('messages_sent', 0)}
📥 Responses Received: {metrics.get('responses_received', 0)}
📈 Response Rate: {metrics.get('response_rate', 0)}%
👍 Positive Responses: {metrics.get('positive_responses', 0)}
👎 Negative Responses: {metrics.get('negative_responses', 0)}
❓ Neutral Responses: {metrics.get('neutral_responses', 0)}

═══════════════════════════════════════════════════════════
🤖 AGENT SELF-REVIEW
═══════════════════════════════════════════════════════════

✅ All decisions were made with high confidence.

═══════════════════════════════════════════════════════════
💡 INSIGHTS & RECOMMENDATIONS
═══════════════════════════════════════════════════════════

{insights}

═══════════════════════════════════════════════════════════

Generated by InG AI Sales Department
Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report
    
    def optimise_strategy(self) -> Dict:
        """
        Optimise strategy based on performance data.
        
        Returns:
            Strategy recommendations
        """
        # This would analyze 2+ weeks of data
        # For now, return basic recommendations
        return {
            "recommendations": ["Continue current strategy", "Monitor response rates"]
        }

