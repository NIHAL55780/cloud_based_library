#!/usr/bin/env python3
"""
Quick test to verify cover extraction is working
"""

import sys
import os
sys.path.append('.')

def test_cover_extraction_directly():
    """Test cover extraction without Flask server"""
    try:
        from pdf_cover_extractor import PDFCoverExtractor
        
        print("✅ Cover extractor imported successfully")
        
        # Initialize extractor
        extractor = PDFCoverExtractor()
        print("✅ Cover extractor initialized")
        
        # Test with a real filename from your S3
        test_filename = "Arundhati Roy - The God of Small Things.pdf"
        print(f"Testing cover extraction for: {test_filename}")
        
        # This will show us exactly what's happening
        try:
            cover_url = extractor.get_cover_url(test_filename)
            
            if cover_url:
                print(f"✅ SUCCESS! Cover URL: {cover_url}")
                print("🎉 Cover extraction is working!")
                return True
            else:
                print("❌ No cover URL generated")
                return False
                
        except Exception as e:
            print(f"❌ Cover extraction failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error importing cover extractor: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Cover Extraction Directly")
    print("=" * 50)
    
    success = test_cover_extraction_directly()
    
    if success:
        print("\n🎉 Cover extraction is working!")
        print("The issue is likely:")
        print("1. Flask server needs to be restarted")
        print("2. Frontend needs to refresh")
        print("3. AWS credentials may need updating")
    else:
        print("\n❌ Cover extraction needs debugging")
        print("Check AWS credentials and S3 access")
    
    print("=" * 50)
