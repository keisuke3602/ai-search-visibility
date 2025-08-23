from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
import os, json, datetime
from dotenv import load_dotenv

# ==========================================================================

from chatgpt_visibility.py import (
    ensure_client, query_openai_one, parse_model_output, detect_brands
)

load_dotenv()
app = Flask(__name__)

# ==========================================================================

