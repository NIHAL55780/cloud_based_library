"""
Enhanced PDF Cover Extractor with Fallback

This version tries to extract real covers from PDFs, but falls back to
beautiful placeholder covers if Poppler is not available.
"""

import os
import io
import tempfile
import logging
from typing import Optional, Tuple
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image, ImageDraw, ImageFont

from config import Config

logger = logging.getLogger(__name__)


class EnhancedPDFCoverExtractor:
    def __init__(self):
        """Initialize the enhanced PDF cover extractor with S3 client."""
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
    
    def get_cover_url(self, filename: str) -> Optional[str]:
        """
        Get cover URL for a book, extracting if necessary or creating placeholder.
        
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
            
            # Try to extract real cover
            real_cover_url = self._extract_real_cover(filename)
            if real_cover_url:
                return real_cover_url
            
            # Fall back to placeholder cover
            placeholder_url = self._create_placeholder_cover(filename)
            if placeholder_url:
                logger.info(f"Created placeholder cover for {filename}")
                return placeholder_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cover URL for {filename}: {e}")
            return None
    
    def _extract_real_cover(self, filename: str) -> Optional[str]:
        """Try to extract real cover from PDF"""
        try:
            # Try to import pdf2image
            from pdf2image import convert_from_bytes
            
            # Download PDF from S3
            pdf_data = self._download_pdf_from_s3(filename)
            if not pdf_data:
                return None
            
            # Try different Poppler paths
            poppler_paths = [
                r'C:\poppler\Library\bin',
                r'C:\poppler\bin',
                r'C:\Program Files\poppler\bin',
                r'C:\Program Files (x86)\poppler\bin',
                None
            ]
            
            for poppler_path in poppler_paths:
                try:
                    images = convert_from_bytes(
                        pdf_data,
                        first_page=1,
                        last_page=1,
                        dpi=150,
                        fmt='JPEG',
                        poppler_path=poppler_path
                    )
                    
                    if images:
                        # Process and upload the real cover
                        return self._process_and_upload_cover(images[0], filename)
                        
                except Exception as e:
                    logger.debug(f"Poppler path {poppler_path} failed: {e}")
                    continue
            
            return None
            
        except ImportError:
            logger.warning("pdf2image not available, using placeholder covers")
            return None
        except Exception as e:
            logger.warning(f"Real cover extraction failed: {e}")
            return None
    
    def _create_placeholder_cover(self, filename: str) -> Optional[str]:
        """Create a beautiful placeholder cover"""
        try:
            # Extract title and author from filename
            title, author = self._parse_filename(filename)
            
            # Create placeholder image
            cover_image = self._generate_placeholder_image(title, author)
            if not cover_image:
                return None
            
            # Upload placeholder cover
            cover_key = f"{self.covers_prefix}{filename.replace('.pdf', '.jpg')}"
            return self._upload_cover_to_s3(cover_image, cover_key)
            
        except Exception as e:
            logger.error(f"Error creating placeholder cover: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Tuple[str, str]:
        """Parse filename to extract title and author"""
        name_without_ext = filename.replace('.pdf', '')
        
        # Try different patterns
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ')
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
        elif ' by ' in name_without_ext.lower():
            parts = name_without_ext.split(' by ')
            if len(parts) >= 2:
                return parts[1].strip(), parts[0].strip()  # Swap for title, author
        
        # Default fallback
        return name_without_ext, "Unknown Author"
    
    def _generate_placeholder_image(self, title: str, author: str, width: int = 300, height: int = 450) -> Optional[bytes]:
        """Generate a beautiful placeholder cover image"""
        try:
            # Create gradient background
            img = Image.new('RGB', (width, height), color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Add gradient effect
            for y in range(height):
                color_value = int(44 + (y / height) * 50)
                draw.line([(0, y), (width, y)], fill=(color_value, color_value + 20, color_value + 40))
            
            # Add text
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title (split into lines if too long)
            title_words = title.split()
            lines = []
            current_line = []
            
            for word in title_words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                bbox = draw.textbbox((0, 0), test_line, font=font_large)
                if bbox[2] - bbox[0] > width - 40:  # Too wide
                    if current_line:
                        lines.append(' '.join(current_line[:-1]))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw title lines
            y_pos = height // 3
            for line in lines[:3]:  # Max 3 lines
                bbox = draw.textbbox((0, 0), line, font=font_large)
                text_width = bbox[2] - bbox[0]
                x_pos = (width - text_width) // 2
                draw.text((x_pos, y_pos), line, fill='white', font=font_large)
                y_pos += 35
            
            # Draw author
            y_pos += 20
            author_text = f"by {author}"
            bbox = draw.textbbox((0, 0), author_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            x_pos = (width - text_width) // 2
            draw.text((x_pos, y_pos), author_text, fill='#bdc3c7', font=font_small)
            
            # Add decorative border
            draw.rectangle([5, 5, width-5, height-5], outline='#3498db', width=3)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating placeholder image: {e}")
            return None
    
    def _process_and_upload_cover(self, image: Image.Image, filename: str) -> Optional[str]:
        """Process and upload a real cover image"""
        try:
            # Resize image
            resized_image = self._resize_image(image, 300, 450)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            resized_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_buffer.seek(0)
            
            # Upload to S3
            cover_key = f"{self.covers_prefix}{filename.replace('.pdf', '.jpg')}"
            return self._upload_cover_to_s3(img_buffer.getvalue(), cover_key)
            
        except Exception as e:
            logger.error(f"Error processing real cover: {e}")
            return None
    
    def _resize_image(self, image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        width, height = image.size
        aspect_ratio = width / height
        
        if width > max_width or height > max_height:
            if aspect_ratio > (max_width / max_height):
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _cover_exists(self, cover_key: str) -> bool:
        """Check if cover image already exists in S3"""
        try:
            self.s3_client.head_object(Bucket=Config.S3_BUCKET_NAME, Key=cover_key)
            return True
        except ClientError:
            return False
    
    def _get_cover_url(self, cover_key: str) -> str:
        """Generate a presigned URL for the cover image"""
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
        """Download PDF from S3"""
        try:
            s3_key = f"{Config.BOOKS_PREFIX}{filename}"
            response = self.s3_client.get_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=s3_key
            )
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Failed to download PDF {filename}: {e}")
            return None
    
    def _upload_cover_to_s3(self, cover_image: bytes, cover_key: str) -> Optional[str]:
        """Upload cover image to S3"""
        try:
            self.s3_client.put_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=cover_key,
                Body=cover_image,
                ContentType='image/jpeg',
                CacheControl='max-age=31536000'  # Cache for 1 year
            )
            
            return self._get_cover_url(cover_key)
            
        except Exception as e:
            logger.error(f"Failed to upload cover image: {e}")
            return None


# Global instance
cover_extractor = EnhancedPDFCoverExtractor()
