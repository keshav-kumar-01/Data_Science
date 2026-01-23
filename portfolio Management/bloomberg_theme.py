"""
Bloomberg Terminal Theme for Streamlit
Dark theme with signature Bloomberg colors and professional styling
"""

bloomberg_theme = """
<style>
/* Bloomberg Terminal Dark Theme */
:root {
    --bloomberg-black: #000000;
    --bloomberg-orange: #FF6B00;
    --bloomberg-blue: #0066CC;
    --bloomberg-green: #00FF00;
    --bloomberg-red: #FF0000;
    --bloomberg-gray: #1A1A1A;
    --bloomberg-light-gray: #2D2D2D;
}

/* Main app background */
.stApp {
    background-color: var(--bloomberg-black) !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: var(--bloomberg-gray) !important;
    border-right: 2px solid var(--bloomberg-orange);
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* Headers with Bloomberg orange accent */
h1, h2, h3 {
    color: var(--bloomberg-orange) !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    border-bottom: 2px solid var(--bloomberg-orange);
    padding-bottom: 10px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bloomberg-gray);
    border-bottom: 2px solid var(--bloomberg-orange);
}

.stTabs [data-baseweb="tab"] {
    color: #CCCCCC !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
    background-color: var(--bloomberg-gray);
    border: 1px solid #333333;
}

.stTabs [aria-selected="true"] {
    background-color: var(--bloomberg-orange) !important;
    color: #000000 !important;
}

/* Metric cards */
[data-testid="stMetricValue"] {
    font-family: 'Courier New', monospace !important;
    font-size: 32px !important;
    font-weight: bold !important;
    color: var(--bloomberg-orange) !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'Courier New', monospace !important;
}

/* Data tables */
.dataframe {
    background-color: var(--bloomberg-light-gray) !important;
    color: #00FF00 !important;
    font-family: 'Courier New', monospace !important;
    border: 1px solid var(--bloomberg-orange) !important;
}

.dataframe th {
    background-color: var(--bloomberg-orange) !important;
    color: #000000 !important;
    font-weight: bold !important;
}

.dataframe td {
    border: 1px solid #333333 !important;
}

/* Text */
p, span, div, label {
    color: #CCCCCC !important;
    font-family: Arial, sans-serif !important;
}

/* Buttons */
button[kind="primary"], button[kind="secondary"] {
    background-color: var(--bloomberg-orange) !important;
    color: #000000 !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
    border: none !important;
    border-radius: 0px !important;
    text-transform: uppercase !important;
}

button[kind="primary"]:hover, button[kind="secondary"]:hover {
    background-color: #FF8C33 !important;
    box-shadow: 0 0 10px var(--bloomberg-orange);
}

/* Input fields */
input, textarea, select {
    background-color: var(--bloomberg-light-gray) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--bloomberg-orange) !important;
    font-family: 'Courier New', monospace !important;
}

/* Progress bar */
.stProgress > div > div {
    background-color: var(--bloomberg-orange) !important;
}

/* Success/Warning/Error messages */
.stSuccess {
    background-color: rgba(0, 255, 0, 0.1) !important;
    border-left: 4px solid var(--bloomberg-green) !important;
    color: var(--bloomberg-green) !important;
}

.stWarning {
    background-color: rgba(255, 107, 0, 0.1) !important;
    border-left: 4px solid var(--bloomberg-orange) !important;
    color: var(--bloomberg-orange) !important;
}

.stError {
    background-color: rgba(255, 0, 0, 0.1) !important;
    border-left: 4px solid var(--bloomberg-red) !important;
    color: var(--bloomberg-red) !important;
}

.stInfo {
    background-color: rgba(0, 102, 204, 0.1) !important;
    border-left: 4px solid var(--bloomberg-blue) !important;
    color: #66B3FF !important;
}

/* Spinner with Bloomberg branding */
.stSpinner > div {
    border-top-color: var(--bloomberg-orange) !important;
}

/* Cards/Containers */
[data-testid="stVerticalBlock"] > div {
    background-color: var(--bloomberg-gray);
    border: 1px solid #333333;
    border-radius: 0px;
    padding: 15px;
    margin: 5px 0;
}

/* Numbers should be monospace and bright */
.stMetricValue, .stDataFrame td, code {
    font-family: 'Courier New', monospace !important;
    color: #00FF00 !important;
}

/* Download button special styling */
[data-testid="stDownloadButton"] button {
    background-color: var(--bloomberg-blue) !important;
    color: #FFFFFF !important;
}

/* Plotly charts dark theme sync */
.js-plotly-plot {
    background-color: transparent !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    background-color: var(--bloomberg-gray);
}

::-webkit-scrollbar-thumb {
    background-color: var(--bloomberg-orange);
    border-radius: 0px;
}

/* Title bar effect */
.main .block-container {
    padding-top: 2rem;
    border-top: 4px solid var(--bloomberg-orange);
}

/* Ticker feed effect */
@keyframes ticker-scroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

.ticker-tape {
    background-color: var(--bloomberg-orange);
    color: #000000;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    padding: 5px;
    overflow: hidden;
    white-space: nowrap;
}

.ticker-content {
    display: inline-block;
    animation: ticker-scroll 30s linear infinite;
}
</style>
"""

def inject_bloomberg_theme():
    """Inject Bloomberg Terminal theme into Streamlit app"""
    import streamlit as st
    st.markdown(bloomberg_theme, unsafe_allow_html=True)
