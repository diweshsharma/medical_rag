# import os
# from app.config import config

# from langchain.chat_models import init_chat_model

# model = init_chat_model("gpt-5.6-luna",api_key=config.omni_key, base_url=config.omni_base , model_provider = "openai")

# response = model.invoke("hey! what are you doing?")
# print(response.content)

from groq import Groq
from app.config import config

client = Groq(api_key=config.groq_api)

models = client.models.list()

for model in models.data:
    print(model.id)