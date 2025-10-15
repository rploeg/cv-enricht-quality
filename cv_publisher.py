#!/usr/bin/env python3
import os, json, time, glob, random, signal, sys
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# ANSI color codes for beautiful terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

def get_timestamp():
    """Generate timestamp for logging"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def print_header():
    """Print a beautiful header for the CV Publisher"""
    print(f"\n{Colors.BRIGHT_CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}{Colors.BOLD}{Colors.BRIGHT_WHITE}{'CV DEFECT PUBLISHER':^78}{Colors.RESET}{Colors.BRIGHT_CYAN}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}{Colors.DIM}{'Factory Line 1 - Automated Defect Detection System':^78}{Colors.RESET}{Colors.BRIGHT_CYAN}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'=' * 80}{Colors.RESET}")

def print_message_box(title, content, color=Colors.BRIGHT_WHITE):
    """Print a bordered message box"""
    max_width = 76
    lines = content.split('\n') if isinstance(content, str) else [str(content)]
    
    print(f"{Colors.BRIGHT_BLUE}┌─{title}─{'─' * (max_width - len(title) - 2)}┐{Colors.RESET}")
    
    for line in lines:
        if len(line) > max_width:
            # Split long lines
            while len(line) > max_width:
                print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET} {color}{line[:max_width-1]}{Colors.RESET} {Colors.BRIGHT_BLUE}│{Colors.RESET}")
                line = line[max_width-1:]
            if line:
                print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET} {color}{line:<{max_width-1}}{Colors.RESET} {Colors.BRIGHT_BLUE}│{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_BLUE}│{Colors.RESET} {color}{line:<{max_width-1}}{Colors.RESET} {Colors.BRIGHT_BLUE}│{Colors.RESET}")
    
    print(f"{Colors.BRIGHT_BLUE}└{'─' * max_width}┘{Colors.RESET}")

def get_confidence_color(confidence):
    """Return color based on confidence level"""
    if confidence >= 0.8:
        return Colors.BRIGHT_RED
    elif confidence >= 0.7:
        return Colors.BRIGHT_YELLOW
    else:
        return Colors.BRIGHT_GREEN

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n\n{Colors.BRIGHT_YELLOW}[{get_timestamp()}] 🛑 Received shutdown signal...{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}[{get_timestamp()}] 👋 CV Publisher stopped gracefully{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{'=' * 80}{Colors.RESET}\n")
    sys.exit(0)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/line1/defects")
IMG_DIR = os.getenv("IMG_DIR", "./data/images")

def main():
    # Set up graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print beautiful header
    print_header()
    
    print(f"{Colors.BRIGHT_GREEN}[{get_timestamp()}] 🔗 Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}{Colors.RESET}")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"{Colors.BRIGHT_GREEN}[{get_timestamp()}] ✅ Connected to MQTT broker successfully{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}[{get_timestamp()}] ❌ Failed to connect to MQTT broker: {e}{Colors.RESET}")
        return

    # Look for both jpg and png images
    jpg_images = glob.glob(os.path.join(IMG_DIR, "*.jpg"))
    png_images = glob.glob(os.path.join(IMG_DIR, "*.png"))
    images = sorted(jpg_images + png_images)
    
    if not images:
        print(f"{Colors.BRIGHT_RED}[{get_timestamp()}] ❌ No images found in {IMG_DIR}. Generate some first.{Colors.RESET}")
        return

    print(f"{Colors.BRIGHT_CYAN}[{get_timestamp()}] 📁 Found {len(images)} images in {IMG_DIR}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}[{get_timestamp()}] ⏰ Publishing one image every 60 seconds to topic: {MQTT_TOPIC}{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}[{get_timestamp()}] 🎯 Press Ctrl+C to stop gracefully{Colors.RESET}")
    print()
    
    i = 0
    message_count = 0
    
    try:
        while True:
            message_count += 1
            img = images[i % len(images)]
            confidence = round(random.uniform(0.55, 0.95), 2)
            defect = "unknown"  # CV could fill its own classification; we leave it generic
            
            # Create timestamp
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            msg = {
                "image_path": img,
                "defect_type": defect,
                "confidence": confidence,
                "timestamp": timestamp,
                "line_id": "line1"
            }
            
            # Get image filename for display
            img_filename = os.path.basename(img)
            confidence_color = get_confidence_color(confidence)
            
            # Publish message
            try:
                client.publish(MQTT_TOPIC, json.dumps(msg))
                
                # Create beautiful message display
                title = f"📤 PUBLISHED MESSAGE #{message_count}"
                content = f"""🖼️  Image: {img_filename}
🎯  Defect Type: {defect}
📊  Confidence: {confidence}
🕐  Timestamp: {timestamp}
🏭  Line ID: line1
📡  Topic: {MQTT_TOPIC}"""
                
                print_message_box(title, content, Colors.BRIGHT_WHITE)
                
                # Show status
                print(f"{Colors.BRIGHT_GREEN}[{get_timestamp()}] ✅ Message published successfully{Colors.RESET}")
                print(f"{Colors.DIM}[{get_timestamp()}] ⏳ Waiting 60 seconds for next message...{Colors.RESET}")
                print()
                
            except Exception as e:
                print(f"{Colors.BRIGHT_RED}[{get_timestamp()}] ❌ Failed to publish message: {e}{Colors.RESET}")
            
            i += 1
            time.sleep(60)
            
    except KeyboardInterrupt:
        # This will be handled by signal_handler
        pass
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}[{get_timestamp()}] ❌ Unexpected error: {e}{Colors.RESET}")
    finally:
        try:
            client.disconnect()
            print(f"{Colors.BRIGHT_GREEN}[{get_timestamp()}] 📡 Disconnected from MQTT broker{Colors.RESET}")
        except:
            pass

if __name__ == "__main__":
    main()
