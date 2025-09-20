import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import os
import json
from dotenv import load_dotenv
import plotly.graph_objects as go
from helper import configure_genai, get_gemini_response, extract_pdf_text, prepare_prompt

def init_session_state():
    """Initialize session state variables."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def custom_css():
    """Injects custom CSS for styling the Streamlit app."""
    st.markdown("""
        <style>
            body {
                background-color: #f0f2f6;
            }
            .main .block-container {
                padding: 2rem;
                border-radius: 10px;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .stButton>button {
                color: #ffffff;
                background-color: #3498db;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 14px 0 rgba(0, 118, 255, 0.39);
            }
            .stButton>button:hover {
                background-color: #2980b9;
                box-shadow: 0 6px 20px 0 rgba(0, 118, 255, 0.23);
                transform: translateY(-2px);
            }
            .stTextArea textarea, .stFileUploader {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                background-color: #ffffff;
            }
            .css-1d391kg {
                background-color: #ffffff;
                border-right: 1px solid #e0e0e0;
            }
            .result-card {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border: 1px solid #e0e0e0;
            }
        </style>
    """, unsafe_allow_html=True)

def create_donut_chart(score):
    """Creates a full-circle donut chart with bright colors."""
    if not isinstance(score, (int, float)):
        return go.Figure()

    # Use brighter, more vibrant hex colors
    colors = ['#28a745', '#FF4136'] # Bright Green and Bright Red

    fig = go.Figure(data=[go.Pie(
        values=[score, 100 - score],
        labels=['Match', 'Gap'],
        hole=.7,
        marker_colors=colors,
        hoverinfo='none',
        textinfo='none',
        direction='clockwise',
        sort=False
    )])

    fig.update_layout(
        title={
            'text': 'Resume Match Score',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#2c3e50'}
        },
        annotations=[dict(
            text=f'<b>{score}%</b>',
            x=0.5,
            y=0.5,
            font_size=40,
            font_color='#2c3e50',
            showarrow=False
        )],
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(t=60, b=10, l=10, r=10)
    )
    return fig

def main():
    # Page configuration
    st.set_page_config(page_title="Smart ATS by TkReddy", page_icon="🎯", layout="wide")
    
    # Load environment variables and apply custom styles
    load_dotenv()
    custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Configure Generative AI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Please set the GOOGLE_API_KEY in your .env file")
        return
        
    try:
        configure_genai(api_key)
    except Exception as e:
        st.error(f"Failed to configure API: {str(e)}")
        return

    # --- Sidebar ---
    with st.sidebar:
        st.title("🎯 **Smart ATS**")
        st.subheader("About")
        st.info("""
            This tool helps you optimize your resume for Applicant Tracking Systems (ATS).
            - **Analyzes** resume-job description match.
            - **Identifies** missing keywords.
            - **Provides** actionable suggestions.
        """)
        add_vertical_space(5)
        st.write("Made with ❤️ by TkReddy🍏")

    # --- Main Content ---
    st.title("📄 Smart ATS Resume Analyzer")
    st.markdown("<h4>Optimize Your Resume for Any Job in Seconds</h4>", unsafe_allow_html=True)
    st.divider()

    # --- Input sections (one by one) ---
    jd = st.text_area(
        "📝 **Job Description**",
        height=250,
        placeholder="Paste the job description here...",
        help="Enter the complete job description for accurate analysis"
    )
    add_vertical_space(1)
    uploaded_file = st.file_uploader(
        "📁 **Your Resume (PDF)**",
        type="pdf",
        help="Upload your resume in PDF format (max 2MB)"
    )
    add_vertical_space(2)

    # Centered "Analyze" button
    _, col2, _ = st.columns([3, 2, 3])
    with col2:
        analyze_button = st.button("🚀 Analyze My Resume", use_container_width=True, disabled=st.session_state.processing)

    if analyze_button:
        if not jd:
            st.warning("Please provide a job description.")
        elif not uploaded_file:
            st.warning("Please upload your resume in PDF format.")
        else:
            st.session_state.processing = True
            try:
                with st.spinner("📊 Analyzing... This may take a moment."):
                    resume_text = extract_pdf_text(uploaded_file)
                    input_prompt = prepare_prompt(resume_text, jd)
                    response = get_gemini_response(input_prompt)
                    response_json = json.loads(response)
                
                st.toast('✨ Analysis Complete!', icon='🎉')
                
                # --- Display Results in a Card with Tabs ---
                with st.container():
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    
                    tab1, tab2, tab3 = st.tabs(["✅ **Match Score**", "🔑 **Keyword Analysis**", "📝 **Profile Summary**"])

                    with tab1:
                        match_percentage_str = response_json.get("JD Match", "0%")
                        try:
                            # ✅ Fix: handle both int and string values safely
                            if isinstance(match_percentage_str, int):
                                score_value = match_percentage_str
                            else:

                                score_value = int(str(match_percentage_str).strip('%'))
                            fig = create_donut_chart(score_value)
                            st.plotly_chart(fig, use_container_width=True)
                        except (ValueError, TypeError):
                            st.error("Could not parse the match score to display the chart.")
                            st.write(f"Raw Score Received: {match_percentage_str}")

                    with tab2:
                        st.subheader("Missing Keywords Analysis")
                        missing_keywords = response_json.get("MissingKeywords", [])
                        if missing_keywords:
                            st.warning("Consider adding these keywords to your resume:")
                            # Display keywords as a bulleted list
                            for keyword in missing_keywords:
                                st.markdown(f"- **{keyword}**")
                        else:
                            st.success("🎉 Excellent! No critical missing keywords found.")

                    with tab3:
                        st.subheader("Your Profile Summary & Suggestions")
                        st.info(response_json.get("Profile Summary", "No summary available"))
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("There was an issue decoding the response. The API might have returned an unexpected format.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                st.session_state.processing = False

if __name__ == "__main__":
    main()



