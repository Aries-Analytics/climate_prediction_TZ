"""
Backtesting Service for Historical Simulation.

This service applies parametric insurance trigger thresholds to historical
climate data to simulate what payouts would have been made if the product
had been active during that period.

Methodology:
1. Fetch historical climate data for the specified period
2. Apply trigger thresholds month-by-month
3. Generate trigger events when thresholds are breached
4. Create claims for simulated farmers
5. Calculate loss ratios and sustainability metrics
"""
import random
from datetime import date, datetime
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.simulation import (
    SimulationRun, SimulatedFarmer, SimulatedTrigger, 
    SimulatedClaim, SimulationStatus
)
from app.models.location import Location
from app.models.climate_data import ClimateData


# Kilombero Basin village distribution (based on geographic spread)
KILOMBERO_VILLAGES = {
    "Ifakara": 0.30,      # 30% - Main town
    "Mlimba": 0.20,       # 20% - Northern region
    "Kidatu": 0.15,       # 15% - Dam area
    "Malinyi": 0.15,      # 15% - Eastern region
    "Mangula": 0.10,      # 10% - Central
    "Kibaoni": 0.10       # 10% - Southern region
}

# Farm size distribution (hectares)
FARM_SIZE_DISTRIBUTION = [
    (0.5, 1.0, 0.60),   # 60% small farms (0.5-1 ha)
    (1.0, 2.0, 0.30),   # 30% medium farms (1-2 ha)
    (2.0, 5.0, 0.10)    # 10% large farms (2-5 ha)
]

# Trigger thresholds (from MOROGORO_RICE_PILOT_SPECIFICATION)
TRIGGER_THRESHOLDS = {
    "drought_vegetative": {
        "type": "drought",
        "threshold_mm": 50,      # <50mm/month during vegetative
        "months": [11, 12, 1],   # Nov-Jan (vegetative for long rains)
        "severity_levels": {
            "mild": (40, 50),
            "moderate": (25, 40),
            "severe": (0, 25)
        }
    },
    "drought_flowering": {
        "type": "drought",
        "threshold_mm": 80,      # <80mm/month during flowering
        "months": [2, 3],        # Feb-Mar (flowering)
        "severity_levels": {
            "mild": (60, 80),
            "moderate": (40, 60),
            "severe": (0, 40)
        }
    },
    "flood": {
        "type": "flood",
        "threshold_mm": 300,     # >300mm/month = flood
        "months": list(range(1, 13)),  # Any month
        "severity_levels": {
            "mild": (300, 400),
            "moderate": (400, 500),
            "severe": (500, 1000)
        }
    }
}

# Payout rates (USD per farmer)
PAYOUT_RATES = {
    "drought": {"mild": 30, "moderate": 45, "severe": 60},
    "flood": {"mild": 40, "moderate": 55, "severe": 75},
    "crop_failure": {"mild": 50, "moderate": 70, "severe": 90}
}

# External validation references (documented climate events)
KNOWN_EVENTS = {
    2016: {"type": "drought", "source": "FEWS NET", "notes": "East Africa drought"},
    2017: {"type": "drought", "source": "WFP Report", "notes": "Prolonged dry spell"},
    2019: {"type": "flood", "source": "OCHA", "notes": "Heavy rains, flooding"},
    2020: {"type": "flood", "source": "Tanzania Met", "notes": "Above-normal rainfall"},
    2021: {"type": "drought", "source": "FEWS NET", "notes": "Failed long rains"},
    2023: {"type": "flood", "source": "News Reports", "notes": "El Niño flooding"}
}


