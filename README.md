# MCP Servers Collection

A collection of MCP (Model Context Protocol) servers for Claude Code integration.

## Available Servers

### 🧠 Planning Agent

A comprehensive planning agent that leverages O3 and Gemini 2.5 Pro models for complex task planning and analysis.

**Features:**
- **32k max tokens** for comprehensive planning
- **Model fallback**: O3 (primary) → Gemini 2.5 Pro (secondary)
- **Production ready**: Retry logic, structured logging, connection pooling
- **Global access**: User-scoped MCP server configuration

**Tools:**
- `create_plan` - Generate comprehensive implementation plans
- `analyze_complexity` - Quick complexity assessment and recommendations

**Installation:**
```bash
# 1. Clone repository
git clone https://github.com/brandonbryant12/mcp-servers.git
cd mcp-servers/planning-agent

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your LiteLLM configuration

# 4. Add to Claude Code (user-scoped for global access)
claude mcp add --scope user planning-agent $(pwd)/venv/bin/python $(pwd)/planning-agent-server.py
```

**Requirements:**
- Python 3.8+
- LiteLLM deployment with O3 and Gemini 2.5 Pro access
- Claude Code

**Usage:**
Once configured, the planning agent is available globally across all Claude Code sessions:

```
analyze_complexity: {"task_description": "Build a React todo app with Node.js backend"}
create_plan: {"task_description": "Implement user authentication system", "preferred_model": "openai-o3"}
```

## Contributing

Feel free to contribute additional MCP servers or improvements to existing ones.

## License

MIT License - see individual server directories for specific licensing information.