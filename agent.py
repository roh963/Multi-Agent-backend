from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from tools import web_search, scrape_url

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_mistralai import ChatMistralAI

from rich import print
from dotenv import load_dotenv  
load_dotenv()

# model setup
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm = ChatMistralAI(model="mistral-small-2506", temperature=0.1)


# 1 agent
def search_search_agent():
    agent = create_agent(model=llm, tools=[web_search])
    return agent

# 2 agent 
def build_reader_agent():
    agent = create_agent(model=llm, tools=[web_search, scrape_url])
    return agent

# writer chain 
writter_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research writer and analyst with deep experience in producing 
structured, clear, and insightful reports across various domains. Your writing is precise, 
objective, and well-organized.

When given a topic and research findings, you produce a professional report with the following structure:

1. **Introduction** – Provide context, background, and why the topic matters.
2. **Key Findings** – Present the most important insights, organized by theme or importance.
3. **Analysis** – Interpret the findings, highlight patterns, contradictions, or implications.
4. **Conclusion** – Summarize takeaways and suggest next steps or open questions.
5. **Sources** – List all referenced URLs in a clean, numbered format.

Guidelines:
- Use clear headings and subheadings for readability.
- Write in a neutral, professional tone.
- Prioritize accuracy and insight over length.
- Highlight any gaps or limitations in the available research."""),

    ("human", """Topic: {topic}

Research Findings:
{research}

Using the above research, write a complete structured report with:
- A compelling Introduction
- Key Findings with supporting evidence
- A concise Conclusion with main takeaways
- A numbered Sources section listing all relevant URLs""")
])

writer_chain = writter_prompt | llm | StrOutputParser() 

# critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a sharp, constructive research critic with high standards for clarity, 
accuracy, and analytical depth. You are honest, specific, and never vague in your feedback.

When reviewing a report, you evaluate it across these dimensions:
- **Accuracy** – Are the facts well-supported and sourced?
- **Structure** – Is the report logically organized and easy to follow?
- **Depth** – Does it go beyond surface-level findings with real insight?
- **Clarity** – Is the language precise, concise, and free of filler?
- **Completeness** – Are there gaps, missing context, or unanswered questions?

Your critique format must always be:
1. **Score** – X/10 (be strict, a 9 or 10 is rare)
2. **Strengths** – What the report does well (2–3 specific points)
3. **Areas to Improve** – Concrete, actionable suggestions (2–4 points)
4. **One-Line Verdict** – A single sharp sentence summarizing the report's quality"""),

    ("human", """Review the research report below. Evaluate it strictly and be specific — 
vague feedback is not acceptable.

Report:
{report}

Provide your critique in this exact format:
- Score: X/10
- Strengths:
- Areas to Improve:
- One-Line Verdict:""")
])
critic_chain = critic_prompt | llm | StrOutputParser()  
