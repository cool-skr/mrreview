import os
import matplotlib.pyplot as plt
from typing import List, Optional
from collections import Counter
from src.analysis.models import Issue

def generate_severity_chart(issues: List[Issue], output_dir: str) -> Optional[str]:
    """
    Generates a bar chart of issue counts by severity and saves it as a PNG file.

    Args:
        issues: A list of Issue objects found by the analysis.
        output_dir: The directory to save the generated chart image.

    Returns:
        The path to the generated image file, or None if no issues were found.
    """
    if not issues:
        return None

    severities = [issue.severity for issue in issues]
    severity_counts = Counter(severities)
    
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    labels = [s for s in order if s in severity_counts]
    counts = [severity_counts[s] for s in labels]
    
    colors = {'LOW': 'skyblue', 'MEDIUM': 'blue', 'HIGH': 'orange', 'CRITICAL': 'red'}
    bar_colors = [colors.get(s, 'gray') for s in labels]

    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots()
    
    bars = ax.bar(labels, counts, color=bar_colors)
    
    ax.set_title('Code Quality Issue Breakdown', fontsize=16, fontweight='bold')
    ax.set_ylabel('Number of Issues', fontsize=12)
    ax.set_xlabel('Severity', fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom', ha='center')

    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "severity_breakdown.png")
    try:
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close(fig) 
        return output_path
    except Exception as e:
        print(f"Error saving chart: {e}")
        plt.close(fig)
        return None