#!/usr/bin/env python3
"""
Planning Agent MCP Server
Global planning agent with O3 and Gemini 2.5 Pro integration
"""

import asyncio
import json
import os
from typing import Any, Sequence
import httpx
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.types as types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("planning_agent")

# Configuration
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-1234567890abcdef")

# Model configuration with fallback priority
MODEL_CONFIG = {
    "primary": "openai-o3",
    "secondary": "google-gemini-2.5-pro", 
    "max_tokens": 32000,
    "temperature": 0.1  # Lower temperature for more focused planning
}

class PlanningAgent:
    def __init__(self):
        # Enhanced connection pooling
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        self.client = httpx.AsyncClient(
            timeout=300.0,  # 5min timeout for O3
            limits=limits,
            http2=True  # Enable HTTP/2 for better performance
        )
        self.logger = logger.bind(component="planning_agent")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def plan_with_model(self, prompt: str, model: str) -> dict:
        """Execute planning request with specified model with retry logic"""
        request_id = id(prompt)  # Simple correlation ID
        log = self.logger.bind(request_id=request_id, model=model)
        
        log.info("Starting planning request", prompt_length=len(prompt))
        
        try:
            response = await self.client.post(
                f"{LITELLM_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert planning agent. Provide detailed, actionable plans with clear steps, dependencies, and considerations."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": MODEL_CONFIG["max_tokens"],
                    "temperature": MODEL_CONFIG["temperature"]
                }
            )
            response.raise_for_status()
            result_data = response.json()
            usage = result_data.get("usage", {})
            
            log.info(
                "Planning request completed successfully",
                response_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0)
            )
            
            return {
                "success": True,
                "model": model,
                "content": result_data["choices"][0]["message"]["content"],
                "usage": usage
            }
        except httpx.RequestError as e:
            log.error("Network error during planning request", error=str(e))
            raise  # Let tenacity handle the retry
        except httpx.TimeoutException as e:
            log.error("Timeout during planning request", error=str(e)) 
            raise  # Let tenacity handle the retry
        except Exception as e:
            log.error("Unexpected error during planning request", error=str(e))
            return {
                "success": False,
                "model": model,
                "error": str(e)
            }

    async def create_plan(self, prompt: str, preferred_model: str = None) -> dict:
        """Create comprehensive plan with model fallback"""
        log = self.logger.bind(preferred_model=preferred_model)
        
        models_to_try = []
        
        if preferred_model:
            models_to_try.append(preferred_model)
        
        # Add default priority order
        for model in [MODEL_CONFIG["primary"], MODEL_CONFIG["secondary"]]:
            if model not in models_to_try:
                models_to_try.append(model)
        
        log.info("Starting planning with model fallback", models=models_to_try)
        
        last_error = None
        for i, model in enumerate(models_to_try):
            try:
                result = await self.plan_with_model(prompt, model)
                if result["success"]:
                    log.info("Planning completed successfully", successful_model=model, attempt=i+1)
                    return result
                last_error = result["error"]
                log.warning("Model failed, trying next", failed_model=model, error=last_error)
            except Exception as e:
                last_error = str(e)
                log.error("Model attempt failed with exception", failed_model=model, error=last_error)
                
        log.error("All models failed", final_error=last_error)
        return {
            "success": False,
            "error": f"All models failed. Last error: {last_error}"
        }

server = Server("planning-agent")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available planning tools"""
    return [
        Tool(
            name="create_plan",
            description="Create a comprehensive plan for complex tasks using O3 or Gemini 2.5 Pro",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Detailed description of the task or project to plan"
                    },
                    "context": {
                        "type": "string", 
                        "description": "Additional context, constraints, or requirements",
                        "default": ""
                    },
                    "preferred_model": {
                        "type": "string",
                        "enum": ["openai-o3", "google-gemini-2.5-pro"],
                        "description": "Preferred model for planning (defaults to O3)",
                        "default": "openai-o3"
                    }
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="analyze_complexity",
            description="Analyze task complexity and recommend planning approach",
            inputSchema={
                "type": "object", 
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Task to analyze for complexity"
                    }
                },
                "required": ["task_description"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    
    if name == "create_plan":
        task_description = arguments["task_description"]
        context = arguments.get("context", "")
        preferred_model = arguments.get("preferred_model", MODEL_CONFIG["primary"])
        
        # Enhanced planning prompt
        planning_prompt = f"""
Task: {task_description}

Context: {context}

Please create a comprehensive implementation plan that includes:

1. **Overview & Objectives**
   - Clear problem statement
   - Success criteria
   - Key deliverables

2. **Technical Analysis**
   - Architecture considerations
   - Technology stack decisions
   - Dependencies and prerequisites

3. **Implementation Steps**
   - Detailed step-by-step breakdown
   - Estimated effort for each step
   - Dependencies between steps

4. **Risk Assessment**
   - Potential challenges
   - Mitigation strategies
   - Alternative approaches

5. **Testing & Validation**
   - Testing strategy
   - Quality assurance checkpoints
   - Success metrics

6. **Deployment & Maintenance**
   - Rollout plan
   - Monitoring considerations
   - Long-term maintenance

Please be specific and actionable in your recommendations.
        """.strip()
        
        async with PlanningAgent() as agent:
            result = await agent.create_plan(planning_prompt, preferred_model)
            
            if result["success"]:
                response = f"""# Planning Result

**Model Used:** {result['model']}
**Usage:** {result.get('usage', {})}

---

{result['content']}
"""
            else:
                response = f"❌ Planning failed: {result['error']}"
            
        return [types.TextContent(type="text", text=response)]
    
    elif name == "analyze_complexity":
        task_description = arguments["task_description"]
        
        complexity_prompt = f"""
Analyze the complexity of this task and provide recommendations:

Task: {task_description}

Please assess:
1. Technical complexity (1-10 scale)
2. Time estimate
3. Required expertise level
4. Recommended planning approach
5. Whether this needs heavy planning with O3 or can be handled with lighter planning

Be concise but thorough in your analysis.
        """.strip()
        
        async with PlanningAgent() as agent:
            # Use Gemini for quick complexity analysis
            result = await agent.plan_with_model(complexity_prompt, "google-gemini-2.5-pro")
            
            if result["success"]:
                response = f"""# Complexity Analysis

**Analyzed by:** {result['model']}

{result['content']}

---
**Recommendation:** {"Use O3 for detailed planning" if "complex" in result['content'].lower() or "difficult" in result['content'].lower() else "Standard planning sufficient"}
"""
            else:
                response = f"❌ Analysis failed: {result['error']}"
                
        return [types.TextContent(type="text", text=response)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # For stdio transport
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())