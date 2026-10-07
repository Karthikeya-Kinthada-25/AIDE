from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class EvidenceImage(Base):
    __tablename__ = "evidence_images"

    id = Column(Integer, primary_key=True, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)

    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)

    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(20))
    megapixels = Column(Float)

    metadata_status = Column(String(100))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class ForensicAnalysis(Base):
    __tablename__ = "forensic_analysis"

    id = Column(Integer, primary_key=True, index=True)

    evidence_id = Column(
        Integer,
        nullable=False
    )

    ela_mean_error = Column(Float)
    ela_maximum_error = Column(Float)
    ela_standard_deviation = Column(Float)

    entropy = Column(Float)
    noise_mean = Column(Float)
    noise_standard_deviation = Column(Float)

    edge_density = Column(Float)
    laplacian_variance = Column(Float)

    forensic_score = Column(Float)
    assessment_level = Column(String(50))

    warning = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )