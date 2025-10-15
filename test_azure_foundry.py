#!/usr/bin/env python3
"""
Test script for Azure AI Foundry Vision Reasoner
Tests the Azure AI Foundry agent integration without MQTT
"""
import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_azure_foundry_integration():
    """Test Azure AI Foundry agent integration"""
    print("=" * 60)
    print("Azure AI Foundry Vision Reasoner Test")
    print("=" * 60)
    
    try:
        # Import the vision analyzer
        from azure_foundry_reasoner import AzureFoundryVisionAnalyzer
        
        print("✅ Successfully imported AzureFoundryVisionAnalyzer")
        
        # Initialize the analyzer
        print("\n🔄 Initializing Azure AI Foundry client...")
        analyzer = AzureFoundryVisionAnalyzer()
        print("✅ Azure AI Foundry client initialized successfully")
        
        # Check for test images
        test_images = []
        image_dir = "data/images"
        
        if os.path.exists(image_dir):
            for file in os.listdir(image_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    test_images.append(os.path.join(image_dir, file))
        
        # If no images in data/images, check current directory
        if not test_images:
            for file in os.listdir('.'):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    test_images.append(file)
        
        if not test_images:
            print("\n⚠️  No test images found!")
            print("Please add some test images to:")
            print("  - data/images/ directory, or")
            print("  - current directory")
            print("\nSupported formats: .jpg, .jpeg, .png, .bmp, .tiff")
            return False
        
        print(f"\n📸 Found {len(test_images)} test image(s):")
        for i, img in enumerate(test_images[:3], 1):  # Test max 3 images
            print(f"  {i}. {img}")
        
        # Test image analysis
        test_image = test_images[0]
        print(f"\n🔍 Testing analysis with: {test_image}")
        
        start_time = datetime.now()
        result = analyzer.analyze_image(test_image, 1)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Analysis completed in {duration:.2f} seconds")
        print(f"📊 Result length: {len(result)} characters")
        print(f"\n📝 Analysis preview:")
        print("-" * 50)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 50)
        
        # Test JSON serialization
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "image_path": test_image,
            "detector": "test_script",
            "confidence": 0.95,
            "reasoning": result,
            "model_used": "azure_foundry_agent",
            "analyzed_at": datetime.now().isoformat()
        }
        
        try:
            json_result = json.dumps(test_data)
            print("\n✅ JSON serialization successful")
            print(f"📦 JSON size: {len(json_result)} bytes")
        except Exception as json_error:
            print(f"\n❌ JSON serialization failed: {json_error}")
            return False
        
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Start your MQTT broker")
        print("2. Run: python azure_foundry_reasoner.py")
        print("3. Send test messages to trigger analysis")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPlease install required dependencies:")
        print("pip install -r requirements-azure-foundry.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Environment Configuration Check")
    print("-" * 40)
    
    required_vars = [
        "AZURE_PROJECT_ENDPOINT",
        "AGENT_ID"
    ]
    
    optional_vars = [
        "MQTT_BROKER",
        "MQTT_PORT", 
        "MQTT_INPUT_TOPIC",
        "MQTT_OUTPUT_TOPIC"
    ]
    
    missing_required = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive parts of the endpoint
            if "ENDPOINT" in var:
                masked_value = value[:30] + "..." if len(value) > 30 else value
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"ℹ️  {var}: {value}")
        else:
            print(f"ℹ️  {var}: Using default")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {missing_required}")
        print("\nPlease set them in your .env file or environment:")
        for var in missing_required:
            print(f"export {var}=your_value_here")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

if __name__ == "__main__":
    print("Loading environment variables...")
    
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("ℹ️  python-dotenv not installed, using system environment only")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    # Check environment
    env_ok = check_environment()
    
    if env_ok:
        # Run integration test
        success = test_azure_foundry_integration()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ Environment check failed. Please fix configuration before testing.")
        sys.exit(1)