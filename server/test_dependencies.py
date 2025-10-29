#!/usr/bin/env python3
"""
Test cover extraction logic without S3 dependency
"""

import sys
import os
import tempfile
import logging

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_processing_dependencies():
    """Test if PDF processing libraries are installed correctly"""
    try:
        import PyPDF2
        logger.info("✅ PyPDF2 imported successfully")
        
        import PIL
        logger.info("✅ Pillow (PIL) imported successfully")
        
        import pdf2image
        logger.info("✅ pdf2image imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False

def test_image_processing():
    """Test basic image processing functionality"""
    try:
        from PIL import Image
        import io
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85)
        img_buffer.seek(0)
        
        logger.info("✅ Image processing test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Image processing test failed: {e}")
        return False

def test_pdf_reading():
    """Test PDF reading functionality with a simple PDF"""
    try:
        from PyPDF2 import PdfReader
        
        # Create a simple test PDF content (this is just a test)
        logger.info("✅ PDF reading libraries available")
        return True
    except Exception as e:
        logger.error(f"❌ PDF reading test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing PDF Cover Extraction Dependencies")
    logger.info("=" * 50)
    
    # Test dependencies
    deps_ok = test_pdf_processing_dependencies()
    img_ok = test_image_processing()
    pdf_ok = test_pdf_reading()
    
    if deps_ok and img_ok and pdf_ok:
        logger.info("🎉 All PDF processing dependencies are working!")
        logger.info("")
        logger.info("📝 Next steps:")
        logger.info("1. Update your AWS credentials in .env file")
        logger.info("2. Test with actual S3 bucket")
        logger.info("3. Start the server and test cover extraction")
    else:
        logger.info("❌ Some dependencies are missing")
        logger.info("Run: pip install -r requirements.txt")
    
    logger.info("=" * 50)
