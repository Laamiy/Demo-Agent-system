import os
import subprocess
from common.logger import logger
from orchestrator.tools.constants import STDOUT_MAX_LEN , STDERR_MAX_LEN
from orchestrator.tools.constants import SUDO_PASSWORD

def bash(command: str, timeout: int = 60) -> dict:
    """
    Execute a shell command. Automatically handles sudo by injecting
    the password via stdin when SUDO_PASSWORD is set.
    """
    logger.info("your password is : %s ", SUDO_PASSWORD)
    if command.strip().startswith("sudo") and SUDO_PASSWORD:
        command = f"echo {SUDO_PASSWORD!r} | sudo -S {command.removeprefix('sudo').strip()}"

    logger.info("bash: %s", command[:200])

    try:
        result = subprocess.run(
                                    command,
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout,
                                    env={**os.environ},
                                )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Truncate 
        # Avoid flooding context window
        if len(stdout) > STDOUT_MAX_LEN:
            stdout = stdout[:STDOUT_MAX_LEN//2] + "\n...[truncated]...\n" + stdout[-STDOUT_MAX_LEN//2:]
            
        if len(stderr) > STDERR_MAX_LEN:
            stderr = stderr[-STDERR_MAX_LEN:]

        logger.info("bash returncode=%d stdout=%s", result.returncode, stdout[:120])

        return {
            "stdout":     stdout,
            "stderr":     stderr,
            "returncode": result.returncode,
            "success":    result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        logger.error("bash timeout: %s", command[:100])
        return {"stdout": "", "stderr": "Command timed out.", "returncode": -1, "success": False}

    except Exception as e:
        logger.error("bash error: %s", e)
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}