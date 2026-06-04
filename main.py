from fastapi import FastAPI 
from api.router import infer 
from config import get_settings 
from api.deps.Agent import QwenModelAgent
from api.deps.core import Base , async_engine 
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings() 

async  def lifespan(app : FastAPI) :
    
    app.state.qwen_model_agent = QwenModelAgent()
    async with async_engine.begin() as conn: 
        
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield 
    
    await async_engine.dispose()
             
    
app = FastAPI(lifespan=lifespan , version="1.0",title= "AGENT DEMO")

app.add_middleware(
                            CORSMiddleware,   
                            allow_origins=settings.CORS_ORIGINS, 
                            allow_headers=["Content-Type"],
                            allow_methods=["GET", "POST"],
                        )

app.include_router(infer.router , prefix = "/infer" , tags= ["Inference"])

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(    "main:app" , 
                    reload=True , 
                    host = settings.HOST , 
                    port = settings.PORT , 
                    workers= settings.WORKERS
                    )
