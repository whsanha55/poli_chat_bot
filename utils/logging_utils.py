import logging

# httpx 로거 비활성화
logging.getLogger("httpx").setLevel(logging.WARNING)

# 기본 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/poli_agent.log'),
        logging.StreamHandler()
    ]
)




def log_tool_usage(agent_name: str, tool_name: str, args: str):
    logger = logging.getLogger(agent_name)
    logger.info(f"Tool Used - Tool: {tool_name}, Arguments: {args}")

def log_agent_routing(from_agent: str, to_agent: str, reason: str = None):
    logger = logging.getLogger("supervisor")
    logger.info(f"Agent Routing - From: {from_agent}, To: {to_agent}, Reason: {reason}") 