"""
Seed FIR Documents Script
Uploads and ingests sample FIR documents into the vault and knowledge graph.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.vault_service import get_vault_service
from app.services.graph_rag.ingestion import IngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_fir_documents():
    """Upload and ingest all FIR documents from sample_documents directory."""
    
    # Get services
    vault_service = get_vault_service()
    
    # Try to initialize ingestion pipeline, but continue if it fails
    ingestion_pipeline = None
    try:
        ingestion_pipeline = IngestionPipeline()
        logger.info("Ingestion pipeline initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize ingestion pipeline: {e}")
        logger.warning("Will upload files but skip ingestion. LLM may not be configured or available.")
        ingestion_pipeline = None
    
    # Sample documents directory
    sample_docs_dir = Path(__file__).parent.parent / "sample_documents"
    
    if not sample_docs_dir.exists():
        logger.error(f"Sample documents directory not found: {sample_docs_dir}")
        return
    
    # Get all FIR text files
    fir_files = list(sample_docs_dir.glob("FIR_*.txt"))
    
    if not fir_files:
        logger.warning(f"No FIR documents found in {sample_docs_dir}")
        return
    
    logger.info(f"Found {len(fir_files)} FIR documents to process")
    
    uploaded_files = []
    
    # Step 1: Upload all files to vault
    for fir_file in fir_files:
        try:
            logger.info(f"Uploading {fir_file.name}...")
            
            # Read file content
            with open(fir_file, "rb") as f:
                file_content = f.read()
            
            # Upload to vault
            metadata = vault_service.upload_file(
                file_content=file_content,
                filename=fir_file.name,
                clearance_level="L3",
                uploaded_by="system",
                content_type="text/plain",
            )
            
            uploaded_files.append((metadata, fir_file))
            logger.info(f"✓ Uploaded {fir_file.name} (ID: {metadata.id})")
            
        except Exception as e:
            logger.error(f"✗ Failed to upload {fir_file.name}: {e}")
            continue
    
    logger.info(f"\nUploaded {len(uploaded_files)} files successfully")
    
    # Step 2: Ingest all uploaded files into knowledge graph (if pipeline is available)
    if ingestion_pipeline is None:
        logger.warning("\n⚠ Skipping ingestion - ingestion pipeline not available")
        logger.warning("Files have been uploaded to vault. You can ingest them later via the UI.")
        return
    
    logger.info("\nStarting ingestion into knowledge graph...")
    
    ingested_count = 0
    
    for metadata, fir_file in uploaded_files:
        try:
            logger.info(f"Ingesting {metadata.filename}...")
            
            # Get file content
            file_content = vault_service.get_file_content(metadata.id)
            if not file_content:
                logger.error(f"✗ Could not retrieve content for {metadata.filename}")
                continue
            
            # Extract text (already text file, just decode)
            text_content = file_content.decode('utf-8')
            
            # Ingest into knowledge graph
            result = await ingestion_pipeline.ingest_text(
                text=text_content,
                source_id=f"file_{metadata.id}",
                source_name=metadata.filename,
                clearance_level=metadata.clearance_level,
            )
            
            logger.info(
                f"✓ Ingested {metadata.filename}: "
                f"{result['entities_extracted']} entities, "
                f"{result['relations_extracted']} relations, "
                f"{result['chunks_created']} chunks"
            )
            
            ingested_count += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to ingest {metadata.filename}: {e}", exc_info=True)
            continue
    
    logger.info(f"\n✓ Successfully ingested {ingested_count}/{len(uploaded_files)} files")
    logger.info("Seed script completed!")


if __name__ == "__main__":
    asyncio.run(seed_fir_documents())
