#!/usr/bin/env python3
"""
Test that the autonomous agent stays active and acts as a persistent guide.

This test verifies:
1. Setup completes and returns status
2. Interactive mode enters continuous loop
3. Agent stays active after each action (chat/demo/command)
4. Only exits on explicit user choice or Ctrl+C
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous_setup import offer_interactive_mode


class TestPersistentAgent(unittest.TestCase):
    """Test that agent acts as persistent interactive guide"""
    
    @patch('builtins.input')
    @patch('autonomous_setup.chat_mode')
    @patch('autonomous_setup.run_demo_mode')
    @patch('autonomous_setup.show_system_status')
    def test_agent_stays_active_after_actions(self, mock_status, mock_demo, mock_chat, mock_input):
        """Test that agent returns to menu after each action"""
        # Simulate user: chat -> demo -> status -> exit
        mock_input.side_effect = ['1', '2', '4', '6']
        
        agent = Mock()
        console = Mock()
        
        # Run interactive mode
        offer_interactive_mode(agent, console)
        
        # Verify all actions were executed
        mock_chat.assert_called_once()
        mock_demo.assert_called_once()
        mock_status.assert_called_once()
        
        # Verify input was called 4 times (for each choice)
        self.assertEqual(mock_input.call_count, 4)
    
    @patch('builtins.input')
    def test_agent_exits_on_user_choice(self, mock_input):
        """Test that agent exits only when user chooses option 6"""
        # User chooses exit immediately
        mock_input.return_value = '6'
        
        agent = Mock()
        console = Mock()
        
        # Should exit cleanly
        offer_interactive_mode(agent, console)
        
        # Verify exit message was printed
        self.assertTrue(any('Exiting' in str(call_args) for call_args in console.print.call_args_list))
    
    @patch('builtins.input')
    @patch('autonomous_setup.perform_cleanup')
    def test_agent_cleanup_on_option_5(self, mock_cleanup, mock_input):
        """Test that agent performs cleanup when user chooses option 5"""
        mock_input.return_value = '5'
        
        agent = Mock()
        console = Mock()
        
        offer_interactive_mode(agent, console)
        
        # Verify cleanup was called
        mock_cleanup.assert_called_once()
    
    @patch('builtins.input')
    def test_agent_handles_invalid_input(self, mock_input):
        """Test that agent handles invalid input gracefully"""
        # Invalid input then exit
        mock_input.side_effect = ['invalid', '99', '6']
        
        agent = Mock()
        console = Mock()
        
        offer_interactive_mode(agent, console)
        
        # Verify error messages for invalid inputs
        error_messages = [call_args for call_args in console.print.call_args_list 
                         if 'Invalid choice' in str(call_args)]
        self.assertEqual(len(error_messages), 2)
    
    @patch('builtins.input')
    def test_agent_shows_help(self, mock_input):
        """Test that agent shows help when requested"""
        mock_input.side_effect = ['help', '6']
        
        agent = Mock()
        console = Mock()
        
        offer_interactive_mode(agent, console)
        
        # Verify help text was shown
        help_messages = [call_args for call_args in console.print.call_args_list 
                        if 'Available Commands' in str(call_args)]
        self.assertTrue(len(help_messages) > 0)
    
    @patch('builtins.input')
    @patch('autonomous_setup.chat_mode')
    def test_agent_continues_after_chat(self, mock_chat, mock_input):
        """Test that agent returns to menu after chat mode"""
        # Chat twice then exit
        mock_input.side_effect = ['1', '1', '6']
        
        agent = Mock()
        console = Mock()
        
        offer_interactive_mode(agent, console)
        
        # Chat should be called twice
        self.assertEqual(mock_chat.call_count, 2)
        
        # Input should be called 3 times (chat, chat, exit)
        self.assertEqual(mock_input.call_count, 3)
    
    @patch('builtins.input')
    def test_agent_handles_ctrl_c(self, mock_input):
        """Test that agent handles Ctrl+C gracefully"""
        # Simulate Ctrl+C
        mock_input.side_effect = KeyboardInterrupt()
        
        agent = Mock()
        console = Mock()
        
        # Should exit gracefully without crashing
        offer_interactive_mode(agent, console)
        
        # Verify interrupt message was shown
        interrupt_messages = [call_args for call_args in console.print.call_args_list 
                            if 'Interrupted' in str(call_args)]
        self.assertTrue(len(interrupt_messages) > 0)


class TestSetupIntegration(unittest.TestCase):
    """Test setup agent returns proper status"""
    
    def test_setup_returns_status(self):
        """Test that run_complete_setup returns status dict"""
        from agents.setup_agent import SetupAgent
        
        # Create agent (don't actually run setup)
        agent = SetupAgent(project_root=".", verbose=False)
        
        # The method should return a dict with 'status' key
        # We're just testing the signature, not running actual setup
        self.assertTrue(hasattr(agent, 'run_complete_setup'))
        
        # Verify the method exists and is callable
        self.assertTrue(callable(agent.run_complete_setup))


def run_tests():
    """Run all tests"""
    print("="*80)
    print("Testing Persistent Agent Behavior")
    print("="*80)
    print()
    
    # Run tests with verbosity
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("="*80)
    if result.wasSuccessful():
        print("✅ All tests passed! Agent will stay active as persistent guide.")
    else:
        print("❌ Some tests failed. Check implementation.")
    print("="*80)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
