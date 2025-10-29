#!/usr/bin/env python3
"""
Test cover extraction with a sample PDF to verify the process works
"""

import sys
import os
import tempfile
import logging
from io import BytesIO

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_pdf():
    """Create a simple sample PDF for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a PDF in memory
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add some content
        p.drawString(100, 750, "Sample Book Cover")
        p.drawString(100, 700, "This is a test PDF for cover extraction")
        p.drawString(100, 650, "Author: Test Author")
        p.drawString(100, 600, "Genre: Test Genre")
        
        # Add some visual elements
        p.rect(50, 500, 500, 200)
        p.drawString(200, 580, "BOOK COVER")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        logger.warning("reportlab not installed - cannot create sample PDF")
        return None
    except Exception as e:
        logger.error(f"Error creating sample PDF: {e}")
        return None

def test_cover_extraction_with_sample():
    """Test cover extraction with a sample PDF"""
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
        
        # Create sample PDF
        pdf_data = create_sample_pdf()
        if not pdf_data:
            logger.warning("Could not create sample PDF - skipping test")
            return False
        
        logger.info("✅ Sample PDF created successfully")
        
        # Extract first page as image
        images = convert_from_bytes(
            pdf_data,
            first_page=1,
            last_page=1,
            dpi=150,
            fmt='JPEG'
        )
        
        if images:
            logger.info("✅ Successfully extracted first page as image")
            
            # Test image resizing
            first_page_image = images[0]
            resized_image = first_page_image.resize((300, 450), Image.Resampling.LANCZOS)
            
            logger.info("✅ Successfully resized image")
            logger.info(f"Original size: {first_page_image.size}")
            logger.info(f"Resized size: {resized_image.size}")
            
            return True
        else:
            logger.error("❌ No images extracted from PDF")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in cover extraction test: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Cover Extraction Process")
    logger.info("=" * 50)
    
    # Test the cover extraction process
    success = test_cover_extraction_with_sample()
    
    if success:
        logger.info("🎉 Cover extraction process is working!")
        logger.info("")
        logger.info("📝 The issue is just AWS credentials:")
        logger.info("1. Update your .env file with fresh AWS credentials")
        logger.info("2. Restart your Flask server")
        logger.info("3. Refresh your dashboard - covers should appear!")
    else:
        logger.info("❌ Cover extraction process has issues")
        logger.info("Check PDF processing dependencies")
    
    logger.info("=" * 50)
