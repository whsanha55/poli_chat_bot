import logging
import os

# httpx 로거 비활성화
logging.getLogger("httpx").setLevel(logging.WARNING)

# 로그 디렉토리 생성
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 기본 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'poli_agent.log')),
        logging.StreamHandler()
    ]
)




def log_tool_usage(agent_name: str, tool_name: str, args: str):
    logger = logging.getLogger(agent_name)
    logger.info(f"Tool Used - Tool: {tool_name}, Arguments: {args}")

def log_agent_routing(from_agent: str, to_agent: str, reason: str = None):
    logger = logging.getLogger("supervisor")
    logger.info(f"Agent Routing - From: {from_agent}, To: {to_agent}, Reason: {reason}") 