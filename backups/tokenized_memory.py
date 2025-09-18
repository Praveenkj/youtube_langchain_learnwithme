# Not working though

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import tiktoken

class TokenLimitedHistory:
    def __init__(self, max_tokens=1000):
        self.history = ChatMessageHistory()
        self.max_tokens = max_tokens
        self.encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self._token_count = 0  # Cache token count
    
    def add_message(self, message):
        self.history.add_message(message)
        self._token_count += len(self.encoder.encode(message.content))
        self._trim_messages()
    
    def add_user_message(self, message):
        self.history.add_user_message(message)
        self._token_count += len(self.encoder.encode(message))
        self._trim_messages()
    
    def add_ai_message(self, message):
        self.history.add_ai_message(message)
        self._token_count += len(self.encoder.encode(message))
        self._trim_messages()
    
    @property
    def messages(self):
        return self.history.messages
    
    def _trim_messages(self):
        while self._token_count > self.max_tokens and len(self.messages) > 1:
            removed = self.history.messages.pop(0)
            self._token_count -= len(self.encoder.encode(removed.content))


# Usage remains same
store = {}
def get_history(session_id):
    if session_id not in store:
        store[session_id] = TokenLimitedHistory(max_tokens=500)
    return store[session_id]

# Chain
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful assistant."),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

chain = prompt | google_llm | StrOutputParser()

# With memory
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Usage
response = chain_with_history.invoke(
    {"input": "Hi, I'm Praveen"},
    config={"configurable": {"session_id": "abc123"}}
)
print(response)
