import click
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from cqia_agent.utils.file_handler import find_code_files
from cqia_agent.core_analyzer import perform_analysis
from cqia_agent.reporting.visualizer import generate_severity_chart
from cqia_agent.qa.indexer import create_vector_store, DB_PATH
from cqia_agent.qa.retriever import create_rag_chain
from .reporting.html_generator import generate_html_report 
from cqia_agent.qa.agent import create_agent_graph
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from cqia_agent.reporting.display import display_ai_response


@click.group()
def cli():
    load_dotenv()


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.option('--no-enrich', is_flag=True, help="Disable AI enrichment for a faster, offline analysis.")
@click.option('--chart', is_flag=True, help="Generate a chart of issue severity distribution.")
@click.option('--html', type=click.Path(dir_okay=False), help="Generate an HTML report at the specified path.")
def analyze(path, no_enrich, chart, html):
    """Analyzes the code repository at the given path."""
    console = Console()

    console.print(f"🚀 Starting analysis of '{path}'...", style="bold green")

    all_issues, file_contents = perform_analysis(path, no_enrich)

    if not file_contents:
        console.print("No supported code files (.py, .js) found.", style="yellow")
        return

    code_files = list(file_contents.keys())
    console.print(f"Found {len(code_files)} code file(s) to analyze.")

    console.print("\n[bold magenta]3. Analysis Report:[/bold magenta]")

    report_summary_str = ""
    if not all_issues:
        console.print("✅ No issues found. Great job!", style="bold green")
    else:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(all_issues, key=lambda i: (severity_order.get(i.severity, 99), i.file_path))
        report_summary_str += f"Found {len(all_issues)} issue(s):\n"
        console.print(f"Found {len(all_issues)} issue(s):", style="bold yellow")
        for issue in sorted_issues:
            color = {"CRITICAL": "red", "HIGH": "yellow", "MEDIUM": "cyan"}.get(issue.severity, "white")
            
            report_md = f"\n---\n"
            report_md += f"### [{issue.severity}] - `{issue.file_path}:{issue.line_number}`\n"
            report_md += f"> {issue.message}\n\n"
            
            if issue.ai_explanation:
                report_md += f"**AI Explanation:**\n{issue.ai_explanation}\n\n"
            if issue.ai_suggestion:
                report_md += f"**AI Suggestion:**\n{issue.ai_suggestion}\n"

            console.print(Markdown(report_md, style=color))
            report_summary_str += report_md 

    if chart and all_issues:
        output_dir = os.path.join(os.getcwd(), "cqia_reports")
        chart_path = generate_severity_chart(all_issues, output_dir)
        if chart_path:
            console.print(f"\n📊 Severity distribution chart saved to: {chart_path}", style="bold blue")
    
    if html:
        from .utils.file_handler import find_code_files
        file_count = len(list(find_code_files(path)))
        generate_html_report(all_issues, file_count, chart_path, html)


    console.print("\n✅ Analysis complete!", style="bold green")



@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
def ask(path):
    """Starts an interactive Q&A session about the codebase."""
    console = Console()
    code_files = list(find_code_files(path))
    console.print("Performing RAG Ingestion", style="blue")
    if not code_files:
        console.print("No code files found to index. Exiting.", style="red")
        return
    create_vector_store(code_files, "")

    try:
        console.print("Loading knowledge base...", style="cyan")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        retriever = db.as_retriever()
        
        agent = create_agent_graph(retriever)
        console.print("🤖 [bold green]Knowledge base loaded. Ask me anything. Type 'exit' to end.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not load the knowledge base. Run 'analyze'. Details: {e}")
        return

    while True:
        question = click.prompt("💬 Ask a question")
        if question.lower() == 'exit':
            break
        
        with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
            result = agent.invoke({"question": question})
            response = result.get('generation', 'Sorry, I could not generate an answer.')
        
        display_ai_response(response)

if __name__ == "__main__":
    cli()
