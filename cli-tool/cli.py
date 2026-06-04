import sys
import json
import httpx
from typing import List, Dict
from argparse import ArgumentParser

import logging 

logger = logging.getLogger(__name__) 

logger.setLevel(logging.DEBUG)

stream = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s -%(module)s')

stream.setFormatter(formatter)
stream.setLevel(logging.DEBUG)

logger.addHandler(stream)

class AgentCLI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.history: List[Dict[str, str]] = []
        self.client = httpx.Client(timeout=60)

    def _post(self, endpoint: str, payload: dict) -> dict | None:
        try:
            resp = self.client.post(f"{self.base_url}{endpoint}", json=payload)
            resp.raise_for_status()
            return resp.json()
        
        except httpx.ConnectError:
            logger.error("Cannot connect to backend. Is the server running?")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} - {e.response.text}")
            return None

    def _get(self, endpoint: str) -> dict | None:
        try:
            resp = self.client.get(f"{self.base_url}{endpoint}")
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e :
            logger.error("Cannot connect to backend. %s",e )
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code}")
            return None

    def chat(self, message: str) -> dict | None:
        payload = {
            "message": message,
            "history": self.history,
        }
        data = self._post("/chat", payload)
        if data is None:
            return None

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": data.get("response", "")})

        if len(self.history) > 20:
            self.history = self.history[-20:]

        return data

    def print_response(self, data: dict):
        logger.info(f"Agent: {data.get('response', '')}")

        tool_calls = data.get("tool_calls")
        if tool_calls:
            logger.info("Tools called:")
            for tc in tool_calls:
                args = json.dumps(tc.get("arguments", {}))
                logger.info(f"  - {tc.get('name')}({args})")

        tool_results = data.get("tool_results")
        if tool_results:
            logger.info("Results:")
            for tr in tool_results:
                if tr.get("error"):
                    logger.info(f"  - {tr['tool']}: ERROR - {tr['error']}")
                else:
                    result = json.dumps(tr.get("result", {}), indent=2)#[:200]
                    logger.info(f"  - {tr['tool']}: {result}")

    def list_tools(self):
        data = self._get("/tools")
        if not data:
            return
        tools = data.get("tools", [])
        logger.info("Available tools:")
        for t in tools:
            fn = t.get("function", {})
            logger.info(f"  - {fn.get('name')}: {fn.get('description', 'No description')}")

    def health(self) -> bool:
        data = self._get("/health")
        if not data:
            logger.info("Backend not responding. Start it with: uvicorn main:app")
            return False
        logger.info(f"Backend: {data.get('status')} | model_loaded={data.get('model_loaded')}")
        return True

    def clear_history(self):
        self.history.clear()
        logger.info("History cleared.")

    def run(self):
        if not self.health():
            sys.exit(1)

        logger.info("Commands: help, tools, clear, health, quit")

        while True:
            try:
                user_input = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                logger.info("Exiting.")
                break

            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd in ("quit", "exit", "q"):
                break

            if cmd == "help":
                logger.info("  help    - show commands")
                logger.info("  tools   - list available tools")
                logger.info("  clear   - clear conversation history")
                logger.info("  health  - check backend status")
                logger.info("  quit    - exit")
                continue

            if cmd == "clear":
                self.clear_history()
                continue

            if cmd == "tools":
                self.list_tools()
                continue

            if cmd == "health":
                self.health()
                continue

            data = self.chat(user_input)
            if data:
                self.print_response(data)

        self.client.close()


def main():
    parser = ArgumentParser(description="Agent CLI")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    cli = AgentCLI(f"http://localhost:{args.port}/infer")
    cli.run()


if __name__ == "__main__":
    main()