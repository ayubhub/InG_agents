"""
Lead Finder Agent - Classifies and scores leads from Google Sheets.
"""

import time
from datetime import datetime
from typing import List
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from src.agents.base_agent import BaseAgent
from src.core.models import Lead
from src.core.lead_classifier import LeadClassifier
from src.core.quality_scorer import QualityScorer

class LeadFinderAgent(BaseAgent):
    """Lead Finder Agent for classification and scoring."""
    
    def __init__(self, *args, **kwargs):
        """Initialize Lead Finder Agent."""
        super().__init__(*args, **kwargs)
        
        self.config_section = self.config.get("lead_finder", {})
        self.max_leads_per_day = self.config_section.get("max_leads_per_day", 100)
        self.quality_threshold = self.config_section.get("quality_threshold", 6.0)
        self.default_quality_score = self.config_section.get("default_quality_score", 5.0)
        self.processing_time = self.config_section.get("processing_time", "10:00")
        self.processing_interval_minutes = self._get_interval_minutes(
            self.config_section.get("processing_interval_minutes")
        )
        
        # Initialize classifier and scorer
        self.classifier = LeadClassifier(llm_client=self.llm_client)
        self.scorer = QualityScorer()
        
        self.scheduler = BlockingScheduler()
        self._setup_scheduler()
    
    def _setup_scheduler(self) -> None:
        """Setup scheduled tasks."""
        if self.processing_interval_minutes:
            self.scheduler.add_job(
                self.process_uncontacted_leads,
                trigger=IntervalTrigger(minutes=self.processing_interval_minutes),
                id='process_leads_interval',
                next_run_time=datetime.now()
            )
        else:
            hour, minute = map(int, self.processing_time.split(":"))
            self.scheduler.add_job(
                self.process_uncontacted_leads,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='process_leads'
            )
    
    def run(self) -> None:
        """Main agent loop."""
        self.logger.info("Lead Finder Agent running")
        self.scheduler.start()
    
    def read_uncontacted_leads(self) -> List[Lead]:
        """
        Read uncontacted leads from Google Sheets.
        
        Returns:
            List of uncontacted leads
        """
        filters = {"contact_status": "Not Contacted"}
        return self.state_manager.read_leads(filters)
    
    def analyse_lead(self, lead: Lead) -> Lead:
        """
        Analyse and enrich lead data.
        
        Args:
            lead: Lead to analyse
        
        Returns:
            Enriched lead
        """
        # Classify if not already classified
        if not lead.classification:
            lead.classification = self.classify_prospect(lead)
        
        # Calculate quality score if missing or placeholder
        if lead.quality_score is None or getattr(lead, "quality_score_placeholder", False):
            lead.quality_score = self.calculate_quality_score(lead)
            lead.quality_score_placeholder = False
        
        return lead

    @staticmethod
    def _get_interval_minutes(value):
        """Return interval minutes as int if value is truthy, else None."""
        if value in (None, "", 0):
            return None
        try:
            minutes = int(value)
            return minutes if minutes > 0 else None
        except (TypeError, ValueError):
            return None
    
    def classify_prospect(self, lead: Lead) -> str:
        """
        Classify prospect as Speaker, Sponsor, or Other.
        
        Args:
            lead: Lead to classify
        
        Returns:
            Classification string
        """
        return self.classifier.classify(lead)
    
    def calculate_quality_score(self, lead: Lead) -> float:
        """
        Calculate quality score for lead.
        
        Args:
            lead: Lead to score
        
        Returns:
            Quality score (1.0-10.0)
        """
        return self.scorer.calculate_score(lead)
    
    def update_lead_classification(self, lead: Lead) -> bool:
        """
        Update lead classification and quality score in Google Sheets.
        
        Args:
            lead: Lead with updated data
        
        Returns:
            True if successful, False otherwise
        """
        updates = {
            "Classification": lead.classification,
            "Quality Score": lead.quality_score,
            "Last Updated": datetime.now().isoformat()
        }
        
        return self.state_manager.update_lead(lead.id, updates)
    
    def process_uncontacted_leads(self) -> None:
        """Process uncontacted leads (scheduled task)."""
        self.logger.info("Processing uncontacted leads")
        
        try:
            # Read uncontacted leads
            leads = self.read_uncontacted_leads()
            
            # Limit processing
            leads_to_process = leads[:self.max_leads_per_day]
            
            processed = 0
            for lead in leads_to_process:
                try:
                    # Analyse lead
                    analysed_lead = self.analyse_lead(lead)
                    
                    # Update in Google Sheets
                    if self.update_lead_classification(analysed_lead):
                        processed += 1
                        self.logger.debug(f"Processed lead: {lead.id} - {lead.classification} (score: {lead.quality_score})")
                    
                    # Publish event
                    self.publish_event("lead_discovered", {
                        "agent_to": "SalesManager",
                        "lead_id": lead.id,
                        "classification": analysed_lead.classification,
                        "quality_score": analysed_lead.quality_score
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error processing lead {lead.id}: {e}")
                    continue
            
            self.logger.info(f"Processed {processed} leads")
            
        except Exception as e:
            self.logger.error(f"Error in process_uncontacted_leads: {e}")

