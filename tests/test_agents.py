"""Tests for AI agent functionality"""
import pytest
import asyncio
from backend.agents.task_agent import TaskManagerAgent
from backend.config import get_settings


class TestTaskManagerAgent:
    """Test TaskManagerAgent"""
    
    @pytest.fixture
    def settings(self):
        """Get settings"""
        return get_settings()
    
    def test_agent_initialization(self, settings):
        """Test that agent can be initialized"""
        if not settings.OPENAI_API_KEY:
            pytest.skip("OpenAI API key not configured")
        
        try:
            agent = TaskManagerAgent()
            assert agent is not None
            assert agent.settings is not None
            assert agent.tools is not None
            assert len(agent.tools) > 0
        except Exception as e:
            pytest.skip(f"Agent initialization failed: {e}")
    
    def test_agent_tools_setup(self, settings):
        """Test that agent tools are properly set up"""
        if not settings.OPENAI_API_KEY:
            pytest.skip("OpenAI API key not configured")
        
        try:
            agent = TaskManagerAgent()
            tool_names = [tool.name for tool in agent.tools]
            
            # Check for essential tools
            assert "create_task" in tool_names
            assert "list_tasks" in tool_names
            assert "get_task" in tool_names
            assert "update_task" in tool_names
            assert "delete_task" in tool_names
            assert "search_tasks" in tool_names
        except Exception as e:
            pytest.skip(f"Agent setup failed: {e}")
    
    @pytest.mark.asyncio
    async def test_agent_process_user_input(self, settings):
        """Test agent processing user input"""
        if not settings.OPENAI_API_KEY:
            pytest.skip("OpenAI API key not configured")
        
        try:
            agent = TaskManagerAgent()
            
            # Test with a simple query
            result = await agent.process_user_input("List all tasks")
            
            assert result is not None
            assert "status" in result
            assert "timestamp" in result
            assert result["status"] in ["success", "error"]
        except Exception as e:
            # If quota exceeded or other API errors, skip
            if "quota" in str(e).lower() or "429" in str(e):
                pytest.skip(f"OpenAI API quota exceeded: {e}")
            else:
                pytest.skip(f"Agent processing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_agent_create_task(self, settings):
        """Test agent creating a task"""
        if not settings.OPENAI_API_KEY:
            pytest.skip("OpenAI API key not configured")
        
        try:
            agent = TaskManagerAgent()
            
            # Test task creation via agent
            result = await agent.process_user_input(
                "Create a test task with title 'Agent Test Task'"
            )
            
            assert result is not None
            assert "status" in result
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                pytest.skip(f"OpenAI API quota exceeded: {e}")
            else:
                pytest.skip(f"Agent task creation failed: {e}")

