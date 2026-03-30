"""
NdviObservation model — shadow-run proxy validation.

One row per pipeline run date. Stores Kilombero NDVI from MODIS MOD13A2
(via Google Earth Engine) so forecast_logs drought/flood signals can be
correlated with vegetation stress after evaluation windows close.
"""
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, text
from app.core.database import Base


class NdviObservation(Base):
    __tablename__ = "ndvi_observations"

    id = Column(Integer, autoincrement=True, primary_key=True)

    # Temporal keys
    run_date = Column(Date, nullable=False, index=True,
                      comment="Pipeline run date this observation corresponds to")
    observed_date = Column(Date, nullable=False, index=True,
                           comment="Date of satellite pass used (nearest within ±3 days of run_date)")

    location_id = Column(Integer, nullable=True)

    # NDVI metrics
    ndvi_mean = Column(Numeric(5, 4), nullable=True,
                       comment="Mean NDVI across Kilombero bounding box [-1, 1]")
    ndvi_anomaly = Column(Numeric(6, 4), nullable=True,
                          comment="Deviation from 2015-2024 same-month historical mean")
    pixel_coverage = Column(Numeric(5, 2), nullable=True,
                            comment="Percentage of valid (cloud-free) pixels 0-100")

    # Provenance
    source = Column(String(50), nullable=False, server_default="MODIS_MOD13A2")
    is_backfilled = Column(Boolean, nullable=False, server_default=text("false"),
                           comment="True if inserted by backfill script")
    created_at = Column(DateTime(timezone=True), nullable=False,
                        server_default=text("now()"))

    def __repr__(self):
        return (
            f"<NdviObservation run_date={self.run_date} "
            f"ndvi_mean={self.ndvi_mean} anomaly={self.ndvi_anomaly}>"
        )
