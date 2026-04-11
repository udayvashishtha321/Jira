# startfile.py
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from langchain_groq import ChatGroq
load_dotenv()
from PyPDF2 import PdfReader



# Load model
"""llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.1-8B-Instruct",
    task="text-generation",
    max_new_tokens=1000,
   
)



chat = ChatHuggingFace(llm=llm)"""

model =ChatGroq(model="llama-3.3-70b-versatile",
                temperature=1,
          )


from PyPDF2 import PdfReader

def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""

    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"

    return text



def send_data(email, url, api_token,project_key, req_file, person_file):
    
    global EMAIL, URL, TOKEN, PROJECT
    global REQ_FILE, PERSON_FILE, REQ_TEXT, PERSON_TEXT

    EMAIL = email
    URL = url
    TOKEN = api_token
    PROJECT = project_key

    REQ_FILE = req_file
    PERSON_FILE = person_file

    # extract text and store globally
   

    return "done"
    
    

def analyze_requirement_doc():
  
  prompt = """ You are a Jira task generator.

REQUIREMENT:

Project Requirement Document
Project Name: E-Commerce Web Application
The system will allow users to browse products, add items to cart, place orders, and track
deliveries. Admin can manage products, categories, and orders.
User Features
• User can register and login
• User can browse products by category
• User can search products
• User can view product details
• User can add product to cart
• User can remove product from cart

Team Members:
Uvuv is backend developer
Aryan Saxena is frontend developer
Abhishek Rajput is database administrator
Uvuv v is tester

RULES:
- Assign tasks only from team members
- Do not create new names
- Return valid JSON only
- No explanation

1 Epic
Multiple Stories
Multiple Tasks under each Story
Each Task must include status = "TODO"
Each Task must include assignee selected based on skill mapping
Use ONLY the provided team skill list to assign work
Assign Backend work to backend developers
Assign UI work to frontend developers
Assign search / recommendation to ML engineers
Assign testing to QA
Assign DB work to database engineers
Assign API integration to backend engineers
If multiple people have same skill → distribute tasks evenly (round robin)

Return STRICT JSON ONLY
No explanation
No markdown
No extra text

data ={
  "project_key": "PDM",
  "epic": {
    "summary": "Implement Shopping Cart Feature",
    "description": "Epic for all tasks related to Shopping Cart functionality",
    "epic_name": "SHOPCART-1"
  },
  "stories": [
    {
      "summary": "Backend cart functionality",
      "description": "APIs to add/remove items and calculate totals",
      "tasks": [
        {
          "summary": "Create backend API for cart",
          "description": "Develop endpoints for adding/removing items from cart"
        }
      ]
    },
    {
      "summary": "Frontend cart UI",
      "description": "UI for shopping cart",
      "tasks": [
        {
          "summary": "Implement cart UI",
          "description": "Build UI for adding/removing items and showing totals"
        }
      ]
    },
    {
      "summary": "Payment integration",
      "description": "Connect cart with payment gateway",
      "tasks": [
        {
          "summary": "Integrate payment gateway",
          "description": "Connect cart with payment API for checkout"
        }
      ]
    }
  ]
}
Do NOT write any Markdown, headings, bullets, or extra text and all task must be in to do status. Only JSON.
"""
  res = model.invoke(prompt)
  return res.content
    
    
"""    
    
Team Members:
Uvuv is backend developer
Aryan Saxena is frontend developer
Abhishek Rajput is database administrator
Uvuv v is tester


Project Requirement Document
Project Name: E-Commerce Web Application
The system will allow users to browse products, add items to cart, place orders, and track
deliveries. Admin can manage products, categories, and orders.
User Features
• User can register and login
• User can browse products by category
• User can search products
• User can view product details
• User can add product to cart
• User can remove product from cart

You are a Senior Product Manager and Agile Business Analyst.
  Your job is to analyze the REQUIREMENT DOCUMENT and break it into:
  
  You are a Jira task generator.

REQUIREMENT:

Project Requirement Document
Project Name: E-Commerce Web Application
The system will allow users to browse products, add items to cart, place orders, and track
deliveries. Admin can manage products, categories, and orders.
User Features
• User can register and login
• User can browse products by category
• User can search products
• User can view product details
• User can add product to cart
• User can remove product from cart

Team Members:
Uvuv is backend developer
Aryan Saxena is frontend developer
Abhishek Rajput is database administrator
Uvuv v is tester

RULES:
- Assign tasks only from team members
- Do not create new names
- Return valid JSON only
- No explanation

1 Epic
Multiple Stories
Multiple Tasks under each Story
Each Task must include status = "TODO"
Each Task must include assignee selected based on skill mapping
Use ONLY the provided team skill list to assign work
Assign Backend work to backend developers
Assign UI work to frontend developers
Assign search / recommendation to ML engineers
Assign testing to QA
Assign DB work to database engineers
Assign API integration to backend engineers
If multiple people have same skill → distribute tasks evenly (round robin)

Return STRICT JSON ONLY
No explanation
No markdown
No extra text

data ={
  "project_key": "PDM",
  "epic": {
    "summary": "Implement Shopping Cart Feature",
    "description": "Epic for all tasks related to Shopping Cart functionality",
    "epic_name": "SHOPCART-1"
  },
  "stories": [
    {
      "summary": "Backend cart functionality",
      "description": "APIs to add/remove items and calculate totals",
      "tasks": [
        {
          "summary": "Create backend API for cart",
          "description": "Develop endpoints for adding/removing items from cart"
        }
      ]
    },
    {
      "summary": "Frontend cart UI",
      "description": "UI for shopping cart",
      "tasks": [
        {
          "summary": "Implement cart UI",
          "description": "Build UI for adding/removing items and showing totals"
        }
      ]
    },
    {
      "summary": "Payment integration",
      "description": "Connect cart with payment gateway",
      "tasks": [
        {
          "summary": "Integrate payment gateway",
          "description": "Connect cart with payment API for checkout"
        }
      ]
    }
  ]
}
Do NOT write any Markdown, headings, bullets, or extra text and all task must be in to do status. Only JSON."""