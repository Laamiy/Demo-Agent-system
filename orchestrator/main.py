from common.logger import logger


from orchestrator.schema import Commands
from orchestrator.model.ModelService import ModelService
from langchain_core.messages import HumanMessage, AIMessage
from orchestrator.orchestrator import build_graph, AgentState
        

REF_HIST = 20 

def run():
    logger.info("Starting model orchestrator...")
    model = ModelService()          
    graph = build_graph(model)      

    history: list = []

    logger.info("Ready. Type 'quit' to exit and 'clear' to reset history.")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            logger.info("Exiting.")
            break

        if not user_input:
            continue
        cmd = user_input.lower()
        
        if cmd in Commands.QUIT.value:
            break
        
        if cmd == Commands.CLEAR.value:
            history.clear()
            logger.info("History cleared.")
            continue

        state: AgentState = {
                                "messages": history + [HumanMessage(content=user_input)],
                                "intent":   "",
                                "response": None,
                                "iterations" : 0 , 
                            }
        # AgentState(messages = history + [HumanMessage(content=user_input)] , intent="" , response= None ) 

        try:
            result   = graph.invoke(state)
            response = result["response"]
            logger.info("Agent: %s", response)

            # for next turn
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=response))

            if len(history) > REF_HIST:
                history = history[-REF_HIST:]

        except Exception as e:
            logger.error("Orchestrator error: %s", e)

if __name__ == "__main__":
    run()
