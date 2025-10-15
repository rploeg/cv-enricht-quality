# Azure AI Foundry Vision Reasoner

This implementation uses Azure AI Foundry's Agent Service to analyze packaging defects. Unlike the local SLM version, this leverages cloud-based AI agents for more sophisticated analysis.


Start the following scripts on a virtual environment:
publish mqtt messages: .\.venv\Scripts\python.exe cv_publisher.py
mqtt listener:  .\.venv\Scripts\python.exe .\mqtt_listener.py
agent service reasoner: .\.venv\Scripts\python.exe azure_foundry_reasoner.py

If you want to test only the agent service with only images use this one (without mqtt): .\.venv\Scripts\python.exe test_azure_foundry.py

## Features

- **Azure AI Foundry Integration**: Uses Azure AI Foundry Agent Service for vision analysis
- **Secure Authentication**: Leverages Azure Entra ID with DefaultAzureCredential 
- **High-Quality Analysis**: Employs advanced vision models via Azure AI Foundry
- **Image Upload**: Automatically uploads images to Azure AI Foundry for analysis
- **MQTT Integration**: Seamlessly integrates with existing CV detection pipeline
- **Error Handling**: Comprehensive error handling and logging
- **Resource Management**: Automatic cleanup of Azure resources

## Prerequisites

1. **Azure AI Foundry Project**: Set up an Azure AI Foundry project
2. **Vision Agent**: Create and configure a vision-capable agent in Azure AI Foundry
3. **Authentication**: Configure Azure Entra ID authentication
4. **Python Environment**: Python 3.8+ with required packages
5. **Local Mosquittto**: install a local mosquitto without authentication

## Quick Setup

### 1. Install Dependencies

```bash
python -m venv .venv
```

```bash
.\.venv\Scripts\python.exe -m pip install -r requirements-azure-foundry.txt
```

### 2. Configure Environment

Copy the template and update with your values:

```bash
cp .env.template .env
```

Edit `.env` with your MQTT details:

```bash
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_INPUT_TOPIC=factory/line1/defects
MQTT_OUTPUT_TOPIC=factory/line1/defects/enriched
```

Adjust in 'azure_foundry_reasoner.py' the following endpoint and agent:

```bash
# Azure AI Foundry Configuration
AZURE_PROJECT_ENDPOINT=https://your-foundry-resource-name.services.ai.azure.com/api/projects/your-project-name
AGENT_ID=asst_your_agent_id_here
```


### 3. Azure Authentication Setup

#### Option A: Managed Identity (Recommended for Azure-hosted)
If running on Azure (VM, Container, Function), managed identity is automatically used.

#### Option B: Azure CLI (Development)
```bash
az login
```

#### Option C: Service Principal (Production)
Set environment variables:
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret  
AZURE_TENANT_ID=your-tenant-id
```

### 4. Create Azure AI Foundry Agent

1. Go to [Azure AI Foundry portal](https://ai.azure.com)
2. Create a new project or use existing
3. Navigate to **Agents** section
4. Create a new agent with:
   - **Model**: Choose a vision-capable model (e.g., GPT-4o, GPT-4.1)
   - **Instructions**: Configure for packaging defect analysis
   - **Tools**: Enable vision analysis capabilities
5. Copy the Agent ID for your configuration

### 5. Run the Application

```bash
python azure_foundry_reasoner.py
```

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint | - | ✅ |
| `AGENT_ID` | Azure AI Foundry agent identifier | - | ✅ |
| `MQTT_BROKER` | MQTT broker hostname | localhost | ❌ |
| `MQTT_PORT` | MQTT broker port | 1883 | ❌ |
| `MQTT_INPUT_TOPIC` | Topic for receiving CV messages | factory/line1/defects | ❌ |
| `MQTT_OUTPUT_TOPIC` | Topic for publishing enriched results | factory/line1/defects/enriched | ❌ |

### Azure Authentication Variables (Optional)

| Variable | Description | When to Use |
|----------|-------------|-------------|
| `AZURE_CLIENT_ID` | Service principal client ID | Production deployments |
| `AZURE_CLIENT_SECRET` | Service principal secret | Production deployments |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Service principal auth |

## Agent Configuration

### Recommended Agent Instructions

```
You are a visual quality inspection agent for a production line that packs teabags into boxes. Each image shows the inside of one box containing rows of teabags. Your task is to carefully analyse the image and describe in clear text any visual problems or anomalies you observe in the packing. Focus on detecting teabags that are misplaced, missing, folded incorrectly, not aligned, tangled by their strings, or have detached or misplaced tags. Also identify if a teabag is outside its intended row, overlapping others, or disrupting the uniform pattern. If the box appears perfect, state “No visual defects detected — all teabags are correctly aligned and positioned.”

For each image, output a short structured analysis in text form that includes:

A general description of the box (for example: “four rows of teabags, evenly packed”),

The specific problems you detect (for example: “one teabag in the top left corner is tilted and its string is loose”), and

A final conclusion: “Pass” or “Fail”.

Be precise, objective, and consistent in describing the type and location of each defect.
```

### Supported Vision Models

- **GPT-4o**: Advanced multimodal capabilities
- **GPT-4.1**: Enhanced vision analysis
- **GPT-4 Vision**: Reliable vision processing
- **Custom Models**: Any vision-enabled model in Azure AI Foundry

## Message Flow

```
CV Detection → MQTT Input → Azure AI Foundry Agent → Analysis → MQTT Output
```

### Input Message Format

```json
{
  "timestamp": "2025-01-14T10:30:45.123Z",
  "image_path": "/path/to/detected/image.jpg",
  "detector": "cv_publisher",
  "confidence": 0.95
}
```

### Output Message Format

```json
{
  "timestamp": "2025-01-14T10:30:45.123Z",
  "image_path": "/path/to/detected/image.jpg",
  "detector": "cv_publisher", 
  "confidence": 0.95,
  "reasoning": "Analysis shows minor corner damage on the upper-left corner...",
  "model_used": "azure_foundry_agent",
  "agent_id": "asst_abc123",
  "analyzed_at": "2025-01-14T10:30:47.456Z"
}
```

## Best Practices

### Security
- **Use Managed Identity** when possible for authentication
- **Rotate credentials** regularly for service principal authentication
- **Limit permissions** to minimum required (Azure AI Developer role)
- **Store secrets** in Azure Key Vault for production

### Performance
- **Image Optimization**: Images are automatically resized to 1024px max dimension
- **Efficient Encoding**: Uses optimized JPEG encoding for faster uploads
- **Resource Cleanup**: Automatically cleans up Azure threads after analysis
- **Connection Reuse**: Maintains persistent MQTT connections

### Monitoring
- **Comprehensive Logging**: Detailed logs for troubleshooting
- **Error Tracking**: Captures and logs all errors with stack traces
- **Message Tracking**: Assigns unique IDs to each processed message
- **Performance Metrics**: Tracks analysis timing and success rates

## Troubleshooting

### Common Issues

#### Authentication Errors
```
DefaultAzureCredential failed to retrieve a token
```
**Solution**: Ensure you're logged in via `az login` or have proper service principal credentials.

#### Agent Not Found
```
Agent with ID 'asst_xyz' not found
```
**Solution**: Verify the `AGENT_ID` in your configuration matches your Azure AI Foundry agent.

#### Image Upload Failures
```
Failed to convert image to base64
```
**Solution**: Check image file exists and is a valid format (JPEG, PNG, etc.).

#### MQTT Connection Issues
```
MQTT connection failed with code: 5
```
**Solution**: Verify MQTT broker is running and accessible.