from typing import AsyncGenerator 

from config import get_settings  
from sqlalchemy.orm import DeclarativeBase 
from sqlalchemy.ext.asyncio import create_async_engine 
from sqlalchemy.ext.asyncio import  AsyncSession , async_sessionmaker  


settings = get_settings() 
CONNECTION  = settings.database.CONNECTION_STR

async_engine  = create_async_engine(CONNECTION)
local_session = async_sessionmaker(
                                        bind=async_engine , 
                                        class_ =AsyncSession ,
                                        expire_on_commit= False, 
                                        autoflush = False 
                                        )

class Base(DeclarativeBase) : 
    pass  

async def get_connection() ->AsyncGenerator[AsyncSession,None]: 
    async with local_session() as session  : 
        try :
            yield session  
            await session.commit() 
        except Exception as e :  
            await session.rollback()
            raise 
        finally : 
            await session.close()