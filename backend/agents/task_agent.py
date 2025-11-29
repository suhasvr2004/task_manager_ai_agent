from langchain.agents import AgentExecutor, create_openai_tools_agent, create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.config import get_settings
from backend.agents.tools.task_crud_tool import (
    create_task, get_task, list_tasks, update_task, delete_task, search_tasks
)
from backend.agents.tools.reminder_tool import create_reminder, list_reminders
from loguru import logger

# Fix for httpx 0.28.0+ compatibility with OpenAI client
# httpx removed 'proxies' parameter, but OpenAI client still tries to pass it
try:
    import openai
    from openai._base_client import SyncHttpxClientWrapper, AsyncHttpxClientWrapper
    import httpx
    
    # Patch the SyncHttpxClientWrapper to remove 'proxies' before passing to httpx.Client
    original_sync_init = SyncHttpxClientWrapper.__init__
    
    def patched_sync_init(self, *args, **kwargs):
        # Remove 'proxies' if present (httpx 0.28+ doesn't support it)
        kwargs.pop("proxies", None)
        return original_sync_init(self, *args, **kwargs)
    
    SyncHttpxClientWrapper.__init__ = patched_sync_init
    
    # Patch the AsyncHttpxClientWrapper as well
    original_async_init = AsyncHttpxClientWrapper.__init__
    
    def patched_async_init(self, *args, **kwargs):
        # Remove 'proxies' if present (httpx 0.28+ doesn't support it)
        kwargs.pop("proxies", None)
        return original_async_init(self, *args, **kwargs)
    
    AsyncHttpxClientWrapper.__init__ = patched_async_init
    logger.info("Applied httpx compatibility patch for OpenAI client (sync and async)")
except Exception as e:
    logger.warning(f"Could not apply httpx compatibility patch: {e}")

