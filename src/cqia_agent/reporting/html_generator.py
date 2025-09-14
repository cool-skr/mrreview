import os
import base64
from datetime import datetime
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from ..analysis.models import Issue

def generate_html_report(issues: List[Issue], file_count: int, chart_path: Optional[str], output_path: str):
    """Generates a self-contained HTML report from the list of issues."""
    
    # Set up Jinja2 environment to load templates from the 'templates' directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_template.html')

    # If a chart exists, encode it in base64 to embed it directly in the HTML
    chart_data = None
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as image_file:
            chart_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Prepare data for the template
    template_data = {
        "issues": sorted(issues, key=lambda i: ({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(i.severity, 99), i.file_path)),
        "file_count": file_count,
        "chart_path": chart_path,
        "chart_data": chart_data,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Render the template with the data
    html_content = template.render(template_data)

    # Write the rendered HTML to the output file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report generated at: {output_path}")
    except Exception as e:
        print(f"Error generating HTML report: {e}")