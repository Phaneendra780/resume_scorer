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

# Custom CSS for beautiful animations and graphics
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #000000;
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
        color: white;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        animation: fadeIn 0.8s ease-out;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .main-header p {
        margin: 15px 0 0 0;
        font-size: 1.3rem;
        opacity: 0.95;
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
    
    /* Card styling */
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
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
    }
    
    .section-header {
        color: #2c3e50;
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
        color: white;
        margin: 10px 0;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        animation: fadeIn 1s ease-out;
        transition: all 0.3s ease;
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
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.95;
        text-transform: uppercase;
        letter-spacing: 1px;
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
        color: white;
        font-weight: 700;
        transition: width 1.5s ease-out;
        animation: slideIn 1s ease-out;
    }
    
    /* Strength and weakness cards */
    .strength-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        animation: slideIn 0.6s ease-out;
        transition: all 0.3s ease;
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
    }
    
    .weakness-card:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 15px rgba(255, 193, 7, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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
        color: white;
    }
    
    .ats-medium {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        color: white;
    }
    
    .ats-low {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
    }
    
    /* Keywords styling */
    .keyword-tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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
        color: white;
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
        color: #856404;
        font-size: 1.2rem;
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
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

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
Analyze the uploaded resume and provide a comprehensive evaluation with the following structure:

*Overall Score:* <score out of 100>

*ATS Compatibility:* <High/Medium/Low with explanation>

*Section Scores:*
- Format & Structure: <score>/100
- Content Quality: <score>/100
- Keyword Optimization: <score>/100
- Experience Details: <score>/100
- Skills & Education: <score>/100

*Strengths:* <list 5-7 specific strengths found in the resume>

*Areas for Improvement:* <list 5-7 specific actionable improvements>

*Keywords Present:* <list important keywords found in the resume>

*Missing Keywords:* <list important industry keywords that should be added>

*Specific Recommendations:*
<Provide 3-5 detailed, actionable recommendations for improvement>

*Industry Alignment:* <Assess how well the resume aligns with modern industry standards>