class TaskManagerAgent:
    """Main AI Agent for task management with multi-provider support"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tools = self._setup_tools()
        # Initialize LLM with fallback support (Gemini -> OpenAI -> Claude)
        self.llm = self._initialize_llm_with_fallback()
        self.agent_executor = self._setup_agent()
    
    def _initialize_llm_with_fallback(self) -> BaseChatModel:
        """
        Initialize LLM with fallback support:
        1. Try Google Gemini (primary)
        2. Fallback to OpenAI
        3. Fallback to Anthropic Claude
        """
        provider = self.settings.LLM_PROVIDER.lower()
        llm_kwargs = {
            "temperature": self.settings.LLM_TEMPERATURE,
        }
        
        # Try Gemini first (primary)
        if provider == "gemini" or not provider:
            if self.settings.GOOGLE_GEMINI_API_KEY:
                try:
                    # Use appropriate Gemini model - try available model names
                    model = self.settings.LLM_MODEL if "gemini" in self.settings.LLM_MODEL.lower() else "gemini-2.5-flash"
                    
                    # Try different model names if the first one fails (in order of preference)
                    model_names_to_try = [
                        model,  # User's preferred model
                        "gemini-2.5-flash",  # Latest stable flash (fast and efficient)
                        "gemini-2.0-flash",  # Stable flash version
                        "gemini-flash-latest",  # Always points to latest flash
                        "gemini-2.5-pro",  # Latest pro version
                        "gemini-pro-latest",  # Always points to latest pro
                        "gemini-2.0-flash-001",  # Specific version
                    ]
                    
                    last_error = None
                    for model_name in model_names_to_try:
                        try:
                            llm = ChatGoogleGenerativeAI(
                                model=model_name,
                                google_api_key=self.settings.GOOGLE_GEMINI_API_KEY,
                                temperature=self.settings.LLM_TEMPERATURE
                            )
                            logger.info(f"✅ Google Gemini initialized with model: {model_name}")
                            return llm
                        except Exception as e:
                            last_error = e
                            logger.debug(f"Failed to initialize with {model_name}: {str(e)}")
                            continue
                    
                    # If all models failed, raise the last error
                    raise last_error
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini: {str(e)}. Trying fallback...")
            else:
                logger.warning("Gemini API key not found. Trying fallback...")
        
        # Fallback to OpenAI
        if provider == "openai" or not self.settings.GOOGLE_GEMINI_API_KEY:
            if self.settings.OPENAI_API_KEY:
                try:
                    model = self.settings.LLM_MODEL if "gpt" in self.settings.LLM_MODEL.lower() else "gpt-4o-mini"
                    llm_kwargs = {
                        "model": model,
                        "temperature": self.settings.LLM_TEMPERATURE,
                        "openai_api_key": self.settings.OPENAI_API_KEY
                    }
                    llm = ChatOpenAI(**llm_kwargs)
                    logger.info(f"✅ OpenAI initialized with model: {model} (fallback)")
                    return llm
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI: {str(e)}. Trying Claude...")
            else:
                logger.warning("OpenAI API key not found. Trying Claude...")
        
        # Fallback to Claude
        if provider == "anthropic" or not self.settings.OPENAI_API_KEY:
            if self.settings.ANTHROPIC_API_KEY:
                try:
                    model = self.settings.LLM_MODEL if "claude" in self.settings.LLM_MODEL.lower() else "claude-3-5-sonnet-20241022"
                    llm = ChatAnthropic(
                        model=model,
                        anthropic_api_key=self.settings.ANTHROPIC_API_KEY,
                        temperature=self.settings.LLM_TEMPERATURE
                    )
                    logger.info(f"✅ Anthropic Claude initialized with model: {model} (fallback)")
                    return llm
                except Exception as e:
                    logger.error(f"Failed to initialize Claude: {str(e)}")
            else:
                logger.error("Anthropic API key not found.")
        
        # If all fail, raise an error
        raise RuntimeError(
            "Failed to initialize any LLM provider. Please ensure at least one API key "
            "(GOOGLE_GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY) is configured in .env"
        )
    
    def _setup_tools(self) -> List[Tool]:
        """Configure all available tools for the agent"""
        # Tools are already created with @tool decorator, use them directly
        # The @tool decorator creates proper StructuredTool instances with schemas
        # These work correctly with Gemini, OpenAI, and Claude
        tools = [
            create_task,
            get_task,
            list_tasks,
            update_task,
            delete_task,
            search_tasks,
            create_reminder,
            list_reminders
        ]
        
        # Ensure all tools are properly structured
        # The @tool decorator already handles this, but we verify
        for tool in tools:
            if not hasattr(tool, 'args_schema'):
                logger.warning(f"Tool {tool.name} does not have args_schema")
        
        return tools
    
    def _setup_agent(self) -> AgentExecutor:
        """Initialize the LLM agent with tools (supports Gemini, OpenAI, and Claude)"""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent Task Manager Agent. Your role is to help users manage tasks efficiently.

CRITICAL RULES - FOLLOW THESE EXACTLY:

1. TASK CREATION:
   - ALWAYS use the create_task tool when user wants to create a task
   - Extract ALL information from user input: title (REQUIRED), description, priority, due_date, estimated_hours, tags
   - For due dates: "today" = today at 6pm, "tomorrow" = tomorrow at 6pm, "evening" = today at 8pm, "morning" = tomorrow at 9am, "Friday" = next Friday at 6pm
   - Convert relative dates to ISO format: YYYY-MM-DDTHH:MM:SS
   - Priority must be: "low", "medium", "high", or "urgent" (lowercase)
   - After creating a task, ALWAYS show: "✅ Task '[title]' created successfully! ID: [task_id]"
   - Then offer: "Would you like to set a reminder for this task?"

2. LISTING TASKS:
   - When user says "list", "show", "display", "get all", "find all" with filters → use list_tasks tool
   - Examples:
     * "List all high priority tasks" → list_tasks(priority="high")
     * "Show me pending tasks" → list_tasks(status="pending")
     * "List all urgent tasks" → list_tasks(priority="urgent")
     * "Show me tasks due today" → list_tasks() then filter by due_date
   - ALWAYS display ALL returned tasks with FULL details:
     * Task ID: [id] (CRITICAL - users need this for reminders)
     * Title: [title]
     * Description: [description]
     * Priority: [priority]
     * Status: [status]
     * Due Date: [due_date]
     * Tags: [tags]
   - Format each task clearly, one per line with all details

3. SEARCHING TASKS:
   - When user says "search", "find", "show me tasks about", "tasks related to" → use search_tasks tool
   - Examples:
     * "Search for tasks about code review" → search_tasks(query="code review")
     * "Find tasks with tag 'work'" → search_tasks(query="work tag")
     * "Show me all tasks related to meetings" → search_tasks(query="meetings")
   - ALWAYS display ALL found tasks with FULL details including Task ID
   - If search returns empty, try expanding the query or use list_tasks as fallback

4. UPDATING TASKS:
   - When user says "update", "change", "set" → use update_task tool
   - Examples:
     * "Update task [task_id] status to in_progress" → update_task(task_id="[id]", status="in_progress")
     * "Update task [task_id] priority to urgent" → update_task(task_id="[id]", priority="urgent")
   - Extract task_id from user input (UUID format)
   - Confirm the update: "✅ Task updated successfully"

5. REMINDERS:
   - When user says "create reminder", "remind me", "set reminder" → use create_reminder tool
   - Examples:
     * "Create a reminder for task [task_id] in 1 hour" → create_reminder(task_id="[id]", reminder_time="in 1 hour")
     * "Create a reminder for task [task_id] tomorrow at 9am" → create_reminder(task_id="[id]", reminder_time="tomorrow at 9am")
   - Extract task_id from user input (can be in format "[task_id: xxx]" or just UUID)
   - Show confirmation with reminder time in IST format

6. LISTING REMINDERS:
   - When user says "list reminders", "show reminders" → use list_reminders tool
   - Show all reminders with task details

TOOL USAGE RULES:
- ALWAYS use the appropriate tool - never just acknowledge without using tools
- If a tool returns an error, explain it clearly and suggest alternatives
- If task_id is needed but not provided, ask the user or extract from previous context
- Always show Task IDs prominently - users need them for reminders and updates

RESPONSE FORMAT:
- Be concise but complete
- Always include Task IDs when displaying tasks
- Use clear formatting with line breaks
- Confirm all actions taken
- If something fails, explain why and suggest next steps

Current datetime: {current_time}"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Use create_openai_tools_agent for all providers (works with Gemini, OpenAI, and Claude)
        # All these providers support function calling/tools
        # For Gemini, ensure tools are properly bound
        try:
            # Bind tools to LLM to ensure proper schema handling
            # This helps Gemini understand the tool schemas correctly
            if hasattr(self.llm, 'bind_tools'):
                try:
                    bound_llm = self.llm.bind_tools(self.tools)
                    agent = create_openai_tools_agent(
                        llm=bound_llm,
                        tools=self.tools,
                        prompt=prompt_template
                    )
                except Exception as bind_error:
                    logger.debug(f"bind_tools failed, using LLM directly: {bind_error}")
                    agent = create_openai_tools_agent(
                        llm=self.llm,
                        tools=self.tools,
                        prompt=prompt_template
                    )
            else:
                agent = create_openai_tools_agent(
                    llm=self.llm,
                    tools=self.tools,
                    prompt=prompt_template
                )
        except Exception as e:
            logger.warning(f"Failed to create tools agent, trying ReAct agent: {e}")
            # Fallback to ReAct agent if tools agent fails
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt_template
            )
        
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=get_settings().DEBUG,  # Only verbose in debug mode
            max_iterations=15,  # Increased for complex queries
            early_stopping_method="force",
            handle_parsing_errors=True,  # Better error handling
            max_execution_time=60  # 60 second timeout
        )
        
        return executor
    
    async def process_user_input(self, user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process user input and execute appropriate actions
        
        Args:
            user_input: Natural language input from user
            conversation_history: Optional list of previous messages for context
        
        Returns:
            Agent response with results and actions taken
        """
        try:
            logger.info(f"Processing input: {user_input}")
            
            # Enhance short queries or follow-up responses
            enhanced_input = user_input
            user_lower = user_input.lower().strip()
            
            if user_lower in ["yes", "y"]:
                # Check if this is a follow-up to task creation (want to create reminder)
                if conversation_history:
                    # Look for recent task creation in history
                    for msg in reversed(conversation_history[-5:]):  # Check last 5 messages
                        assistant_msg = msg.get("assistant", "").lower()
                        if "created successfully" in assistant_msg and "id:" in assistant_msg:
                            # Extract task ID from the message
                            import re
                            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                            match = re.search(uuid_pattern, msg.get("assistant", ""), re.IGNORECASE)
                            if match:
                                task_id = match.group(0)
                                enhanced_input = f"Create a reminder for task {task_id} in 1 hour"
                                logger.info(f"Detected 'yes' response after task creation, creating reminder for task {task_id}")
                                break
                
                # If no task creation found, treat as general follow-up
                if enhanced_input == user_input:
                    enhanced_input = f"{user_input} - show me the full details of the tasks from the previous search results"
            elif user_lower in ["show me", "details", "show details"]:
                enhanced_input = f"{user_input} - show me the full details of the tasks from the previous search results"
            
            # Add context from conversation history if available
            if conversation_history:
                context = "\n".join([f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}" 
                                    for msg in conversation_history[-3:]])  # Last 3 exchanges
                enhanced_input = f"Previous conversation:\n{context}\n\nCurrent request: {enhanced_input}"
            
            # Run agent in sync context (agent_executor.invoke is sync)
            response = self.agent_executor.invoke({
                "input": enhanced_input,
                "current_time": datetime.now().isoformat()
            })
            
            logger.info(f"Agent response: {response}")
            
            output = response.get("output", "")
            
            # Extract and format tool results from intermediate steps
            if "intermediate_steps" in response:
                steps = response.get("intermediate_steps", [])
                if steps:
                    # Process all tool results, not just the last one
                    formatted_results = []
                    for step in steps:
                        if len(step) > 1:
                            tool_name = step[0].tool if hasattr(step[0], 'tool') else "unknown"
                            tool_result = step[1]
                            
                            # Format based on tool type and result
                            if isinstance(tool_result, dict):
                                if tool_result.get("success"):
                                    formatted_results.append(tool_result.get("message", "Operation completed successfully"))
                                elif tool_result.get("error"):
                                    formatted_results.append(f"Error: {tool_result.get('error')}")
                                elif "task_id" in tool_result:
                                    # Task creation result
                                    formatted_results.append(tool_result.get("message", "Task created successfully"))
                                elif "reminders" in tool_result:
                                    # Reminder list result
                                    reminders = tool_result.get("reminders", [])
                                    if reminders:
                                        reminder_list = "\n".join([
                                            f"- Reminder for task {r.get('task_id', 'N/A')} at {r.get('reminder_time', 'N/A')}"
                                            for r in reminders[:10]
                                        ])
                                        formatted_results.append(f"Found {len(reminders)} reminder(s):\n{reminder_list}")
                                    else:
                                        formatted_results.append("No reminders found.")
                            elif isinstance(tool_result, list) and len(tool_result) > 0:
                                # List of tasks
                                task_count = len(tool_result)
                                task_list = "\n\n".join([
                                    f"**Task ID:** `{task.get('id', 'N/A')}`\n"
                                    f"**Title:** {task.get('title', 'Untitled')}\n"
                                    f"**Description:** {task.get('description', 'No description')}\n"
                                    f"**Priority:** {task.get('priority', 'medium')}\n"
                                    f"**Status:** {task.get('status', 'pending')}\n"
                                    f"**Due Date:** {task.get('due_date', 'No due date')}\n"
                                    f"**Tags:** {', '.join(task.get('tags', [])) if task.get('tags') else 'None'}"
                                    for task in tool_result[:20]  # Show up to 20 tasks
                                ])
                                formatted_results.append(f"Found {task_count} task(s):\n\n{task_list}")
                                if task_count > 20:
                                    formatted_results.append(f"\n... and {task_count - 20} more task(s)")
                            elif isinstance(tool_result, str):
                                formatted_results.append(tool_result)
                    
                    if formatted_results:
                        output = "\n\n".join(formatted_results)
            
            # Better fallback message based on input
            if not output:
                user_lower = user_input.lower()
                if any(word in user_lower for word in ["list", "show", "display", "get all", "find"]):
                    output = "I couldn't retrieve the tasks. Please try again or check if there are any tasks in the system."
                elif any(word in user_lower for word in ["create", "add", "new"]):
                    output = "I couldn't create the task. Please check the details and try again."
                else:
                    output = "I've processed your request. If you expected a specific action, please try rephrasing your request."
            
            return {
                "status": "success",
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing input: {error_msg}")
            logger.exception("Full traceback:")
            
            # Provide helpful error messages for common issues
            if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                # Determine which provider had the quota issue
                provider_name = "API"
                if "gemini" in error_msg.lower() or "google" in error_msg.lower():
                    provider_name = "Google Gemini"
                    help_url = "https://makersuite.google.com/app/apikey"
                elif "anthropic" in error_msg.lower() or "claude" in error_msg.lower():
                    provider_name = "Anthropic Claude"
                    help_url = "https://console.anthropic.com/settings/keys"
                else:
                    provider_name = "OpenAI"
                    help_url = "https://platform.openai.com/usage"
                
                error_msg = f"{provider_name} API quota exceeded. Please check your account billing and usage limits."
                user_friendly_msg = (
                    f"⚠️ **{provider_name} API Quota Exceeded**\n\n"
                    f"Your {provider_name} API key has reached its usage limit. To resolve this:\n\n"
                    f"1. **Check your usage**: Visit {help_url}\n"
                    f"2. **Add billing**: Check your account billing settings\n"
                    f"3. **Upgrade plan**: If needed, upgrade your plan\n"
                    f"4. **Wait for reset**: Free tier quotas reset monthly\n\n"
                    "**Alternative**: You can still create tasks manually using the 'Create Task' page!"
                )
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                error_msg = "API key error. Please check your API key configuration in .env file."
                user_friendly_msg = "API key error. Please check your API key configuration in the .env file."
            elif "tool" in error_msg.lower():
                error_msg = f"Tool execution error: {error_msg}. The task may still have been created - please check the task list."
                user_friendly_msg = error_msg
            else:
                user_friendly_msg = f"I encountered an error: {error_msg}. Please try again or check the backend logs."
            
            return {
                "status": "error",
                "error": error_msg,
                "output": user_friendly_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_task_summary(self) -> Dict[str, Any]:
        """Get high-level summary of all tasks"""
        summary_prompt = """
        Analyze all tasks and provide:
        1. Total count by status and priority
        2. Overdue tasks
        3. High-priority items
        4. Workload distribution
        5. Recommendations for task management
        """
        return await self.process_user_input(summary_prompt)
    
    async def suggest_next_task(self) -> Dict[str, Any]:
        """AI recommendation for next task to work on"""
        prompt = "Based on priorities, due dates, and workload, what task should I work on next?"
        return await self.process_user_input(prompt)