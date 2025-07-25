import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase

# Load .env file
load_dotenv()

# ✅ Ensure your .env file contains:
# OPENAI_API_KEY=sk-...

# Create database object
db = SQLDatabase.from_uri("sqlite:///uploaded.db")

# ✅ Create LLM with correct API key
llm = ChatOpenAI(
    temperature=0,
    model="gpt-3.5-turbo",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# ✅ Create SQL agent
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm),
    verbose=True
)

# ✅ Query function
def ask_query(question: str) -> str:
    return agent_executor.run(question)


