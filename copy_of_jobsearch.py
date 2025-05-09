# -*- coding: utf-8 -*-
"""Copy of JobSearch.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17_GL0h7DLuAZ_BmBdlYHBr956Y3XGM9j
"""

# Warning control
import warnings
warnings.filterwarnings('ignore')

from google.colab import drive
drive.mount('/content/drive')

!pip install llama-index --quiet
!pip install llama-index-llms-groq --quiet
!pip install llama-index-core --quiet
!pip install llama-index-readers-file --quiet
!pip install llama-index-tools-wolfram-alpha --quiet
!pip install llama-index-embeddings-huggingface --quiet
!pip install 'crewai[tools]' --quiet
!pip install -q crewai==0.28.8 crewai_tools==0.1.6 langchain_community==0.0.29
!pip install -Uq transformers
!pip install -q tokenizers>=0.21,<0.22
!pip install numpy==1.25.0
!pip install groq

from llama_index.llms.groq import Groq
from google.colab import userdata

from langchain_openai import ChatOpenAI

# Define your API key here
groq_api_key = userdata.get('groq_key')

def select_model(model_name, temperature=0.1, max_tokens=2000):

  # using LLama3 on groq free API
  llm = ChatOpenAI(
      openai_api_base="https://api.groq.com/openai/v1",
      openai_api_key=groq_api_key,
      model=model_name,
      #model = "distil-whisper-large-v3-en",
      # model="llama3-70b-8192",
      # model="deepseek-r1-distill-qwen-32b",
      # model = "deepseek-r1-distill-llama-70b",
      temperature=temperature,
      max_tokens=max_tokens,
  )
  return llm

import os
os.environ["SERPER_API_KEY"] = userdata.get('Serper_Key')
os.environ["OPENAI_API_KEY"] = userdata.get('openaikey')
from crewai import Crew, Agent, Task, Process
from crewai_tools import FileReadTool
from crewai_tools import SerperDevTool
from crewai_tools import DirectoryReadTool

from crewai_tools import BaseTool
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperTokenizer
from groq import Groq

class JobRankingTool(BaseTool):
    name: str ="Job Ranking Tool"
    description: str = ("Given the list of jobs provided by the search_and_ranking_agent, rank the postings based on keywords found."
    )

    def _run(self, job_postings: list, keywords: list) -> list:
      """
    Analyze the retrieved job postings using the following ranking algorithm:
    - For each job posting (URL), check for the provided keywords.
    - Add 1 point to the job's score each time a keyword is found in the posting URL.
    - Rank the job postings based on their total score, with higher scores listed at the top.

    Args:
        job_postings (list): A list of job posting URLs.
        keywords (list): A list of keywords to search for.

    Returns:
        list: A ranked list of job postings, including their scores.
      """
      ranked_jobs = []

      for job in job_postings:
          score = 0

        # Check for keywords in the job posting URL
          if isinstance(job, str):  # Ensure it's a string
              for keyword in keywords:
                  if keyword.lower() in job.lower():
                      score += 1

        # Add the job and its score to the ranked list
          ranked_jobs.append({"job": job, "score": score})

    # Sort jobs by score in descending order
      ranked_jobs.sort(key=lambda x: x["score"], reverse=True)

      return ranked_jobs

class WhisperAgent(Agent):
    def __init__(self, model_size="small", role=None, goal=None, backstory=None):
        super().__init__(role=role, goal=goal, backstory=backstory)
        self.llm=Groq(api_key=userdata.get('groq_key'))
        #openai.api_key = os.environ.get("OPENAI_API_KEY")

    def transcribe_audio(self, audio_path):
        client = self.llm
        audio_file= open(audio_path, "rb")

        transcription = client.audio.transcriptions.create(
        model='whisper-large-v3',
        file=audio_file
        )

        return transcription.text

#create more tools later
directory_read_tool = DirectoryReadTool(directory='/content/drive/MyDrive/crewAI_docs_updated')
file_read_tool = FileReadTool()
search_tool = SerperDevTool()
ranking_tool= JobRankingTool()

query_processing_agent = Agent(
    role="Job Query Processor and Comparison Agent",
    goal=(
        "Process and clean user job queries, translating them into a structured format. "
        "Compare and rank various job options based on similarity, relevance, or importance to the user's requirements."
    ),
    backstory=(
        "An expert in job data processing and comparison, you are skilled at interpreting and refining user queries. "
        "Your mission is to ensure the user's search intent is accurately captured and translated into a structured format. "
        "Using advanced tools, you clean and preprocess the query, then compare and rank job options to present the most relevant results. "
        "Your goal is to deliver precise and user-friendly outputs that align closely with the user's preferences and constraints."
    ),
    llm=select_model(model_name="llama-3.1-8b-instant", max_tokens=2000),
    allow_delegation=False,
    verbose=True
)

search_and_ranking_agent = Agent(
    role="Search and Ranking Agent",
    goal=("Compare and rank job options based on similarity, relevance, or importance to the user's requirements "
    "as given by the user query generated by the query_processing_agent."
    ),
    backstory=(
        "An expert in comparing and ranking job postings, you analyze job data to find the best matches for the user. "
        "You use the given search and rank tools to rank options based on user preferences and constraints."
    ),
    tools=[search_tool],
    llm=select_model(model_name = "llama-3.1-8b-instant", max_tokens = 2000),
    allow_delegation=False,
    verbose=True
)

