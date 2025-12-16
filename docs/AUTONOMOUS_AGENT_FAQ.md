## ❓ Autonomous Agent FAQ

### How does the agent stay active after setup?

The autonomous agent enters a **persistent interactive loop** after completing setup. It continuously shows a menu with options (chat, demo, commands, status) and only exits when you:
- Choose option 5 (Cleanup and Exit) or 6 (Exit)
- Press Ctrl+C (which offers optional cleanup)

This means you can run multiple demos, execute various commands, chat multiple times, and keep exploring - all without restarting the agent.

### What happens if I press Ctrl+C during setup?

The agent has a **signal handler** that catches Ctrl+C:
- **During setup**: Pauses setup, offers recovery info, may cleanup partial resources
- **In interactive mode**: Shows exit menu with cleanup option
- **Safe**: Never leaves orphaned containers or processes

### Can I use the agent for continuous testing?

Yes! The agent is designed for this. After setup:
1. Choose option 2 (Run Demo) repeatedly to test different scenarios
2. Choose option 3 (Custom Command) to execute specific Docker commands
3. Choose option 4 (System Status) to monitor health between tests
4. Return to menu automatically after each action

### Does the agent remember previous conversations?

Within the same session, yes. The chat mode maintains context within that specific chat session. However, when you exit chat and return, it starts fresh. For persistent knowledge, refer to the README or use the demo mode.

### What if setup fails partway through?

The agent has **self-healing capabilities**:
- Automatically retries failed operations (up to 3 times)
- Provides recovery instructions if complete healing fails
- Offers manual cleanup commands
- Saves setup logs for debugging
- Can be re-run safely (idempotent operations)

### Can I skip the interactive mode and just do setup?

Currently, the agent always enters interactive mode after setup. To exit quickly:
```bash
python3 autonomous_setup.py
# Wait for setup to complete
# When menu appears, press: 6 (Exit)
# System remains running at http://localhost:8080
```

For completely non-interactive setup, use Docker Compose directly:
```bash
docker compose up -d
```

### How do I exit without cleanup?

Choose **option 6 (Exit - Leave containers running)** from the menu. This:
- ✅ Exits the agent
- ✅ Leaves all containers running
- ✅ Keeps your data and configuration
- ✅ Dashboard remains accessible at http://localhost:8080

Later, you can:
```bash
# Stop containers
docker compose stop

# Start again
docker compose start

# Or cleanup manually
docker compose down -v
```

### What's the difference between options 5 and 6?

- **Option 5 (Cleanup and Exit)**: 
  - Stops all Docker containers
  - Removes containers and volumes
  - Cleans up ALL resources
  - Fresh start next time
  
- **Option 6 (Exit - Leave running)**:
  - Agent exits only
  - Containers keep running
  - Dashboard still accessible
  - Resume where you left off

---
