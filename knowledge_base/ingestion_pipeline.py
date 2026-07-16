import asyncio
import logging
from sqlalchemy.orm import Session
from app.models.models import Document

logger = logging.getLogger(__name__)

async def ingest_document_pipeline(document_id: str, db: Session):
    logger.info(f"Starting ingestion for document {document_id}")
    await asyncio.sleep(2) # Mock processing time
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.is_ingested = True
        db.commit()
        logger.info(f"Document {document_id} marked as ingested.")
    else:
        logger.error(f"Document {document_id} not found for ingestion.")
