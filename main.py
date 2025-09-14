import click
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from src.utils.file_handler import find_code_files
from src.analysis.ast_parser import parse_file_to_ast
from src.analysis.issue_detector import (
    detect_complexity_issues,
    detect_missing_documentation,
    detect_hardcoded_secrets,
)
from src.ai.enricher import enrich_issue
from src.reporting.visualizer import generate_severity_chart

from src.qa.indexer import create_vector_store

from src.qa.indexer import create_vector_store, DB_PATH
from src.qa.retriever import create_rag_chain
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from src.reporting.display import display_ai_response

@click.group()
def cli():
    load_dotenv()

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.option('--no-enrich', is_flag=True, help="Disable AI enrichment for a faster, offline analysis.")
@click.option('--chart', is_flag=True, help="Generate a chart of issue severity distribution.")
@click.option('--no-index', is_flag=True, help="Disable Q&A index creation.")
def analyze(path, no_enrich, chart,no_index):
    """Analyzes the code repository at the given path."""
    console = Console()

    console.print(f"🚀 Starting analysis of '{path}'...", style="bold green")
    
    code_files = list(find_code_files(path))
    if not code_files:
        console.print("No supported code files (.py, .js) found.", style="yellow")
        return
        
    console.print(f"Found {len(code_files)} code file(s) to analyze.")
    console.print("1. Running deterministic detectors...")

    all_issues = []
    file_contents = {}
    for file_path in code_files:
        try:
            with open(file_path, "rb") as f:
                file_contents[file_path] = f.read()
        except Exception: continue
        
        all_issues.extend(detect_hardcoded_secrets(file_path, file_contents[file_path]))
        
        parse_result = parse_file_to_ast(file_path)
        if parse_result:
            tree, language = parse_result
            lang_name = "python" if file_path.endswith('.py') else "javascript"
            all_issues.extend(detect_complexity_issues(tree, language, file_path, file_contents[file_path], lang_name))
            all_issues.extend(detect_missing_documentation(tree, language, file_path, file_contents[file_path], lang_name))

    if not no_enrich and all_issues:
        console.print(f"\n2. Enriching {len(all_issues)} issue(s) with AI... (this may take a moment)", style="bold cyan")
        enriched_issues = [
            enrich_issue(issue, file_contents[issue.file_path].decode('utf-8', errors='ignore'))
            for issue in all_issues
        ]
        all_issues = enriched_issues

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
    if not no_index:
        console.print("\n[bold purple]4. Creating Q&A Index...[/bold purple]")
        create_vector_store(code_files, report_summary_str)

    console.print("\n✅ Analysis complete!", style="bold green")



@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
def ask(path):
    """Starts an interactive Q&A session about the codebase."""
    console = Console()

    if not os.path.exists(DB_PATH):
        console.print("[bold yellow]Warning:[/bold yellow] No analysis index found.", style="yellow")
        console.print("Performing a one-time code-only indexing. For more detailed answers, run 'analyze' first.")
        code_files = list(find_code_files(path))
        if not code_files:
            console.print("No code files found to index. Exiting.", style="red")
            return
        create_vector_store(code_files, "")

    try:
        console.print("Loading knowledge base...", style="cyan")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        rag_chain = create_rag_chain(db)
        console.print("🤖 [bold green]Knowledge base loaded. Ask me anything. Type 'exit' to end.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not load knowledge base. Please run 'analyze'. Details: {e}")
        return

    while True:
        question = click.prompt("💬 Ask a question")
        if question.lower() == 'exit':
            break
        
        with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
            response = rag_chain.invoke(question)
        
        display_ai_response(response)

if __name__ == "__main__":
    cli()
