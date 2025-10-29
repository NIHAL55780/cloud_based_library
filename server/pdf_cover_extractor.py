"""
PDF Cover Extractor Utility

This module provides functionality to extract the first page of a PDF as a cover image.
It downloads PDFs from S3, extracts the first page, converts it to an image,
and uploads the cover image back to S3 for caching.
"""

import os
import io
import tempfile
import logging
from typing import Optional, Tuple
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pdf2image import convert_from_bytes
from PIL import Image
from PyPDF2 import PdfReader

from config import Config

logger = logging.getLogger(__name__)


class PDFCoverExtractor:
    def __init__(self):
        """Initialize the PDF cover extractor with S3 client."""
        self.s3_client = self._get_s3_client()
        self.covers_prefix = 'covers/'
    
    def _get_s3_client(self):
        """Get S3 client with proper error handling."""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                aws_session_token=Config.AWS_SESSION_TOKEN,
                region_name=Config.AWS_REGION
            )
        except Exception as e:
            logger.error(f"Failed to create S3 client: {e}")
            raise
    
    def extract_cover_from_s3(self, filename: str, max_width: int = 300, max_height: int = 450) -> Optional[str]:
        """
        Extract cover image from PDF stored in S3.
        
        Args:
            filename: The PDF filename in S3
            max_width: Maximum width for the cover image
            max_height: Maximum height for the cover image
            
        Returns:
            S3 URL of the cover image, or None if extraction failed
        """
        try:
            # Check if cover already exists
            cover_key = f"{self.covers_prefix}{filename.replace('.pdf', '.jpg')}"
            if self._cover_exists(cover_key):
                logger.info(f"Cover already exists for {filename}")
                return self._get_cover_url(cover_key)
            
            # Download PDF from S3
            pdf_data = self._download_pdf_from_s3(filename)
            if not pdf_data:
                logger.error(f"Failed to download PDF: {filename}")
                return None
            
            # Extract first page as image
            cover_image = self._extract_first_page_as_image(pdf_data, max_width, max_height)
            if not cover_image:
                logger.error(f"Failed to extract cover from PDF: {filename}")
                return None
            
            # Upload cover image to S3
            cover_url = self._upload_cover_to_s3(cover_image, cover_key)
            if cover_url:
                logger.info(f"Successfully extracted and uploaded cover for {filename}")
                return cover_url
            else:
                logger.error(f"Failed to upload cover for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting cover for {filename}: {e}")
            return None
    
    def _cover_exists(self, cover_key: str) -> bool:
        """Check if cover image already exists in S3."""
        try:
            self.s3_client.head_object(Bucket=Config.S3_BUCKET_NAME, Key=cover_key)
            return True
        except ClientError:
            return False
    
    def _get_cover_url(self, cover_key: str) -> str:
        """Generate a presigned URL for the cover image."""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': Config.S3_BUCKET_NAME, 'Key': cover_key},
                ExpiresIn=86400  # 24 hours
            )
        except Exception as e:
            logger.error(f"Failed to generate cover URL: {e}")
            return ""
    
    def _download_pdf_from_s3(self, filename: str) -> Optional[bytes]:
        """Download PDF from S3."""
        try:
            s3_key = f"{Config.BOOKS_PREFIX}{filename}"
            response = self.s3_client.get_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to download PDF {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF {filename}: {e}")
            return None
    
    def _extract_first_page_as_image(self, pdf_data: bytes, max_width: int, max_height: int) -> Optional[bytes]:
        """Extract the first page of PDF as an image."""
        try:
            # Convert first page to image
            # Try different Poppler paths
            poppler_paths = [
                r'C:\poppler\Library\bin',
                r'C:\poppler\bin',
                r'C:\Program Files\poppler\bin',
                r'C:\Program Files (x86)\poppler\bin',
                None  # Try without path (if in PATH)
            ]
            
            images = None
            for poppler_path in poppler_paths:
                try:
                    images = convert_from_bytes(
                        pdf_data,
                        first_page=1,
                        last_page=1,
                        dpi=150,  # Good quality for thumbnails
                        fmt='JPEG',
                        poppler_path=poppler_path
                    )
                    if images:
                        break
                except Exception as e:
                    logger.debug(f"Poppler path {poppler_path} failed: {e}")
                    continue
            
            if not images:
                # Try without specifying poppler_path at all
                try:
                    images = convert_from_bytes(
                        pdf_data,
                        first_page=1,
                        last_page=1,
                        dpi=150,
                        fmt='JPEG'
                    )
                except Exception as e:
                    logger.error(f"All Poppler paths failed: {e}")
                    return None
            
            if not images:
                logger.error("No images extracted from PDF")
                return None
            
            # Get the first (and only) image
            first_page_image = images[0]
            
            # Resize image while maintaining aspect ratio
            resized_image = self._resize_image(first_page_image, max_width, max_height)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            resized_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error extracting first page as image: {e}")
            return None
    
    def _resize_image(self, image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Resize image while maintaining aspect ratio."""
        # Calculate new dimensions
        width, height = image.size
        aspect_ratio = width / height
        
        if width > max_width or height > max_height:
            if aspect_ratio > (max_width / max_height):
                # Width is the limiting factor
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                # Height is the limiting factor
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _upload_cover_to_s3(self, cover_image: bytes, cover_key: str) -> Optional[str]:
        """Upload cover image to S3."""
        try:
            self.s3_client.put_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=cover_key,
                Body=cover_image,
                ContentType='image/jpeg',
                CacheControl='max-age=31536000'  # Cache for 1 year
            )
            
            # Generate presigned URL
            return self._get_cover_url(cover_key)
            
        except Exception as e:
            logger.error(f"Failed to upload cover image: {e}")
            return None
    
    def get_cover_url(self, filename: str) -> Optional[str]:
        """
        Get cover URL for a book, extracting if necessary.
        
        Args:
            filename: The PDF filename
            
        Returns:
            URL of the cover image or None if not available
        """
        try:
            # Check if cover exists first
            cover_key = f"{self.covers_prefix}{filename.replace('.pdf', '.jpg')}"
            if self._cover_exists(cover_key):
                return self._get_cover_url(cover_key)
            
            # Extract cover if it doesn't exist
            return self.extract_cover_from_s3(filename)
            
        except Exception as e:
            logger.error(f"Error getting cover URL for {filename}: {e}")
            return None


# Global instance
cover_extractor = PDFCoverExtractor()
