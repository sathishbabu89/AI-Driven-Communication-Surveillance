from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_version=os.getenv("OPENAI_API_VERSION"),
)

deployment = os.getenv("AZURE_DEPLOYMENT_NAME")

response = client.chat.completions.create(
    model=deployment,
    messages=[
        {"role": "user", "content": "Tell about Sachin Tendulkar from Azure GPT-4o"}
    ]
)

print(response.choices[0].message.content)
