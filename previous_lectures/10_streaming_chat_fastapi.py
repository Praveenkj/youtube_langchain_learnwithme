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


from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Post endpoint for chat
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_input = data.get("user_input", "")
    
    if not user_input:
        return {"error": "No user input provided."}
    
    # Define the prompt template
    
    prompt = PromptTemplate.from_template(
        """You are a helpful AI assistant. Answer the question below shortly and briefly.

        Question: {question}

        Answer:"""
    )

    chat_chain = prompt | openai_llm | StrOutputParser()

    # res = chat_chain.invoke({"question": user_input})
    # return JSONResponse({"answer": res})
    
    def generate():
        try:
            for chunk in chat_chain.stream({"question": user_input}):
                # Changed to "answer" field
                event_data = json.dumps({"answer": chunk})
                yield f"data: {event_data}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        content=generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )



# Generator function overview

# def get_all_numbers():
#     return [i for i in range(100000)]  # Creates entire list

# # Generator function - one at a time
# def get_numbers():
#     for i in range(100000):
#         yield i  # Only creates one number at a time
    

# def countdown():
#     yield 3
#     yield 2  
#     yield 1
#     yield "Blast off!"

# # Usage
# gen = countdown()
# print(next(gen))  # 3
# print(next(gen))  # 2
# print(next(gen))  # 1
# print(next(gen))  # "Blast off!"



# Any yield = Generator


# Generators maintain their state and sequence through Python's internal mechanism.