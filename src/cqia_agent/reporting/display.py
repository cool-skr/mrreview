import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def display_ai_response(response: str):
    """
    Parses a structured AI response and prints it to the console as a formatted panel.
    """
    console = Console()

    title_match = re.search(r"\[TITLE\]:(.*?)\n", response, re.DOTALL)
    summary_match = re.search(r"\[SUMMARY\]:(.*?)\n", response, re.DOTALL)
    response_match = re.search(r"\[RESPONSE\]:(.*)", response, re.DOTALL)

    title = title_match.group(1).strip() if title_match else "AI Response"
    summary = summary_match.group(1).strip() if summary_match else ""
    main_content = response_match.group(1).strip() if response_match else response

    full_markdown_content = f"**{summary}**\n\n{main_content}"
    
    console.print(
        Panel(
            Markdown(full_markdown_content),
            title=f"[bold green]{title}[/bold green]",
            border_style="green",
            expand=True
        )
    )