class BacktestingService:
    """Service for running historical backtesting simulations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_simulation(
        self,
        name: str,
        location_id: int,
        start_year: int,
        end_year: int,
        farmer_count: int = 1000,
        crop_type: str = "rice",
        description: str = None,
        annual_premium_per_farmer: float = 91.0  # Sustainable premium (75% loss ratio target)
    ) -> SimulationRun:
        """Create a new simulation run."""
        
        # Get location
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location {location_id} not found")
        
        # Calculate premiums
        years = end_year - start_year + 1
        total_premiums = farmer_count * annual_premium_per_farmer * years
        
        simulation = SimulationRun(
            name=name,
            description=description,
            location_id=location_id,
            location_name=location.name,
            start_year=start_year,
            end_year=end_year,
            farmer_count=farmer_count,
            crop_type=crop_type,
            annual_premium_per_farmer=annual_premium_per_farmer,
            total_premiums_collected=total_premiums,
            status=SimulationStatus.PENDING.value
        )
        
        self.db.add(simulation)
        self.db.commit()
        self.db.refresh(simulation)
        
        return simulation
    
    def generate_farmer_portfolio(self, simulation: SimulationRun) -> List[SimulatedFarmer]:
        """Generate a portfolio of simulated farmers based on realistic distributions."""
        
        farmers = []
        farmer_num = 1
        
        for village, proportion in KILOMBERO_VILLAGES.items():
            village_count = int(simulation.farmer_count * proportion)
            
            for _ in range(village_count):
                # Determine farm size
                hectares = self._get_random_farm_size()
                
                # Calculate premium and coverage
                premium = simulation.annual_premium_per_farmer * (simulation.end_year - simulation.start_year + 1)
                coverage = simulation.crop_failure_payout_rate  # Max payout
                
                farmer = SimulatedFarmer(
                    simulation_id=simulation.id,
                    farmer_code=f"KLM-{farmer_num:04d}",
                    village=village,
                    hectares=hectares,
                    premium_paid=premium,
                    coverage_amount=coverage
                )
                farmers.append(farmer)
                farmer_num += 1
        
        # Add remaining farmers to largest village
        remaining = simulation.farmer_count - len(farmers)
        for _ in range(remaining):
            farmer = SimulatedFarmer(
                simulation_id=simulation.id,
                farmer_code=f"KLM-{farmer_num:04d}",
                village="Ifakara",
                hectares=self._get_random_farm_size(),
                premium_paid=simulation.annual_premium_per_farmer * (simulation.end_year - simulation.start_year + 1),
                coverage_amount=simulation.crop_failure_payout_rate
            )
            farmers.append(farmer)
            farmer_num += 1
        
        self.db.add_all(farmers)
        self.db.commit()
        
        return farmers
    
    def _get_random_farm_size(self) -> float:
        """Get a random farm size based on distribution."""
        rand = random.random()
        cumulative = 0
        
        for min_ha, max_ha, probability in FARM_SIZE_DISTRIBUTION:
            cumulative += probability
            if rand <= cumulative:
                return round(random.uniform(min_ha, max_ha), 2)
        
        return 1.0  # Default
    
    def fetch_historical_climate_data(
        self, 
        location_id: int, 
        start_year: int, 
        end_year: int
    ) -> Dict[int, Dict[int, float]]:
        """
        Fetch historical climate data (monthly rainfall) for the simulation period.
        
        Returns: {year: {month: rainfall_mm}}
        """
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {}
        
        # Query monthly rainfall aggregates
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        
        # Get data from climate_data table
        climate_records = self.db.query(
            func.extract('year', ClimateData.date).label('year'),
            func.extract('month', ClimateData.date).label('month'),
            func.sum(ClimateData.rainfall_mm).label('total_rainfall')
        ).filter(
            ClimateData.location_lat == location.latitude,
            ClimateData.location_lon == location.longitude,
            ClimateData.date.between(start_date, end_date)
        ).group_by(
            func.extract('year', ClimateData.date),
            func.extract('month', ClimateData.date)
        ).all()
        
        # Organize by year and month
        data = {}
        for record in climate_records:
            year = int(record.year)
            month = int(record.month)
            rainfall = float(record.total_rainfall or 0)
            
            if year not in data:
                data[year] = {}
            data[year][month] = rainfall
        
        return data
    
    def apply_trigger_thresholds(
        self, 
        climate_data: Dict[int, Dict[int, float]],
        simulation: SimulationRun
    ) -> List[SimulatedTrigger]:
        """
        Apply trigger thresholds to historical climate data.
        
        Returns list of trigger events where thresholds were breached.
        """
        triggers = []
        
        for year in range(simulation.start_year, simulation.end_year + 1):
            if year not in climate_data:
                continue
            
            monthly_data = climate_data[year]
            
            # Check each threshold type
            for threshold_name, config in TRIGGER_THRESHOLDS.items():
                for month in config["months"]:
                    if month not in monthly_data:
                        continue
                    
                    rainfall = monthly_data[month]
                    threshold = config["threshold_mm"]
                    trigger_type = config["type"]
                    
                    # Check if threshold breached
                    triggered = False
                    deviation = 0
                    
                    if trigger_type == "drought" and rainfall < threshold:
                        triggered = True
                        deviation = rainfall - threshold  # Negative
                    elif trigger_type == "flood" and rainfall > threshold:
                        triggered = True
                        deviation = rainfall - threshold  # Positive
                    
                    if triggered:
                        # Determine severity
                        severity = self._get_severity(rainfall, config["severity_levels"], trigger_type)
                        
                        # Get phenology stage
                        phenology = self._get_phenology_stage(month)
                        
                        # Get payout rate
                        payout_rate = PAYOUT_RATES.get(trigger_type, {}).get(severity, 60)
                        total_payout = simulation.farmer_count * payout_rate
                        
                        # Check external validation
                        external = KNOWN_EVENTS.get(year)
                        validation_text = None
                        validated = "pending"
                        if external and external["type"] == trigger_type:
                            validation_text = f"{external['source']}: {external['notes']}"
                            validated = "confirmed"
                        
                        trigger = SimulatedTrigger(
                            simulation_id=simulation.id,
                            year=year,
                            month=month,
                            trigger_type=trigger_type,
                            trigger_date=date(year, month, 15),  # Mid-month
                            observed_value=rainfall,
                            threshold_value=threshold,
                            deviation=deviation,
                            severity=severity,
                            phenology_stage=phenology,
                            farmers_affected=simulation.farmer_count,
                            payout_per_farmer=payout_rate,
                            total_payout=total_payout,
                            external_validation=validation_text,
                            validated=validated
                        )
                        triggers.append(trigger)
        
        if triggers:
            self.db.add_all(triggers)
            self.db.commit()
        
        return triggers
    
    def _get_severity(self, value: float, levels: Dict, trigger_type: str) -> str:
        """Determine severity level based on observed value."""
        for severity, (min_val, max_val) in levels.items():
            if trigger_type == "drought":
                if min_val <= value < max_val:
                    return severity
            else:  # flood
                if min_val <= value < max_val:
                    return severity
        return "moderate"  # Default
    
    def _get_phenology_stage(self, month: int) -> str:
        """Get rice phenology stage for a given month (Tanzania long rains)."""
        stages = {
            10: "land_preparation",
            11: "planting",
            12: "vegetative",
            1: "vegetative",
            2: "flowering",
            3: "flowering",
            4: "maturation",
            5: "harvest",
            6: "off_season",
            7: "off_season",
            8: "off_season",
            9: "land_preparation"
        }
        return stages.get(month, "unknown")
    
    def generate_claims(
        self, 
        simulation: SimulationRun, 
        triggers: List[SimulatedTrigger]
    ) -> List[SimulatedClaim]:
        """Generate claim records for triggered events."""
        
        farmers = self.db.query(SimulatedFarmer).filter(
            SimulatedFarmer.simulation_id == simulation.id
        ).all()
        
        claims = []
        claim_num = 1
        
        for trigger in triggers:
            for farmer in farmers:
                claim = SimulatedClaim(
                    simulation_id=simulation.id,
                    farmer_id=farmer.id,
                    trigger_id=trigger.id,
                    claim_code=f"CLM-SIM-{trigger.year}-{claim_num:05d}",
                    year=trigger.year,
                    trigger_type=trigger.trigger_type,
                    payout_amount=trigger.payout_per_farmer
                )
                claims.append(claim)
                claim_num += 1
        
        if claims:
            self.db.add_all(claims)
            self.db.commit()
        
        return claims
    
    def run_simulation(self, simulation_id: int) -> SimulationRun:
        """
        Run a complete backtesting simulation.
        
        Steps:
        1. Generate farmer portfolio
        2. Fetch historical climate data
        3. Apply trigger thresholds
        4. Generate claims
        5. Calculate summary metrics
        """
        simulation = self.db.query(SimulationRun).filter(
            SimulationRun.id == simulation_id
        ).first()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        try:
            # Update status
            simulation.status = SimulationStatus.RUNNING.value
            simulation.started_at = datetime.utcnow()
            self.db.commit()
            
            # Step 1: Generate farmers
            farmers = self.generate_farmer_portfolio(simulation)
            
            # Step 2: Fetch historical data
            climate_data = self.fetch_historical_climate_data(
                simulation.location_id,
                simulation.start_year,
                simulation.end_year
            )
            
            # Step 3: Apply thresholds
            triggers = self.apply_trigger_thresholds(climate_data, simulation)
            
            # Step 4: Generate claims
            claims = self.generate_claims(simulation, triggers)
            
            # Step 5: Calculate metrics
            total_payouts = sum(t.total_payout for t in triggers)
            loss_ratio = (total_payouts / simulation.total_premiums_collected) * 100 if simulation.total_premiums_collected > 0 else 0
            
            # Update simulation
            simulation.total_triggers = len(triggers)
            simulation.total_claims = len(claims)
            simulation.total_payouts = total_payouts
            simulation.loss_ratio = round(loss_ratio, 2)
            simulation.status = SimulationStatus.COMPLETED.value
            simulation.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(simulation)
            
            return simulation
            
        except Exception as e:
            simulation.status = SimulationStatus.FAILED.value
            simulation.error_message = str(e)
            self.db.commit()
            raise
    
    def get_simulation_summary(self, simulation_id: int) -> Dict:
        """Get a detailed summary of simulation results."""
        
        simulation = self.db.query(SimulationRun).filter(
            SimulationRun.id == simulation_id
        ).first()
        
        if not simulation:
            return {}
        
        # Get triggers by year
        triggers = self.db.query(SimulatedTrigger).filter(
            SimulatedTrigger.simulation_id == simulation_id
        ).order_by(SimulatedTrigger.year, SimulatedTrigger.month).all()
        
        yearly_summary = {}
        for trigger in triggers:
            if trigger.year not in yearly_summary:
                yearly_summary[trigger.year] = {
                    "triggers": [],
                    "total_payout": 0,
                    "validated": False
                }
            yearly_summary[trigger.year]["triggers"].append(trigger.to_dict())
            yearly_summary[trigger.year]["total_payout"] += trigger.total_payout
            if trigger.validated == "confirmed":
                yearly_summary[trigger.year]["validated"] = True
        
        return {
            "simulation": simulation.to_dict(),
            "yearly_summary": yearly_summary,
            "sustainability_analysis": {
                "loss_ratio": simulation.loss_ratio,
                "is_sustainable": simulation.loss_ratio < 80 if simulation.loss_ratio else None,
                "recommendation": self._get_sustainability_recommendation(simulation.loss_ratio)
            }
        }
    
    def _get_sustainability_recommendation(self, loss_ratio: float) -> str:
        """Get sustainability recommendation based on loss ratio."""
        if loss_ratio is None:
            return "Insufficient data"
        if loss_ratio < 40:
            return "Excellent - Premium may be too high, consider reduction"
        if loss_ratio < 60:
            return "Good - Sustainable with adequate reserves"
        if loss_ratio < 80:
            return "Acceptable - Within industry norms"
        if loss_ratio < 100:
            return "Concerning - Review premium adequacy"
        return "Unsustainable - Immediate premium adjustment required"
