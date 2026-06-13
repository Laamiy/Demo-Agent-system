from config import get_settings 
settings = get_settings()


MAX_LEN = 6000
MAX_KEEP = 3000
STDOUT_MAX_LEN = 3000
STDERR_MAX_LEN = 1000

AGENT_WORKSPACE = settings.agent.WORKSPACE
SUDO_PASSWORD = settings.agent.SUDO_PASSWORD.get_secret_value()