Be specific, constructive, and actionable in your feedback. Focus on helping the candidate succeed.
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            instructions=INSTRUCTIONS,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
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

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk."""
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        with NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        return temp_path
    except Exception as e:
        st.error(f"💾 Error saving uploaded file: {e}")
        return None

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
            section_pattern = r"\*([\w\s&]+):\*(.*?)(?=\*[\w\s&]+:\*|$)"
            matches = re.findall(section_pattern, analysis_results, re.DOTALL | re.IGNORECASE)
            
            if matches:
                for section_title, section_content in matches:
                    content.append(Paragraph(f"<b>{section_title.strip()}</b>", heading_style))
                    
                    paragraphs = section_content.strip().split("\n")
                    for para in paragraphs:
                        if para.strip():
                            clean_para = para.strip().replace('<', '&lt;').replace('>', '&gt;')
                            content.append(Paragraph(clean_para, normal_style))
                    
                    content.append(Spacer(1, 0.2*inch))
        
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
        
        if st.session_state.analysis_results:
            analysis_text = st.session_state.analysis_results
            
            # Extract overall score
            score_match = re.search(r"\*Overall Score:\*\s*(\d+)", analysis_text, re.IGNORECASE)
            overall_score = int(score_match.group(1)) if score_match else 75
            
            # Display score circle
            display_score_circle(overall_score)
            
            # Extract ATS compatibility
            ats_match = re.search(r"\*ATS Compatibility:\*\s*(\w+)", analysis_text, re.IGNORECASE)
            ats_level = ats_match.group(1) if ats_match else "Medium"
            
            ats_class = "ats-high" if ats_level.lower() == "high" else \
                       "ats-medium" if ats_level.lower() == "medium" else "ats-low"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <span class="ats-badge {ats_class}">🎯 ATS Compatibility: {ats_level}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Section scores
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📈 Detailed Scores</div>', unsafe_allow_html=True)
            
            section_scores = {
                "Format & Structure": 0,
                "Content Quality": 0,
                "Keyword Optimization": 0,
                "Experience Details": 0,
                "Skills & Education": 0
            }
            
            for section_name in section_scores.keys():
                pattern = rf"{re.escape(section_name)}:\s*(\d+)"
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    section_scores[section_name] = int(match.group(1))
            
            for section_name, score in section_scores.items():
                st.markdown(f"**{section_name}**")
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
                
                strengths_match = re.search(r"\*Strengths:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
                if strengths_match:
                    strengths_text = strengths_match.group(1).strip()
                    strengths = [s.strip() for s in strengths_text.split('\n') if s.strip() and not s.strip().startswith('*')]
                    
                    for strength in strengths[:7]:
                        if strength:
                            clean_strength = strength.lstrip('-•').strip()
                            st.markdown(f"""
                            <div class="strength-card">
                                ✅ {clean_strength}
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">🎯 Improvements</div>', unsafe_allow_html=True)
                
                improvements_match = re.search(r"\*Areas for Improvement:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
                if improvements_match:
                    improvements_text = improvements_match.group(1).strip()
                    improvements = [i.strip() for i in improvements_text.split('\n') if i.strip() and not i.strip().startswith('*')]
                    
                    for improvement in improvements[:7]:
                        if improvement:
                            clean_improvement = improvement.lstrip('-•').strip()
                            st.markdown(f"""
                            <div class="weakness-card">
                                ⚠️ {clean_improvement}
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Keywords Analysis
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">🔑 Keyword Analysis</div>', unsafe_allow_html=True)
            
            # Keywords present
            st.markdown("**✅ Keywords Found in Your Resume:**")
            keywords_match = re.search(r"\*Keywords Present:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                keywords = [k.strip() for k in keywords_text.replace('\n', ',').split(',') if k.strip() and not k.strip().startswith('*')]
                
                keywords_html = ""
                for keyword in keywords[:10]:
                    if keyword:
                        clean_keyword = keyword.lstrip('-•').strip()
                        keywords_html += f'<span class="keyword-tag">{clean_keyword}</span>'
                
                if keywords_html:
                    st.markdown(keywords_html, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Missing keywords
            st.markdown("**❌ Important Keywords to Add:**")
            missing_match = re.search(r"\*Missing Keywords:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
            if missing_match:
                missing_text = missing_match.group(1).strip()
                missing_keywords = [m.strip() for m in missing_text.replace('\n', ',').split(',') if m.strip() and not m.strip().startswith('*')]
                
                missing_html = ""
                for keyword in missing_keywords[:10]:
                    if keyword:
                        clean_keyword = keyword.lstrip('-•').strip()
                        missing_html += f'<span class="missing-keyword-tag">{clean_keyword}</span>'
                
                if missing_html:
                    st.markdown(missing_html, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Specific Recommendations
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">💡 Specific Recommendations</div>', unsafe_allow_html=True)
            
            recommendations_match = re.search(r"\*Specific Recommendations:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
            if recommendations_match:
                recommendations_text = recommendations_match.group(1).strip()
                recommendations = [r.strip() for r in recommendations_text.split('\n') if r.strip() and not r.strip().startswith('*')]
                
                for i, recommendation in enumerate(recommendations[:5], 1):
                    if recommendation:
                        clean_rec = recommendation.lstrip('-•').strip()
                        st.markdown(f"""
                        <div class="weakness-card">
                            <strong>{i}.</strong> {clean_rec}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Industry Alignment
            industry_match = re.search(r"\*Industry Alignment:\*(.*?)(?=\*[\w\s&]+:\*|$)", analysis_text, re.DOTALL | re.IGNORECASE)
            if industry_match:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">🏢 Industry Alignment</div>', unsafe_allow_html=True)
                industry_text = industry_match.group(1).strip()
                st.markdown(f"<p style='font-size: 1.1rem; line-height: 1.6;'>{industry_text}</p>", unsafe_allow_html=True)
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
                    <p style="color: #666; font-size: 1.1rem; line-height: 1.6;">
                        Upload your resume and click 'Analyze My Resume' to receive:
                    </p>
                    <div style="text-align: left; max-width: 400px; margin: 20px auto;">
                        <p>✅ Overall score out of 100</p>
                        <p>✅ ATS compatibility rating</p>
                        <p>✅ Section-by-section breakdown</p>
                        <p>✅ Identified strengths</p>
                        <p>✅ Areas for improvement</p>
                        <p>✅ Keyword analysis</p>
                        <p>✅ Actionable recommendations</p>
                        <p>✅ Industry alignment assessment</p>
                        <p>✅ Downloadable PDF report</p>
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
                <p style="color: #666;">Customize your resume for each position by incorporating job-specific keywords and requirements.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 style="color: #667eea;">Quantify Achievements</h3>
                <p style="color: #666;">Use numbers, percentages, and metrics to demonstrate your impact and accomplishments.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h3 style="color: #667eea;">Keep It Updated</h3>
                <p style="color: #666;">Regular updates ensure your resume reflects your latest skills and achievements.</p>
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
