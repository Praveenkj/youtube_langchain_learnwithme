import langchain
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

google_llm = ChatGoogleGenerativeAI(
    temperature=0, 
    model="gemini-2.0-flash", 
    api_key=google_api_key,
    max_tokens=200
)

openai_llm = ChatOpenAI(
    temperature=0, 
    model="gpt-4", 
    api_key=openai_api_key
)

##### RAG #####

##### Loading the docs #####

from langchain.agents import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader

pdf_loader_1 = PyPDFLoader(
    "./docs_for_rag/for_agents_lectures/wellarchitected-framework.pdf",
)

pdf_loader_2 = PyPDFLoader(
    "./docs_for_rag/for_agents_lectures/gzip.pdf",
)

text_loader = TextLoader(
    "./docs_for_rag/for_agents_lectures/coolie_english.txt",
)

pdf_1_docs = pdf_loader_1.load()
pdf_2_docs = pdf_loader_2.load()
text_docs = text_loader.load()

all_docs = pdf_1_docs + pdf_2_docs + text_docs

##### Splitting the docs #####

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=100
)

split_docs = text_splitter.split_documents(all_docs)


##### Creating FAISS store #####

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(split_docs, embeddings)


##### Tool creation - RAG #####

from langchain.agents import tool

@tool
def search_documents(input: str) -> str:
    """Search through documents to answer questions about AWS Well-Architected Framework, GZIP, and Coolie movie."""
    
    retriever = vectorstore.as_retriever()

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant"),
        ("human", """Always answer the question just by using the context provided and not from your knowledge.
            Context: {context}
            question: {input}
        
            Answer: 
        """),
        ("placeholder", "{agent_scratchpad}")
    ])


    chain = {"context": retriever, "input": RunnablePassthrough()} | prompt | google_llm

    rag_search_result = chain.invoke(input)

    return rag_search_result


##### Executing Agent & available tools #####

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

tools = [search_documents]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")]
)

agent = create_tool_calling_agent(google_llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

res = agent_executor.invoke({"input": "Who is dahaa in coolie movie?"})