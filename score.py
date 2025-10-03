import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.units import inch
from datetime import datetime
import re
import PyPDF2
import docx

# Set page configuration
st.set_page_config(
    page_title="ResumeScore - AI Resume Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📄"
)

# Custom CSS for beautiful animations and graphics - FIXED TEXT COLOR TO BLACK
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* FORCE BLACK TEXT COLOR */
    .stApp, .stApp p, .stApp div, .stApp span, .stApp li {
        color: #000000 !important;
    }
    
    /* Animated background */
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-size: 200% 200%;
        animation: gradient 15s ease infinite;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        color: white !important;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        animation: fadeIn 0.8s ease-out;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        animation: pulse 2s ease-in-out infinite;
        color: white !important;
    }
    
    .main-header p {
        margin: 15px 0 0 0;
        font-size: 1.3rem;
        opacity: 0.95;
        color: white !important;
    }
    
    /* Score circle styling */
    .score-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px auto;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        animation: float 3s ease-in-out infinite;
        position: relative;
        overflow: hidden;
    }
    
    .score-circle::before {
        content: '';
        position: absolute;
        width: 180px;
        height: 180px;
        background: white;
        border-radius: 50%;
    }
    
    .score-value {
        position: relative;
        z-index: 1;
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Card styling - BLACK TEXT */
    .info-card {
        background: rgba(255, 255, 255, 0.95);
        border: none;
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    .info-card * {
        color: #000000 !important;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
    }
    
    .section-header {
        color: #2c3e50 !important;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 4px solid;
        border-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%) 1;
        animation: slideIn 0.8s ease-out;
    }
    
    /* Upload section */
    .upload-section {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 50px;
        text-align: center;
        margin: 30px 0;
        transition: all 0.3s ease;
        animation: fadeIn 0.8s ease-out;
    }
    
    .upload-section:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        transform: scale(1.02);
    }
    
    /* Score metrics */
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        color: white !important;
        margin: 10px 0;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        animation: fadeIn 1s ease-out;
        transition: all 0.3s ease;
    }
    
    .metric-box * {
        color: white !important;
    }
    
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.5);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        color: white !important;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.95;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: white !important;
    }
    
    /* Progress bars */
    .progress-bar {
        width: 100%;
        height: 30px;
        background: #e0e0e0;
        border-radius: 15px;
        overflow: hidden;
        margin: 15px 0;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 15px;
        color: white !important;
        font-weight: 700;
        transition: width 1.5s ease-out;
        animation: slideIn 1s ease-out;
    }
    
    /* Strength and weakness cards - BLACK TEXT */
    .strength-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        animation: slideIn 0.6s ease-out;
        transition: all 0.3s ease;
        color: #000000 !important;
    }
    
    .strength-card:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
    }
    
    .weakness-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ffc107;
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        animation: slideIn 0.6s ease-out;
        transition: all 0.3s ease;
        color: #000000 !important;
    }
    
    .weakness-card:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 15px rgba(255, 193, 7, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 30px;
        padding: 18px 40px;
        font-size: 1.2rem;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.6);
    }
    
    /* ATS compatibility badge */
    .ats-badge {
        display: inline-block;
        padding: 15px 30px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 15px 0;
        animation: pulse 2s ease-in-out infinite;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .ats-high {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white !important;
    }
    
    .ats-medium {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        color: white !important;
    }
    
    .ats-low {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white !important;
    }
    
    /* Keywords styling */
    .keyword-tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 8px 20px;
        border-radius: 20px;
        margin: 5px;
        font-weight: 600;
        animation: fadeIn 0.6s ease-out;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .keyword-tag:hover {
        transform: scale(1.1);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5);
    }
    
    .missing-keyword-tag {
        display: inline-block;
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white !important;
        padding: 8px 20px;
        border-radius: 20px;
        margin: 5px;
        font-weight: 600;
        animation: fadeIn 0.6s ease-out;
        box-shadow: 0 3px 10px rgba(220, 53, 69, 0.3);
        transition: all 0.3s ease;
    }
    
    .missing-keyword-tag:hover {
        transform: scale(1.1);
        box-shadow: 0 5px 15px rgba(220, 53, 69, 0.5);
    }
    
    /* Disclaimer box */
    .disclaimer {
        background: linear-gradient(135deg, rgba(255, 243, 205, 0.9) 0%, rgba(255, 234, 167, 0.9) 100%);
        border: 2px solid #ffc107;
        border-radius: 15px;
        padding: 25px;
        margin: 25px 0;
        border-left: 6px solid #ffc107;
        animation: fadeIn 1s ease-out;
    }
    
    .disclaimer strong {
        color: #856404 !important;
        font-size: 1.2rem;
    }
    
    .disclaimer * {
        color: #000000 !important;
    }
    
    /* Icon styling */
    .icon-bounce {
        animation: float 2s ease-in-out infinite;
        display: inline-block;
    }
    
    /* Section divider */
    .section-divider {
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
        margin: 30px 0;
        animation: slideIn 1s ease-out;
    }
    
    /* Loading animation */
    .loading-spinner {
        border: 5px solid #f3f3f3;
        border-top: 5px solid #667eea;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: fadeIn 0.8s ease-out;
    }
    
    .feature-card * {
        color: #000000 !important;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 15px;
        animation: float 3s ease-in-out infinite;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .score-circle {
            width: 150px;
            height: 150px;
        }
        
        .score-value {
            font-size: 3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# API Keys
# NOTE: Replace 'st.secrets.get("TAVILY_API_KEY")' and 'st.secrets.get("GOOGLE_API_KEY")' with your actual keys
# or ensure they are correctly set in your Streamlit secrets file.
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "YOUR_TAVILY_API_KEY") # Placeholder for local testing
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY") # Placeholder for local testing

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY or TAVILY_API_KEY == "YOUR_TAVILY_API_KEY" or GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY":
     st.error("🔑 API keys are missing or set to placeholders. Please set them correctly.")
     # st.stop() # Commented out for giving the user a chance to see the code structure, uncomment in production

SYSTEM_PROMPT = """
You are an expert resume analyzer and career consultant with deep knowledge in ATS (Applicant Tracking Systems), 
recruitment practices, and professional resume writing. Your role is to analyze resumes comprehensively and provide 
actionable feedback to help candidates improve their job application success rate.

Analyze resumes across multiple dimensions:
1. Format and structure
2. Content quality and relevance
3. ATS compatibility
4. Keyword optimization
5. Experience presentation
6. Skills and education
7. Overall professional impact
"""

INSTRUCTIONS = """
Analyze the uploaded resume and provide a comprehensive evaluation with EXACTLY this structure:

**Overall Score:** <score out of 100>

**ATS Compatibility:** <High/Medium/Low with brief explanation>

**Section Scores:**
- Format & Structure: <score>/100
- Content Quality: <score>/100
- Keyword Optimization: <score>/100
- Experience Details: <score>/100
- Skills & Education: <score>/100

**Strengths:**
- <strength 1>
- <strength 2>
- <strength 3>
- <strength 4>
- <strength 5>

**Areas for Improvement:**
- <improvement 1>
- <improvement 2>
- <improvement 3>
- <improvement 4>
- <improvement 5>

**Keywords Present:** <keyword1>, <keyword2>, <keyword3>, <keyword4>, <keyword5>

**Missing Keywords:** <missing keyword1>, <missing keyword2>, <missing keyword3>, <missing keyword4>

**Specific Recommendations:**
1. <detailed recommendation 1>
2. <detailed recommendation 2>
3. <detailed recommendation 3>

**Industry Alignment:** <assessment of how well the resume aligns with modern industry standards>

IMPORTANT: Use exactly this format with these exact headers using ** for bold. List items with dashes (-) or numbers (1., 2.). Be specific and actionable.
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(model="gemini-2.5-flash", api_key=GOOGLE_API_KEY), # Changed model ID for general availability
            system_prompt=SYSTEM_PROMPT,
            instructions=INSTRUCTIONS,
            # tools=[TavilyTools(api_key=TAVILY_API_KEY)], # Tavily is often not needed for resume analysis
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        pdf_file.seek(0)
        # Use PdfReader, which is the updated version for PyPDF2.PdfFileReader
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() if page.extract_text() else ""
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file."""
    try:
        docx_file.seek(0)
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {e}")
        return None

def analyze_resume(resume_text):
    """Analyze resume using AI agent."""
    agent = get_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔍 Analyzing your resume with AI... This may take a moment..."):
            response = agent.run(
                f"Analyze this resume comprehensively and provide detailed feedback:\n\n{resume_text}"
            )
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error analyzing resume: {e}")
        return None

def parse_analysis_results(analysis_text):
    """
    Parse the analysis results to extract structured data.
    Enhanced regex for better robustness against multi-line and variable AI output.
    """
    results = {
        'overall_score': 75,
        'ats_level': 'Medium',
        'ats_explanation': '',
        'section_scores': {
            'Format & Structure': 75,
            'Content Quality': 75,
            'Keyword Optimization': 75,
            'Experience Details': 75,
            'Skills & Education': 75
        },
        'strengths': [],
        'improvements': [],
        'keywords_present': [],
        'missing_keywords': [],
        'recommendations': [],
        'industry_alignment': ''
    }
    
    if not analysis_text:
        return results
    
    # Helper to find text blocks between two headers
    def get_text_block(start_header, end_header, text):
        # Use re.DOTALL to match across newlines
        pattern = rf"\*\*{re.escape(start_header)}:\*\*\s*(.*?)(?=\n\*\*{re.escape(end_header)}:\*\*|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    # --- 1. Simple Value Extractions (Score, ATS, Industry Alignment) ---
    
    # Extract Overall Score
    score_match = re.search(r"\*\*Overall Score:\*\*\s*(\d+)", analysis_text, re.IGNORECASE)
    if score_match:
        results['overall_score'] = int(score_match.group(1))

    # Extract ATS Compatibility and Explanation
    ats_match = re.search(r"\*\*ATS Compatibility:\*\*\s*(\w+)(?:\s*[-–—:]\s*(.+?))?(?=\n\*\*|\n\n|$)", analysis_text, re.IGNORECASE | re.DOTALL)
    if ats_match:
        results['ats_level'] = ats_match.group(1).strip()
        if ats_match.group(2):
            results['ats_explanation'] = ats_match.group(2).strip()

    # Extract Industry Alignment
    alignment_match = re.search(r"\*\*Industry Alignment:\*\*\s*(.+?)(?=\n\*\*|\n\n|\Z)", analysis_text, re.IGNORECASE | re.DOTALL)
    if alignment_match:
        results['industry_alignment'] = alignment_match.group(1).strip()
    
    # Extract Section Scores
    for section in results['section_scores'].keys():
        patterns = [
            rf"{re.escape(section)}:\s*(\d+)",
            rf"-\s*{re.escape(section)}:\s*(\d+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                results['section_scores'][section] = int(match.group(1))
                break

    # --- 2. List Extractions (Strengths, Improvements, Recommendations) ---
    
    # Extract Strengths
    strengths_block = get_text_block("Strengths", "Areas for Improvement", analysis_text)
    if strengths_block:
        # Split by dash, bullet, or number, and strip whitespace/empty lines
        results['strengths'] = [s.strip().lstrip('-•*').strip() 
                                for s in re.split(r'[\s]*[-•*1-9]\s*', strengths_block) if s.strip()]

    # Extract Areas for Improvement
    improvements_block = get_text_block("Areas for Improvement", "Keywords Present", analysis_text)
    if improvements_block:
        results['improvements'] = [i.strip().lstrip('-•*').strip() 
                                   for i in re.split(r'[\s]*[-•*1-9]\s*', improvements_block) if i.strip()]

    # Extract Specific Recommendations
    recommendations_block = get_text_block("Specific Recommendations", "Industry Alignment", analysis_text)
    if recommendations_block:
        # Split by a number followed by a period and space
        results['recommendations'] = [r.strip() 
                                      for r in re.findall(r'\d+\.\s*(.+)', recommendations_block) if r.strip()]

    # --- 3. Keywords Extractions (Keywords Present, Missing Keywords) ---

    # Extract Keywords Present (Robust comma or newline split)
    keywords_present_block = get_text_block("Keywords Present", "Missing Keywords", analysis_text)
    if keywords_present_block:
        # Split by comma OR newline and clean up
        all_keywords = re.split(r'[\s,]+', keywords_present_block)
        results['keywords_present'] = [k.strip() for k in all_keywords if k.strip()]

    # Extract Missing Keywords (Robust comma or newline split)
    missing_keywords_block = get_text_block("Missing Keywords", "Specific Recommendations", analysis_text)
    if missing_keywords_block:
        # Split by comma OR newline and clean up
        all_missing_keywords = re.split(r'[\s,]+', missing_keywords_block)
        results['missing_keywords'] = [k.strip() for k in all_missing_keywords if k.strip()]
    
    return results

def create_pdf_report(analysis_results, filename):
    """Create a PDF report of the resume analysis."""
    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        content = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=20,
            alignment=1,
            spaceAfter=12,
            textColor=colors.HexColor('#667eea')
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=6
        )
        
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=11,
            leading=14
        )
        
        # Title
        content.append(Paragraph("📄 Resume Score Analysis Report", title_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Date
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"Generated on: {current_datetime}", normal_style))
        content.append(Paragraph(f"Resume File: {filename}", normal_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Analysis results
        if analysis_results:
            content.append(Paragraph(f"<b>Analysis Results</b>", heading_style))
            # Basic cleanup for PDF presentation
            clean_text = analysis_results.replace('<', '&lt;').replace('>', '&gt;').replace('*', '') 
            paragraphs = clean_text.split("\n")
            for para in paragraphs:
                if para.strip():
                    content.append(Paragraph(para.strip(), normal_style))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 ResumeScore - AI Resume Analyzer | Powered by Gemini AI + Tavily", 
                                 ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        pdf.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_score_circle(score):
    """Display animated score circle."""
    color = "linear-gradient(135deg, #28a745 0%, #20c997 100%)" if score >= 80 else \
            "linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)" if score >= 60 else \
            "linear-gradient(135deg, #dc3545 0%, #c82333 100%)"
    
    st.markdown(f"""
    <div class="score-circle" style="background: {color};">
        <div class="score-value">{score}</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'resume_filename' not in st.session_state:
        st.session_state.resume_filename = None
    if 'parsed_results' not in st.session_state:
        st.session_state.parsed_results = None

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📄 ResumeScore AI</h1>
        <p>Professional Resume Analysis & Optimization Platform</p>
        <p>🚀 Powered by Advanced AI • Get Instant Feedback • Beat ATS Systems</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        <strong>💡 PROFESSIONAL GUIDANCE</strong><br>
        ResumeScore provides AI-powered analysis to help improve your resume. While our analysis is comprehensive, 
        we recommend consulting with career professionals for personalized advice. This tool is designed to complement, 
        not replace, professional career guidance.
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📤 Upload Your Resume</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Upload your resume in PDF or DOCX format for comprehensive AI analysis"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / 1024
            st.success(f"✅ **{uploaded_file.name}** • {file_size:.1f} KB uploaded successfully!")
            
            # Display file icon
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div class="feature-icon">📄</div>
                <p style="color: #667eea; font-weight: 600;">Ready for analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze button
        if uploaded_file:
            if st.button("🚀 Analyze My Resume", use_container_width=True):
                st.session_state.analyze_clicked = True
                st.session_state.resume_filename = uploaded_file.name
                
                # Extract text from resume
                resume_text = None
                if uploaded_file.name.endswith('.pdf'):
                    resume_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.name.endswith('.docx'):
                    resume_text = extract_text_from_docx(uploaded_file)
                
                if resume_text:
                    # Analyze resume
                    analysis_result = analyze_resume(resume_text)
                    
                    if analysis_result:
                        st.session_state.analysis_results = analysis_result
                        st.session_state.parsed_results = parse_analysis_results(analysis_result)
                        st.success("✅ Analysis completed successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed. Please try again.")
                else:
                    st.error("❌ Could not extract text from resume. Please check the file format.")
        
        # Features section
        if not st.session_state.analysis_results:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-header">✨ Why Choose ResumeScore?</div>', unsafe_allow_html=True)
            
            features = [
                ("🎯", "ATS Optimization", "Ensure your resume passes Applicant Tracking Systems"),
                ("🔍", "Deep Analysis", "Comprehensive review of format, content, and keywords"),
                ("⚡", "Instant Results", "Get detailed feedback in seconds"),
                ("📊", "Actionable Insights", "Specific recommendations for improvement"),
            ]
            
            for icon, title, desc in features:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <h3 style="color: #667eea; margin-bottom: 10px;">{title}</h3>
                    <p style="color: #666;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        if st.session_state.analysis_results and st.session_state.parsed_results:
            parsed = st.session_state.parsed_results
            
            # Display score circle
            display_score_circle(parsed['overall_score'])
            
            # ATS Compatibility
            ats_class = "ats-high" if parsed['ats_level'].lower() == "high" else \
                         "ats-medium" if parsed['ats_level'].lower() == "medium" else "ats-low"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <span class="ats-badge {ats_class}">🎯 ATS Compatibility: {parsed['ats_level']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if parsed['ats_explanation']:
                st.markdown(f"""
                <div class="info-card">
                    <p style="color: #000000; text-align: center;"><strong>{parsed['ats_explanation']}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            # Section scores
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📈 Detailed Scores</div>', unsafe_allow_html=True)
            
            for section_name, score in parsed['section_scores'].items():
                st.markdown(f"<p style='color: #000000; font-weight: bold; margin-bottom: 5px;'>{section_name}</p>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {score}%;">{score}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Strengths and Improvements
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">💪 Strengths</div>', unsafe_allow_html=True)
                
                if parsed['strengths']:
                    for strength in parsed['strengths'][:7]:
                        if strength:
                            st.markdown(f"""
                            <div class="strength-card">
                                ✅ {strength}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #000000;'>No strengths extracted. Check raw analysis below.</p>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">🎯 Improvements</div>', unsafe_allow_html=True)
                
                if parsed['improvements']:
                    for improvement in parsed['improvements'][:7]:
                        if improvement:
                            st.markdown(f"""
                            <div class="weakness-card">
                                ⚠️ {improvement}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #000000;'>No improvements extracted. Check raw analysis below.</p>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Keywords Analysis
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">🔑 Keyword Analysis</div>', unsafe_allow_html=True)
            
            # Keywords present
            st.markdown("<p style='color: #000000; font-weight: bold;'>✅ Keywords Found in Your Resume:</p>", unsafe_allow_html=True)
            if parsed['keywords_present']:
                keywords_html = ""
                for keyword in parsed['keywords_present'][:10]:
                    if keyword:
                        keywords_html += f'<span class="keyword-tag">{keyword}</span>'
                
                if keywords_html:
                    st.markdown(keywords_html, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #000000;'>No keywords extracted.</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Missing keywords
            st.markdown("<p style='color: #000000; font-weight: bold;'>❌ Important Keywords to Add:</p>", unsafe_allow_html=True)
            if parsed['missing_keywords']:
                missing_html = ""
                for keyword in parsed['missing_keywords'][:10]:
                    if keyword:
                        missing_html += f'<span class="missing-keyword-tag">{keyword}</span>'
                
                if missing_html:
                    st.markdown(missing_html, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #000000;'>No missing keywords identified.</p>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Specific Recommendations
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">💡 Specific Recommendations</div>', unsafe_allow_html=True)
            
            if parsed['recommendations']:
                for i, recommendation in enumerate(parsed['recommendations'][:5], 1):
                    if recommendation:
                        st.markdown(f"""
                        <div class="weakness-card">
                            <strong style="color: #000000;">{i}.</strong> <span style="color: #000000;">{recommendation}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #000000;'>No specific recommendations extracted. Check raw analysis below.</p>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Industry Alignment
            if parsed['industry_alignment']:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">🏢 Industry Alignment</div>', unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.1rem; line-height: 1.6; color: #000000;'>{parsed['industry_alignment']}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # RAW ANALYSIS OUTPUT FOR DEBUGGING
            with st.expander("🔍 View Raw AI Analysis (for debugging)", expanded=False):
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown(f"<pre style='color: #000000; white-space: pre-wrap; word-wrap: break-word;'>{st.session_state.analysis_results}</pre>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Download PDF Report
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📥 Download Your Report</div>', unsafe_allow_html=True)
            
            pdf_bytes = create_pdf_report(
                st.session_state.analysis_results,
                st.session_state.resume_filename
            )
            
            if pdf_bytes:
                download_filename = f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.download_button(
                    label="📄 Download Detailed PDF Report",
                    data=pdf_bytes,
                    file_name=download_filename,
                    mime="application/pdf",
                    help="Download a comprehensive PDF report of your resume analysis",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # New Analysis Button
            if st.button("🔄 Analyze Another Resume", use_container_width=True):
                st.session_state.analysis_results = None
                st.session_state.parsed_results = None
                st.session_state.resume_filename = None
                st.session_state.analyze_clicked = False
                st.rerun()
        
        else:
            # Placeholder when no results
            st.markdown("""
            <div class="info-card">
                <div style="text-align: center; padding: 40px;">
                    <div class="feature-icon">📊</div>
                    <h3 style="color: #667eea; margin-bottom: 15px;">Ready to Analyze</h3>
                    <p style="color: #000000; font-size: 1.1rem; line-height: 1.6;">
                        Upload your resume and click 'Analyze My Resume' to receive:
                    </p>
                    <div style="text-align: left; max-width: 400px; margin: 20px auto;">
                        <p style="color: #000000;">✅ Overall score out of 100</p>
                        <p style="color: #000000;">✅ ATS compatibility rating</p>
                        <p style="color: #000000;">✅ Section-by-section breakdown</p>
                        <p style="color: #000000;">✅ Identified strengths</p>
                        <p style="color: #000000;">✅ Areas for improvement</p>
                        <p style="color: #000000;">✅ Keyword analysis</p>
                        <p style="color: #000000;">✅ Actionable recommendations</p>
                        <p style="color: #000000;">✅ Industry alignment assessment</p>
                        <p style="color: #000000;">✅ Downloadable PDF report</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Additional Tips Section
    if st.session_state.analysis_results:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📚 Pro Tips for Resume Success</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3 style="color: #667eea;">Tailor for Each Job</h3>
                <p style="color: #000000;">Customize your resume for each position by incorporating job-specific keywords and requirements.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 style="color: #667eea;">Quantify Achievements</h3>
                <p style="color: #000000;">Use numbers, percentages, and metrics to demonstrate your impact and accomplishments.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h3 style="color: #667eea;">Keep It Updated</h3>
                <p style="color: #000000;">Regular updates ensure your resume reflects your latest skills and achievements.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Key Metrics Section
    if not st.session_state.analysis_results:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 What Gets Measured</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">100</div>
                <div class="metric-label">Overall Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">5</div>
                <div class="metric-label">Section Scores</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">ATS</div>
                <div class="metric-label">Compatibility</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">AI</div>
                <div class="metric-label">Powered</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 30px; color: white; font-size: 1rem;">
        <p><strong>© 2025 ResumeScore AI - Professional Resume Analyzer</strong></p>
        <p>Powered by Gemini AI + Tavily | Built with ❤️ for Job Seekers</p>
        <p><em>Your success is our mission. Make every application count.</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
