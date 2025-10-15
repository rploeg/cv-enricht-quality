import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Enhanced ANSI color codes and styles
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    BG_PURPLE = '\033[105m'
    BG_CYAN = '\033[106m'
    
    # Custom combinations
    SUCCESS = '\033[1;92m'  # Bold Green
    ERROR = '\033[1;91m'    # Bold Red
    WARNING = '\033[1;93m'  # Bold Yellow
    INFO = '\033[1;96m'     # Bold Cyan
    DEBUG = '\033[2;95m'    # Dim Purple

# Icons for different message types
class Icons:
    CONNECT = '🔗'
    SUBSCRIBE = '📡'
    ORIGINAL = '📦'
    ENRICHED = '🤖'
    ERROR = '❌'
    SUCCESS = '✅'
    DEBUG = '🔍'
    TIME = '⏰'
    AI = '🧠'
    ANALYSIS = '🔬'
    CONFIDENCE = '📊'
    SEPARATOR = '━'

def print_header():
    header = f"""
{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}          🏭 SMART FACTORY MQTT LISTENER 🏭{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}     Real-time CV Detection + AI Analysis Pipeline{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.RESET}
"""
    print(header)

def on_connect(client, userdata, flags, rc, properties=None):
    print(f'\n{Icons.CONNECT} {Colors.SUCCESS}Connected to MQTT Broker{Colors.RESET}')
    print(f'   {Colors.DIM}Connection result: {rc} (0 = success){Colors.RESET}')
    
    print(f'\n{Icons.SUBSCRIBE} {Colors.INFO}Setting up subscriptions...{Colors.RESET}')
    
    # Subscribe to original defect detection
    print(f'   {Colors.YELLOW}📍 Subscribing to: factory/line1/defects{Colors.RESET}')
    result1 = client.subscribe('factory/line1/defects')
    print(f'   {Colors.DIM}   Result: {result1}{Colors.RESET}')
    
    # Subscribe to AI-enriched analysis
    print(f'   {Colors.CYAN}🎯 Subscribing to: factory/line1/defects/enriched{Colors.RESET}')
    result2 = client.subscribe('factory/line1/defects/enriched')
    print(f'   {Colors.DIM}   Result: {result2}{Colors.RESET}')
    
    print(f'\n{Colors.SUCCESS}🎉 Ready to monitor factory line messages!{Colors.RESET}')
    print(f'{Colors.DIM}{Icons.SEPARATOR * 80}{Colors.RESET}')

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print(f'{Icons.SUCCESS} {Colors.SUCCESS}Subscription confirmed{Colors.RESET} - MID: {mid}, QoS: {granted_qos}')

