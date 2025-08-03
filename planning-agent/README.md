# Planning Agent MCP Server

A sophisticated planning agent that integrates with LiteLLM to provide comprehensive task planning using O3 and Gemini 2.5 Pro models.

## Features

### 🎯 **Advanced Planning Capabilities**
- **32,000 token limit** for comprehensive planning
- **Dual model support**: OpenAI O3 (primary) and Google Gemini 2.5 Pro (fallback)
- **Structured planning framework** with 6-section comprehensive plans
- **Complexity analysis** for task assessment

### ⚡ **Production Ready**
- **Retry logic** with exponential backoff (3 attempts)
- **Structured logging** with correlation IDs and JSON output
- **Connection pooling** with HTTP/2 support
- **Graceful error handling** and model fallback

### 🛠️ **Available Tools**

#### `create_plan`
Generates comprehensive implementation plans including:
- Overview & objectives
- Technical analysis
- Step-by-step implementation
- Risk assessment
- Testing & validation strategy
- Deployment considerations

**Parameters:**
- `task_description` (required): Detailed task description
- `context` (optional): Additional context or constraints
- `preferred_model` (optional): "openai-o3" or "google-gemini-2.5-pro"

#### `analyze_complexity`
Quick complexity assessment providing:
- Technical complexity rating (1-10)
- Time estimates
- Required expertise level
- Planning approach recommendations

**Parameters:**
- `task_description` (required): Task to analyze

## Installation

### Prerequisites
- Python 3.8+
- LiteLLM deployment with O3 and Gemini 2.5 Pro configured
- Claude Code

### Setup Steps

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/brandonbryant12/mcp-servers.git
   cd mcp-servers/planning-agent
   
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```
   LITELLM_URL=http://localhost:4000
   LITELLM_MASTER_KEY=your-litellm-api-key
   ```

3. **Add to Claude Code**
   ```bash
   # For global access across all projects
   claude mcp add --scope user planning-agent $(pwd)/venv/bin/python $(pwd)/planning-agent-server.py
   ```

4. **Verify Installation**
   ```bash
   claude mcp list
   ```

## Configuration

### Environment Variables
- `LITELLM_URL`: LiteLLM server URL (default: http://localhost:4000)
- `LITELLM_MASTER_KEY`: API key for LiteLLM authentication

### Model Configuration
The agent is configured to use:
- **Primary**: `openai-o3` - For complex, comprehensive planning
- **Secondary**: `google-gemini-2.5-pro` - Fallback for availability/cost optimization
- **Max Tokens**: 32,000 (suitable for detailed plans)
- **Temperature**: 0.1 (focused, consistent output)

## Usage Examples

### Complex Project Planning
```
create_plan: {
  "task_description": "Build a scalable microservices architecture for an e-commerce platform",
  "context": "Team of 5 developers, 3-month timeline, AWS infrastructure",
  "preferred_model": "openai-o3"
}
```

### Quick Complexity Assessment
```
analyze_complexity: {
  "task_description": "Implement OAuth2 authentication with refresh tokens"
}
```

## Architecture

### Retry Logic
- **3 attempts** with exponential backoff (4-10 seconds)
- **Retries on**: Network errors, timeouts
- **No retry on**: Authentication errors, invalid requests

### Logging
- **Structured JSON logs** with correlation IDs
- **Request tracking**: Model used, token usage, response times
- **Error details**: Full error context with request correlation

### Connection Management
- **Connection pooling**: 10 max connections, 5 keepalive
- **HTTP/2 support** for improved performance
- **5-minute timeout** for O3 model requests

## Troubleshooting

### Common Issues

**Planning Agent Not Available**
```bash
# Check MCP server status
claude mcp list

# Restart if needed
claude mcp remove planning-agent
claude mcp add --scope user planning-agent $(pwd)/venv/bin/python $(pwd)/planning-agent-server.py
```

**Model Failures**
- Check LiteLLM server status and API key configuration
- Verify model availability in your LiteLLM deployment
- Review logs for specific error details

**Performance Issues**
- Monitor token usage - large requests may take 30+ seconds
- Consider using Gemini 2.5 Pro for faster responses
- Check network connectivity to LiteLLM server

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export STRUCTLOG_LEVEL=DEBUG
```

## Development

### Quick Wins Implemented
✅ **Retry Logic** - Exponential backoff with tenacity  
✅ **Structured Logging** - JSON logs with correlation IDs  
✅ **Connection Pooling** - HTTP/2 with optimized limits  

### Future Enhancements
- Circuit breaker pattern for model failures
- Response caching for similar requests
- Planning templates for common scenarios
- Metrics collection and monitoring

## License

MIT License - Feel free to use and modify for your needs.