response_agent = Agent(
    role="Response Agent",
    goal=("Given the list of jobs provided by the search_and_ranking_agent, communicate the options to the users in a polite and professional manner."
    ),
    backstory=(
        "You are a polite and helpful communicator that clearly gives the user the most relevant job postings that matches the user's requirements."
    ),
    llm=select_model(model_name = "llama-3.1-8b-instant", max_tokens = 2000),
    allow_delegation=False,
    verbose=True
)

process_query = Task(
    description=(
        "Process the user query to extract and clean details like location, job title, "
        "salary, and company. The user query is: {user_query}. Return a structured query."
        "If user query is not asking for a job search, stop processing."
    ),
    expected_output=('A structured query in JSON format.'),

    agent = query_processing_agent,
    verbose = True
)

retrieve_and_rank = Task(
    description=(
        "1. Retrieve job postings using the structured query provided by query_processing_agent using the search tool **once**. Must include at least 5 key words: location, job title, company, salary, and salary range from user query. "
        "2. After retrieving the results, **stop searching** and do not perform any additional searches. "
        "3. Use the ranking_tool to rank the job postings."
        "4. Return the ranked list and **Stop task**."
    ),
    expected_output=(
        "A ranked list of job postings and URLs, sorted by their score. If scores are 0, list alphabetically."
    ),
    tools=[search_tool, ranking_tool],
    agent = search_and_ranking_agent,
    verbose = True
)

generate_final_response = Task(
    description=(
        "Generate a user-friendly response based on the ranked job postings created by search_and_ranking_agent."
        "Break the Json list apart and turn it into a numbered list in a string format."
        "The response should be clear, concise, and easy to understand."
        "After finishing, **Stop task**."
    ),
    expected_output=("A list of the top ranked and msot relevant jobs with the location, company, job title, stated salary, and URL link."),
    agent = response_agent,
    verbose = True
)

crew = Crew(
    agents=[query_processing_agent,
            search_and_ranking_agent, response_agent],

    tasks=[process_query,
           retrieve_and_rank, generate_final_response],

    verbose=2,
    # llm=select_model(model_name = "llama3-70b-8192")
	#  memory=True
)
role="Conversational Input Agent"
goal="Capture real-time voice input from the user, transcribe it into text, and pass the transcribed text to other agents for further processing."
backstory="You are a highly skilled voice input processor. Your expertise lies in capturing audio, transcribing it accurately, and ensuring the transcribed text is ready for downstream tasks."

class CentralController:
    def __init__(self, crew):
        """
        Initializes the Central Controller with the CrewAI crew.
        Parameters:
            crew: The CrewAI crew managing the agents and tasks.
        """
        self.crew = crew
        self.whisper_agent = WhisperAgent(role="assistant", goal="transcribe", backstory="none")

    def handle_user_query(self, user_query):
        """
         Handles the entire workflow for a user query using the CrewAI crew.
        Parameters:
            user_query (dict): The raw user query.
        Returns:
            str: The final response to the user.
        """
        print("Handling user query...")

        result = self.crew.kickoff(inputs={"user_query": user_query})
        return result

    def handle_voice_query(self, audio_path):
        """
         Handles the entire workflow for a user query using the CrewAI crew.
        Parameters:
            user_query (dict): The raw user query.
        Returns:
            str: The final response to the user.
        """
        print("Handling voice query...")
        transcribed_text = self.whisper_agent.transcribe_audio(audio_path)

        result = self.crew.kickoff(inputs={"user_query": transcribed_text})
        return result

!pip install fastapi uvicorn nest-asyncio pyngrok python-multipart

import uvicorn
from pyngrok import ngrok
import threading
import time
import os
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

central_controller = CentralController(crew)

app = FastAPI()
templates = Jinja2Templates(directory="/content/drive/My Drive/Colab Notebooks/templates")

# Endpoint to handle voice queries
@app.post("/search_voice", response_class=HTMLResponse)
async def search_jobs_voice(request: Request, voice_file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{voice_file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(voice_file.file.read())

    # Pass the voice file to the Voice Capture Agent for transcription
    results = central_controller.handle_voice_query(temp_file_path)

    # Clean up the temporary file
    os.remove(temp_file_path)

    return templates.TemplateResponse("index.html", {"request": request, "results": results})

@app.post("/search", response_class=HTMLResponse)
async def search_jobs(request: Request, query: str = Form(...)):
    results = central_controller.handle_user_query({"text": query})
    return templates.TemplateResponse("index.html", {"request": request, "results": results})

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": None})

def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Set your ngrok authtoken
ngrok.set_auth_token("2tm4fEcmxh7QMddWUxnhD000qUW_EHt7ynH8dwbekgaomqv1")  # Replace with your actual authtoken

# Close all existing tunnels to avoid hitting the limit
ngrok.kill()

# Set up ngrok
public_url = ngrok.connect(8000).public_url
print("Public URL:", public_url)

# Start Uvicorn in a background thread
uvicorn_thread = threading.Thread(target=run_uvicorn, daemon=True)
uvicorn_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")