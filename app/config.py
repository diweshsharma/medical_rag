import os 
from dotenv import load_dotenv

load_dotenv()

class config:
    groq_api = os.getenv("GROQ_API_KEY")
    
    
    #omnirouter
    omni_key = os.getenv("ci_api_key")
    omni_base = os.getenv("base_url")
    
    
    
config = config()