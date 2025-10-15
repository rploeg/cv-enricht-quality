#!/usr/bin/env python3
"""
Azure AI Foundry Vision Reasoner
Uses Azure AI Foundry Agent Service for image analysis with defect detection
Integrates with MQTT for receiving CV detection messages and publishing enriched results
"""
import os, json, sys, base64
from datetime import datetime, timezone
from typing import Optional
import logging

def get_timestamp():
    """Generate timestamp for logging"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log_message(message):
    """Print message with timestamp"""
    timestamp = get_timestamp()
    print(f"[{timestamp}] {message}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add error handling for imports
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents.models import (
        ListSortOrder, 
        FilePurpose,
        MessageRole,
        MessageInputContentBlock,
        MessageInputTextBlock,
        MessageInputImageUrlBlock,
        MessageImageUrlParam
    )
    log_message("[AZURE-FOUNDRY] Azure AI Projects SDK loaded successfully")
except Exception as e:
    log_message(f"[AZURE-FOUNDRY] ❌ Azure AI Projects SDK import failed: {e}")
    log_message("[AZURE-FOUNDRY] Please install with: pip install azure-ai-projects azure-identity")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
    log_message("[AZURE-FOUNDRY] MQTT client loaded successfully")
except Exception as e:
    log_message(f"[AZURE-FOUNDRY] ❌ MQTT client import failed: {e}")
    sys.exit(1)

try:
    from PIL import Image
    log_message("[AZURE-FOUNDRY] PIL (Pillow) loaded successfully")
except Exception as e:
    log_message(f"[AZURE-FOUNDRY] ❌ PIL (Pillow) import failed: {e}")
    sys.exit(1)

# Configuration - Environment variables with defaults
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_INPUT_TOPIC = os.getenv("MQTT_INPUT_TOPIC", "factory/line1/defects")
MQTT_OUTPUT_TOPIC = os.getenv("MQTT_OUTPUT_TOPIC", "factory/line1/defects/enriched")

# Azure AI Foundry Configuration
AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT", "https://ENDPOINT.services.ai.azure.com/api/projects/firstProject")
AGENT_ID = os.getenv("AGENT_ID", "AGENTIDfromPortal")

log_message(f"[AZURE-FOUNDRY] MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
log_message(f"[AZURE-FOUNDRY] Input Topic: {MQTT_INPUT_TOPIC}")
log_message(f"[AZURE-FOUNDRY] Output Topic: {MQTT_OUTPUT_TOPIC}")
log_message(f"[AZURE-FOUNDRY] Azure Project Endpoint: {AZURE_PROJECT_ENDPOINT}")
log_message(f"[AZURE-FOUNDRY] Agent ID: {AGENT_ID}")

class AzureFoundryVisionAnalyzer:
    """Azure AI Foundry Vision Analysis Client"""
    
    def __init__(self):
        """Initialize Azure AI Foundry client and agent"""
        try:
            # Use DefaultAzureCredential for secure authentication (managed identity preferred)
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=False,
                exclude_shared_token_cache_credential=True,
                exclude_visual_studio_code_credential=True
            )
            
            log_message("[AZURE-FOUNDRY] Initializing Azure AI Project client...")
            self.project_client = AIProjectClient(
                endpoint=AZURE_PROJECT_ENDPOINT,
                credential=credential
            )
            
            log_message("[AZURE-FOUNDRY] Retrieving agent configuration...")
            self.agent = self.project_client.agents.get_agent(AGENT_ID)
            log_message(f"[AZURE-FOUNDRY] ✅ Connected to agent: {self.agent.name}")
            
        except Exception as e:
            log_message(f"[AZURE-FOUNDRY] ❌ Failed to initialize Azure AI Foundry client: {e}")
            raise
    
    def image_to_base64_url(self, image_path: str) -> str:
        """Convert image file to base64 data URL for Azure AI Foundry"""
        try:
            # Verify image exists and is readable
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Open and validate image
            with Image.open(image_path) as img:
                # Optimize image size for API efficiency
                max_size = 1024  # Azure AI Foundry recommended max dimension
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    log_message(f"[AZURE-FOUNDRY] Image resized to {img.size} for API efficiency")
                
                # Convert to RGB if needed (for JPEG compatibility)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save optimized image to bytes
                import io
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
                img_byte_arr = img_byte_arr.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Create data URL
            data_url = f"data:image/jpeg;base64,{img_base64}"
            log_message(f"[AZURE-FOUNDRY] Image converted to base64 data URL ({len(data_url)} chars)")
            
            return data_url
            
        except Exception as e:
            log_message(f"[AZURE-FOUNDRY] ❌ Failed to convert image to base64: {e}")
            raise
    
    def analyze_image(self, image_path: str, message_count: int) -> str:
        """Analyze image using Azure AI Foundry Agent"""
        try:
            log_message(f"[AZURE-FOUNDRY] 🖼️ Analyzing image #{message_count}: {image_path}")
            
            # Convert image to base64 data URL
            image_data_url = self.image_to_base64_url(image_path)
            
            # Create thread for this analysis
            thread = self.project_client.agents.threads.create()
            log_message(f"[AZURE-FOUNDRY] Created thread: {thread.id}")
            
            # Prepare vision analysis prompt
            analysis_prompt = """
            You are a visual quality inspection agent for a production line that packs teabags into boxes. 
            Each image shows the inside of one box containing rows of teabags. 
            Your task is to carefully analyse the image and describe in clear text any visual problems or anomalies you observe in the packing. 
            Focus on detecting teabags that are misplaced, missing, folded incorrectly, not aligned, tangled by their strings, or have detached or misplaced tags. 
            Also identify if a teabag is outside its intended row, overlapping others, or disrupting the uniform pattern. 
            If the box appears perfect, state “No visual defects detected — all teabags are correctly aligned and positioned.”
            For each image, output a short structured analysis in text form that includes:
            A general description of the box (for example: “four rows of teabags, evenly packed”),
            Focus on:
            
            1. **Physical Damage**: Look for dents, tears, holes, or structural damage
            2. **Label Issues**: Check for missing, misaligned, wrinkled, or damaged labels
            3. **Tape Problems**: Examine tape placement, gaps, or adhesion issues
            4. **Corner Integrity**: Assess corner damage, separation, or wear
            5. **Overall Condition**: Evaluate general packaging quality and appearance
            
            Provide a detailed analysis describing:
            - What specific defects you observe (if any)
            - The severity of each issue (minor, moderate, severe)
            - The location of defects on the package
            - Overall quality assessment (pass/fail recommendation)
            
            Be specific and objective in your assessment.
            """
            
            # Create message content with image
            image_url_param = MessageImageUrlParam(url=image_data_url, detail="high")
            content_blocks = [
                MessageInputTextBlock(text=analysis_prompt),
                MessageInputImageUrlBlock(image_url=image_url_param)
            ]
            
            # Send message to agent
            message = self.project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=content_blocks
            )
            log_message(f"[AZURE-FOUNDRY] Created message: {message.id}")
            
            # Create and process run
            log_message("[AZURE-FOUNDRY] Starting agent analysis...")
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=self.agent.id
            )
            
            if run.status == "failed":
                error_msg = f"Agent run failed: {run.last_error}"
                log_message(f"[AZURE-FOUNDRY] ❌ {error_msg}")
                return error_msg
            
            log_message(f"[AZURE-FOUNDRY] Agent run completed with status: {run.status}")
            
            # Retrieve agent response
            messages = self.project_client.agents.messages.list(
                thread_id=thread.id, 
                order=ListSortOrder.ASCENDING
            )
            
            # Extract agent's analysis from the last message
            agent_response = ""
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    agent_response = msg.text_messages[-1].text.value
                    break
            
            if not agent_response:
                agent_response = "No analysis response received from agent"
            
            log_message(f"[AZURE-FOUNDRY] Analysis completed. Response length: {len(agent_response)} chars")
            log_message(f"[AZURE-FOUNDRY] Preview: {agent_response[:150]}{'...' if len(agent_response) > 150 else ''}")
            
            # Clean up thread (optional - helps manage resources)
            try:
                self.project_client.agents.threads.delete(thread.id)
                log_message(f"[AZURE-FOUNDRY] Cleaned up thread: {thread.id}")
            except Exception as cleanup_error:
                log_message(f"[AZURE-FOUNDRY] ⚠ Thread cleanup warning: {cleanup_error}")
            
            return agent_response
            
        except Exception as e:
            log_message(f"[AZURE-FOUNDRY] ❌ Image analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Image analysis failed: {str(e)}"

# Initialize global analyzer instance
log_message("[AZURE-FOUNDRY] Initializing Azure AI Foundry Vision Analyzer...")
try:
    vision_analyzer = AzureFoundryVisionAnalyzer()
    log_message("[AZURE-FOUNDRY] ✅ Vision analyzer ready!")
except Exception as init_error:
    log_message(f"[AZURE-FOUNDRY] ❌ Vision analyzer initialization failed: {init_error}")
    sys.exit(1)

# MQTT Event Handlers
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log_message("[AZURE-FOUNDRY] ✅ Connected to MQTT broker successfully")
        log_message(f"[AZURE-FOUNDRY] 📋 Connection flags: {flags}")
        
        # Subscribe to input topic with QoS 1 for reliability
        result = client.subscribe(MQTT_INPUT_TOPIC, qos=1)
        log_message(f"[AZURE-FOUNDRY] 📡 Subscribed: {MQTT_INPUT_TOPIC} with QoS 1")
        log_message(f"[AZURE-FOUNDRY] 📋 Subscription result: {result}")
        
        # Log readiness status
        log_message("[AZURE-FOUNDRY] 🟢 System ready to receive defect detection messages!")
    else:
        log_message(f"[AZURE-FOUNDRY] ❌ MQTT connection failed with code: {rc}")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    try:
        log_message(f"[AZURE-FOUNDRY] ✅ Subscription confirmed - MID: {mid}, QoS: {granted_qos}")
        log_message("[AZURE-FOUNDRY] 🎉 Now actively listening for CV detection messages!")
    except Exception as e:
        log_message(f"[AZURE-FOUNDRY] ❌ Error in subscribe callback: {e}")

def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    try:
        if rc != 0:
            log_message(f"[AZURE-FOUNDRY] ⚠ Unexpected MQTT disconnection: {rc}")
            log_message(f"[AZURE-FOUNDRY] 🔄 Client will attempt to reconnect...")
        else:
            log_message(f"[AZURE-FOUNDRY] 📡 MQTT disconnected normally")
    except Exception as e:
        log_message(f"[AZURE-FOUNDRY] ❌ Error in disconnect callback: {e}")

def on_publish(client, userdata, mid, properties=None, reasonCode=None):
    try:
        log_message(f"[AZURE-FOUNDRY] 📨 Message {mid} published to broker")
    except Exception as e:
        log_message(f"[AZURE-FOUNDRY] ❌ Error in publish callback: {e}")

# Global message counter for debugging
message_count = 0

def on_message(client, userdata, msg):
    global message_count
    message_count += 1
    
    log_message(f"[AZURE-FOUNDRY] 📥 Received message #{message_count} on topic: {msg.topic}")
    log_message(f"[AZURE-FOUNDRY] 🔄 Processing with Azure AI Foundry Agent...")
    
    try:
        data = json.loads(msg.payload.decode())
        
        img_path = data.get("image_path")
        if not img_path or not os.path.exists(img_path):
            log_message(f"[AZURE-FOUNDRY] ⚠ Missing or invalid image: {img_path}")
            return

        log_message(f"[AZURE-FOUNDRY] 🖼️ Processing image #{message_count}: {img_path}")
        
        # Analyze image using Azure AI Foundry Agent
        reasoning = vision_analyzer.analyze_image(img_path, message_count)
        
        # Sanitize reasoning for JSON compatibility
        reasoning = reasoning.strip()
        reasoning = reasoning.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        reasoning = reasoning.replace('"', "'").replace('\\', '/')
        
        # Remove control characters and normalize spaces
        import re
        reasoning = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', reasoning)
        reasoning = re.sub(r'\s+', ' ', reasoning).strip()
        
        log_message(f"[AZURE-FOUNDRY] ✅ Azure AI Foundry Analysis: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}")
        
        # Create enriched message
        enriched = {
            **data,
            "reasoning": reasoning,
            "model_used": "azure_foundry_agent",
            "agent_id": AGENT_ID,
            "analyzed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        # Validate JSON before publishing
        try:
            json_message = json.dumps(enriched)
            test_parse = json.loads(json_message)
            log_message(f"[AZURE-FOUNDRY] ✅ JSON validation passed")
        except Exception as json_error:
            log_message(f"[AZURE-FOUNDRY] ❌ JSON validation failed: {json_error}")
            return
        
        # Publish enriched message
        log_message(f"[AZURE-FOUNDRY] 📤 Publishing enriched message...")
        try:
            result = client.publish(MQTT_OUTPUT_TOPIC, json_message, qos=0)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log_message(f"[AZURE-FOUNDRY] ✅ Message sent to broker (ID: {result.mid})")
                log_message(f"[AZURE-FOUNDRY] 🎉 MESSAGE SUCCESSFULLY SENT TO BROKER!")
            else:
                log_message(f"[AZURE-FOUNDRY] ❌ Publish failed with return code: {result.rc}")
                
        except Exception as pub_error:
            log_message(f"[AZURE-FOUNDRY] ❌ Publishing exception: {pub_error}")
        
        log_message(f"[AZURE-FOUNDRY] " + "═" * 80)
        log_message(f"[AZURE-FOUNDRY] ✅ Completed processing message #{message_count}")
        log_message(f"[AZURE-FOUNDRY] 🎯 Ready for next message...")
        
    except Exception as e:
        log_message(f"[AZURE-FOUNDRY] ❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()

def main():
    log_message("[AZURE-FOUNDRY] Starting Azure AI Foundry Vision Reasoner...")
    
    # Create MQTT client with unique ID
    import time
    import random
    client_id = f"azure_foundry_reasoner_{int(time.time())}_{random.randint(1000, 9999)}"
    log_message(f"[AZURE-FOUNDRY] Using client ID: {client_id}")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_message = on_message
    
    # Enable auto-reconnect
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    
    try:
        log_message(f"[AZURE-FOUNDRY] Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 90)
        
        log_message("[AZURE-FOUNDRY] Starting MQTT event loop...")
        log_message("[AZURE-FOUNDRY] 🎯 Ready to process defect detection messages with Azure AI Foundry!")
        
        # Use blocking loop_forever() for proper MQTT message handling
        client.loop_forever()
        
    except KeyboardInterrupt:
        log_message("[AZURE-FOUNDRY] 🛑 Received shutdown signal...")
        client.disconnect()
        log_message("[AZURE-FOUNDRY] 👋 Graceful shutdown complete")
    except Exception as e:
        log_message(f"[AZURE-FOUNDRY] ❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        client.disconnect()

if __name__ == "__main__":
    main()