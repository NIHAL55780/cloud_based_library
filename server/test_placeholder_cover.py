#!/usr/bin/env python3
"""
Temporary workaround for cover extraction without Poppler
This creates placeholder covers until Poppler is properly configured
"""

import sys
import os
import tempfile
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_placeholder_cover(title, author, width=300, height=450):
    """Create a placeholder cover image"""
    try:
        # Create a new image with gradient background
        img = Image.new('RGB', (width, height), color='#2c3e50')
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect
        for y in range(height):
            color_value = int(44 + (y / height) * 50)  # Gradient from dark to lighter
            draw.line([(0, y), (width, y)], fill=(color_value, color_value + 20, color_value + 40))
        
        # Add title text
        try:
            # Try to use a nice font
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw title
        title_lines = title.split(' ')
        y_pos = height // 3
        
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            x_pos = (width - text_width) // 2
            draw.text((x_pos, y_pos), line, fill='white', font=font_large)
            y_pos += 35
        
        # Draw author
        y_pos += 20
        bbox = draw.textbbox((0, 0), f"by {author}", font=font_small)
        text_width = bbox[2] - bbox[0]
        x_pos = (width - text_width) // 2
        draw.text((x_pos, y_pos), f"by {author}", fill='#bdc3c7', font=font_small)
        
        # Add a decorative border
        draw.rectangle([5, 5, width-5, height-5], outline='#3498db', width=3)
        
        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG', quality=85, optimize=True)
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating placeholder cover: {e}")
        return None

def test_placeholder_cover():
    """Test the placeholder cover creation"""
    try:
        cover_data = create_placeholder_cover(
            "The God of Small Things", 
            "Arundhati Roy"
        )
        
        if cover_data:
            logger.info("✅ Placeholder cover created successfully")
            logger.info(f"Cover size: {len(cover_data)} bytes")
            return True
        else:
            logger.error("❌ Failed to create placeholder cover")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing placeholder: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Placeholder Cover Creation")
    logger.info("=" * 50)
    
    success = test_placeholder_cover()
    
    if success:
        logger.info("🎉 Placeholder covers are working!")
        logger.info("This can be used as a temporary solution")
        logger.info("while Poppler is being configured")
    else:
        logger.info("❌ Placeholder cover creation failed")
    
    logger.info("=" * 50)