def on_message(client, userdata, msg):
    topic = msg.topic
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    try:
        payload = json.loads(msg.payload.decode())
        image_path = payload.get('image_path', 'unknown')
        filename = image_path.split('\\')[-1] if '\\' in image_path else image_path.split('/')[-1]
        
        if topic == 'factory/line1/defects/enriched':
            # 🤖 AI-Enhanced Analysis Message
            reasoning = payload.get('reasoning', 'no reasoning')
            model_used = payload.get('model_used', 'unknown')
            analyzed_at = payload.get('analyzed_at', 'unknown')
            
            print(f'\n{Colors.BOLD}{Colors.CYAN}┌{Icons.SEPARATOR * 78}┐{Colors.RESET}')
            print(f'{Colors.BOLD}{Colors.CYAN}│ {Icons.ENRICHED} AI ANALYSIS COMPLETE {Icons.AI}                                          │{Colors.RESET}')
            print(f'{Colors.BOLD}{Colors.CYAN}├{Icons.SEPARATOR * 78}┤{Colors.RESET}')
            
            # Calculate proper spacing for each line
            time_line = f"│ {Icons.TIME} Time: {Colors.WHITE}{timestamp}{Colors.CYAN}"
            time_padding = 78 - len(f"│ ⏰ Time: {timestamp}") + 1
            print(f'{Colors.CYAN}{time_line}{" " * time_padding}│{Colors.RESET}')
            
            file_line = f"│ 📁 File: {Colors.WHITE}{filename}{Colors.CYAN}"
            file_padding = 78 - len(f"│ 📁 File: {filename}") + 1
            print(f'{Colors.CYAN}{file_line}{" " * file_padding}│{Colors.RESET}')
            
            model_line = f"│ 🔧 Model: {Colors.WHITE}{model_used.upper()}{Colors.CYAN}"
            model_padding = 78 - len(f"│ 🔧 Model: {model_used.upper()}") + 1
            print(f'{Colors.CYAN}{model_line}{" " * model_padding}│{Colors.RESET}')
            
            print(f'{Colors.CYAN}├{Icons.SEPARATOR * 78}┤{Colors.RESET}')
            print(f'{Colors.CYAN}│ {Icons.ANALYSIS} ANALYSIS:{Colors.RESET}{" " * (78 - len("│ 🔬 ANALYSIS:"))}│{Colors.RESET}')
            
            # Word wrap the reasoning text
            words = reasoning.split()
            lines = []
            current_line = ""
            max_width = 70
            
            for word in words:
                if len(current_line + " " + word) <= max_width:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                line_content = f"│ {line}"
                line_padding = 78 - len(line_content) + 1
                print(f'{Colors.CYAN}{line_content}{Colors.WHITE}{" " * line_padding}{Colors.CYAN}│{Colors.RESET}')
            
            print(f'{Colors.BOLD}{Colors.CYAN}└{Icons.SEPARATOR * 78}┘{Colors.RESET}')
            
        else:
            # 📦 Original CV Detection Message
            defect_type = payload.get('defect_type', 'unknown')
            confidence = payload.get('confidence', 0)
            
            # Color code confidence levels
            if confidence >= 0.8:
                conf_color = Colors.SUCCESS
                conf_icon = '🟢'
            elif confidence >= 0.6:
                conf_color = Colors.WARNING
                conf_icon = '🟡'
            else:
                conf_color = Colors.ERROR
                conf_icon = '🔴'
            
            print(f'\n{Colors.WHITE}┌{Icons.SEPARATOR * 60}┐{Colors.RESET}')
            print(f'{Colors.WHITE}│ {Icons.ORIGINAL} CV DETECTION {Icons.DEBUG}                                    │{Colors.RESET}')
            print(f'{Colors.WHITE}├{Icons.SEPARATOR * 60}┤{Colors.RESET}')
            
            # Calculate proper spacing for CV detection
            time_file_line = f"│ {Icons.TIME} {timestamp} │ 📁 {filename}"
            time_file_padding = 60 - len(f"│ ⏰ {timestamp} │ 📁 {filename}") + 1
            print(f'{Colors.WHITE}{time_file_line}{" " * time_file_padding}│{Colors.RESET}')
            
            type_line = f"│ 🏷️  Type: {defect_type}"
            type_padding = 60 - len(type_line) + 1
            print(f'{Colors.WHITE}{type_line}{" " * type_padding}│{Colors.RESET}')
            
            conf_line = f"│ {conf_icon} Confidence: {conf_color}{confidence:.2f}{Colors.WHITE}"
            conf_padding = 60 - len(f"│ {conf_icon} Confidence: {confidence:.2f}") + 1
            print(f'{Colors.WHITE}{conf_line}{" " * conf_padding}│{Colors.RESET}')
            
            print(f'{Colors.WHITE}└{Icons.SEPARATOR * 60}┘{Colors.RESET}')
            
    except Exception as e:
        print(f'\n{Icons.ERROR} {Colors.ERROR}ERROR PROCESSING MESSAGE{Colors.RESET}')
        print(f'{Colors.ERROR}├─ Time: {timestamp}{Colors.RESET}')
        print(f'{Colors.ERROR}├─ Topic: {topic}{Colors.RESET}')
        print(f'{Colors.ERROR}├─ Error: {str(e)}{Colors.RESET}')
        print(f'{Colors.ERROR}└─ Raw: {msg.payload.decode()[:100]}...{Colors.RESET}')

def main():
    print_header()
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="smart_factory_monitor", clean_session=True)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    
    try:
        print(f'{Icons.CONNECT} {Colors.INFO}Connecting to MQTT broker...{Colors.RESET}')
        client.connect('localhost', 1883, 60)
        print(f'{Icons.SUCCESS} {Colors.SUCCESS}Starting message loop...{Colors.RESET}')
        print(f'{Colors.DIM}💡 Press Ctrl+C to stop monitoring{Colors.RESET}\n')
        client.loop_forever()
    except KeyboardInterrupt:
        print(f'\n\n{Icons.SUCCESS} {Colors.WARNING}🛑 Received shutdown signal (Ctrl+C){Colors.RESET}')
        print(f'{Colors.INFO}📡 Disconnecting from MQTT broker...{Colors.RESET}')
        try:
            client.disconnect()
            print(f'{Icons.SUCCESS} {Colors.SUCCESS}✅ Disconnected successfully{Colors.RESET}')
        except Exception as disconnect_error:
            print(f'{Icons.ERROR} {Colors.ERROR}⚠ Disconnect error: {disconnect_error}{Colors.RESET}')
        
        print(f'{Colors.SUCCESS}👋 Smart Factory Monitor shutdown complete!{Colors.RESET}')
        print(f'{Colors.DIM}{"═" * 60}{Colors.RESET}')
    except Exception as e:
        print(f'\n{Icons.ERROR} {Colors.ERROR}❌ Connection failed: {e}{Colors.RESET}')
        print(f'{Colors.ERROR}Please check if MQTT broker is running on localhost:1883{Colors.RESET}')

if __name__ == "__main__":
    main()