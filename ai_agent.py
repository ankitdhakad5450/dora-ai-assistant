from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain.tools import tool  # ✅ Add this
from dotenv import load_dotenv
from tools import analyze_image_with_query
import wikipedia

load_dotenv()

# 🌟 Dora’s system prompt
system_prompt = """You are Dora — a witty, clever, and helpful AI assistant.
You can:
- Use the 'analyze_image_with_query' tool for vision-based questions.
- Use the 'get_wikipedia_answer' tool for factual knowledge (like 'Who is Rohit Sharma?').
Always reply like a friendly assistant Dora would.
"""

# 🧠 Gemini Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
)

# 🌍 Wikipedia Tool (decorated)
@tool("get_wikipedia_answer", return_direct=True)
def get_wikipedia_answer(query: str) -> str:
    """Fetch a short Wikipedia summary about a person, place, or topic."""
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"That’s a bit broad. Maybe you meant one of these: {', '.join(e.options[:3])}"
    except Exception:
        return "Sorry, I couldn’t find anything about that."

# 🚀 Query Handler
def ask_agent(user_query: str) -> str:
    # Create agent
    agent = create_agent(
        model=llm,
        tools=[analyze_image_with_query, get_wikipedia_answer],
    )

    # Define system + user messages
    input_messages = {
        "messages": [
            SystemMessage(content=system_prompt),
            {"role": "user", "content": user_query},
        ]
    }

    # Run agent
    response = agent.invoke(input_messages)
    return response["messages"][-1].content


# ✅ Test
if __name__ == "__main__":
    print(ask_agent("Who is Rohit Sharma?"))
