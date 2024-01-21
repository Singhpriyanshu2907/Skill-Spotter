import streamlit as st
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import spacy
from spacy.cli import download
download("en_core_web_sm")
from google.generativeai import configure, GenerativeModel


load_dotenv()  # Load all our environment variables

configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input):
    model = GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += str(page.extract_text())
    return text

def extract_name(resume_text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(resume_text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Candidate"

def extract_skills(resume_text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(resume_text)
    skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]
    return skills

def extract_projects(resume_text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(resume_text)
    projects = [chunk.text for chunk in doc.noun_chunks if "project" in chunk.root.text.lower()]
    return projects

def extract_experience(resume_text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(resume_text)
    experiences = [chunk.text for chunk in doc.noun_chunks if "experience" in chunk.root.text.lower()]
    return experiences

def generate_suggestions(job_description, missing_keywords):
    suggestions = []

    for keyword in missing_keywords:
        if keyword.lower() in job_description.lower():
            suggestions.append(f"Consider highlighting your experience with '{keyword}'.")

    return suggestions

def generate_analysis(candidate_name, skills, projects, experiences, missing_keywords):
    analysis = f"{candidate_name}, has demonstrated strong skills in {', '.join(skills)}. "
    analysis += f"Their projects showcase {', '.join(projects)}. "
    analysis += f"The candidate has valuable experience in {', '.join(experiences)}. "
    
    if missing_keywords:
        analysis += f"However, the resume lacks keywords related to {', '.join(missing_keywords)}, which are mentioned in the job description. "
        analysis += "The profile summary should be revised to highlight relevant skills and experiences, focusing on NLP, machine learning, and statistical analysis."
    else:
        analysis += "The resume aligns well with the job description, showcasing a strong match in skills and experiences."

    return analysis

# Prompt Template
input_prompt = """
Hey, Act like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of the tech field, software engineering, data science, data analyst,
and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive, and you should provide 
the best assistance for improving the resumes. Assign the percentage matching based 
on JD and the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
"""

# Streamlit app
st.title("🚀 Skill Spotter - Elevate Your Resume")
st.markdown(
    """
    Streamline your resume with the power of AI. Upload your resume and paste the job description to get personalized insights.
    """
)

uploaded_file = st.file_uploader("Upload Your Resume 📂", type="pdf", help="Please upload the pdf")

jd = st.text_area("Paste the Job Description 📄")

submit = st.button("Submit")

if submit:
    if uploaded_file is not None:
        text = input_pdf_text(uploaded_file)
        candidate_name = extract_name(text)
        skills = extract_skills(text)
        projects = extract_projects(text)
        experiences = extract_experience(text)

        prompt_input = input_prompt.format(text=text, jd=jd)
        response = get_gemini_response(prompt_input)

        try:
            parsed_response = json.loads(response)
            st.subheader("Model Output:")

            st.success(f"**JD Match:** {parsed_response['JD Match']}")

            if parsed_response['MissingKeywords']:
                st.warning("**Missing Keywords:**")
                for keyword in parsed_response['MissingKeywords']:
                    st.warning(f"- {keyword}")
                
                suggestions = generate_suggestions(jd, parsed_response['MissingKeywords'])
                st.subheader("Suggestions for CV Improvement:")
                for suggestion in suggestions:
                    st.success(f"- {suggestion}")

            else:
                st.success("**Missing Keywords:** None")

            st.markdown(f"**Profile Summary:** {candidate_name}, {parsed_response['Profile Summary']}")

            st.subheader("Analysis and Recommendations:")
            
            analysis = generate_analysis(candidate_name, skills, projects, experiences, parsed_response['MissingKeywords'])
            
            st.markdown(analysis)

        except json.JSONDecodeError:
            st.subheader("Error parsing the response. Please check the response format.")
