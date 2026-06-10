from dataclasses import dataclass 

@dataclass
class chatModel : 
    role : str  
    content  : str 
    name : str | None = None 