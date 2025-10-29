#!/usr/bin/env python3
"""
Test script for PDF cover extraction functionality
"""

import sys
import os
import logging

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_cover_extractor import PDFCoverExtractor
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cover_extraction():
    """Test the cover extraction functionality"""
    try:
        # Initialize the cover extractor
        extractor = PDFCoverExtractor()
        logger.info("Cover extractor initialized successfully")
        
        # Test with a sample filename (you can replace this with an actual PDF in your S3)
        test_filename = "sample-book.pdf"  # Replace with actual filename
        
        logger.info(f"Testing cover extraction for: {test_filename}")
        
        # Try to get cover URL
        cover_url = extractor.get_cover_url(test_filename)
        
        if cover_url:
            logger.info(f"✅ Cover URL generated successfully: {cover_url}")
            return True
        else:
            logger.warning(f"⚠️ No cover URL generated for {test_filename}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing cover extraction: {e}")
        return False

def test_config():
    """Test if configuration is properly set"""
    try:
        logger.info("Testing configuration...")
        logger.info(f"S3 Bucket: {Config.S3_BUCKET_NAME}")
        logger.info(f"AWS Region: {Config.AWS_REGION}")
        logger.info(f"Books Prefix: {Config.BOOKS_PREFIX}")
        
        # Check if AWS credentials are available
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            logger.info("✅ AWS credentials found")
            return True
        else:
            logger.warning("⚠️ AWS credentials not found in environment")
            return False
            
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing PDF Cover Extraction")
    logger.info("=" * 50)
    
    # Test configuration first
    config_ok = test_config()
    
    if config_ok:
        # Test cover extraction
        extraction_ok = test_cover_extraction()
        
        if extraction_ok:
            logger.info("🎉 All tests passed!")
        else:
            logger.info("⚠️ Cover extraction test failed (this might be expected if no PDFs are available)")
    else:
        logger.error("❌ Configuration test failed")
    
    logger.info("=" * 50)
