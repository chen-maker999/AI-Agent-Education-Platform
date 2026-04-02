"""调试工具获取"""
import sys
sys.path.insert(0, '.')
import json

# 加载 agents
with open('services/agent/crud/data/agents.json', 'r', encoding='utf-8') as f:
    agents = json.load(f)

agent = agents[0]
print(f'Agent: {agent["name"]}')
print(f'enabled_tools type: {type(agent["enabled_tools"])}')
print(f'enabled_tools: {agent["enabled_tools"]}')

# 测试 get_tools_for_agent
from services.agent.tools.registry import get_tools_for_agent
tools = get_tools_for_agent(agent['enabled_tools'], 'general')
print(f'Tools count: {len(tools)}')
