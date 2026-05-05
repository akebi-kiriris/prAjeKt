"""Tests for Phase 6.6 LangChain Chains

Unit tests for task generation, summary generation, and tool selection chains.
"""

import pytest
from unittest.mock import MagicMock
from chains import (
    create_task_generation_chain,
    create_task_summary_chain,
    create_group_snapshot_chain,
    create_tool_selection_chain,
    PromptManager,
)


class TestPromptManager:
    """Tests for PromptManager utility."""

    def test_get_config_returns_dict(self):
        """PromptManager.get_config should return configuration dict."""
        mgr = PromptManager()
        config = mgr.get_config("task_generation")

        assert isinstance(config, dict)
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_config_all_keys(self):
        """PromptManager should have config for all prompt types."""
        mgr = PromptManager()

        configs = {
            "task_generation": mgr.get_config("task_generation"),
            "task_summary": mgr.get_config("task_summary"),
            "group_snapshot": mgr.get_config("group_snapshot"),
            "tool_selection": mgr.get_config("tool_selection"),
        }

        for key, config in configs.items():
            assert isinstance(config, dict), f"Config for {key} is not dict"

    def test_get_version_info(self):
        """PromptManager.get_version_info should return structured version info."""
        mgr = PromptManager()
        version = mgr.get_version_info()

        assert isinstance(version, dict)
        assert "version" in version
        assert "langchain_version" in version
        assert "timestamp" in version


class TestTaskGenerationChain:
    """Tests for task generation chain."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM instance."""
        llm = MagicMock()
        return llm

    def test_create_task_generation_chain_returns_chain(self, mock_llm):
        """create_task_generation_chain should return a chain."""
        chain = create_task_generation_chain(mock_llm)

        # Chain should have invoke method
        assert hasattr(chain, "invoke")

    def test_task_chain_structure(self, mock_llm):
        """Task generation chain should have proper structure."""
        chain = create_task_generation_chain(mock_llm)

        # Mock LLM response
        mock_llm.return_value = [
            {
                "title": "Task 1",
                "description": "Do something",
                "estimated_hours": 2,
                "priority": "high",
            }
        ]

        # Should not raise error
        assert chain is not None


class TestSummaryChains:
    """Tests for summary generation chains."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM instance."""
        return MagicMock()

    def test_create_task_summary_chain(self, mock_llm):
        """create_task_summary_chain should return a chain."""
        chain = create_task_summary_chain(mock_llm)

        assert hasattr(chain, "invoke")

    def test_create_group_snapshot_chain(self, mock_llm):
        """create_group_snapshot_chain should return a chain."""
        chain = create_group_snapshot_chain(mock_llm)

        assert hasattr(chain, "invoke")


class TestToolSelectionChain:
    """Tests for tool selection chain."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM instance."""
        return MagicMock()

    def test_create_tool_selection_chain(self, mock_llm):
        """create_tool_selection_chain should return a chain."""
        chain = create_tool_selection_chain(mock_llm)

        assert hasattr(chain, "invoke")


class TestChainIntegration:
    """Integration tests for chains."""

    def test_imports_are_consistent(self):
        """All chain imports should be consistent."""
        from chains import (
            create_task_generation_chain,
            generate_tasks,
            create_task_summary_chain,
            create_group_snapshot_chain,
            generate_task_summary,
            generate_group_snapshot,
            create_tool_selection_chain,
            select_tools,
            parse_tool_selection_result,
        )

        # Should not raise ImportError
        assert callable(create_task_generation_chain)
        assert callable(generate_tasks)
        assert callable(create_task_summary_chain)
        assert callable(create_group_snapshot_chain)
        assert callable(generate_task_summary)
        assert callable(generate_group_snapshot)
        assert callable(create_tool_selection_chain)
        assert callable(select_tools)
        assert callable(parse_tool_selection_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
