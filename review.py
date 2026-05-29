# reviewer.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
   model="llama-3.3-70b-versatile",
    temperature=0.3,
)

review_prompt = PromptTemplate(
    input_variables=["code", "criteria"],
    template="""
You are a senior software engineer reviewing code before a git push.

Acceptance Criteria:
{criteria}

Code to Review:
{code}

Provide your review in this structure:

**Acceptance Criteria Check**
You are a senior software architect and code review expert, you have experience of about in 20 years in tech related feild and have
a good expertise in software related things
- Go through each criterion and state if the code meets it or not.
also make it in tabular form the output like  in the first column states the acceptance criteria and in the second columns mark it as "MET ✅" OR "NOT MET ❌"
and in the third column add the reason why it was good or not , give reasoning why it was met or not 

**Verdict**
✅ GOOD TO PUSH | ⚠️ PUSH WITH CAUTION | ❌ DO NOT PUSH

**Summary**
2-3 lines max on overall quality and verdict reason.
"""
)

chain = review_prompt | llm

code = TextLoader("code.py").load()[0].page_content
criteria = TextLoader("ac.txt").load()[0].page_content

print("\n🔍 Reviewing code against acceptance criteria...\n")
print("=" * 60)
response = chain.invoke({"code": code, "criteria": criteria})
print(response.content)
print("=" * 60)