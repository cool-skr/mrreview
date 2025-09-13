import click
import os
from dotenv import load_dotenv

from src.utils.file_handler import find_code_files
from src.analysis.ast_parser import parse_file_to_ast
from src.analysis.issue_detector import detect_complexity_issues

@click.group()
def cli():
    """A Code Quality Intelligence Agent
    
    Set your GROQ_API_KEY in a .env file.
    """
    load_dotenv()

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, resolve_path=True))
def analyze(path):
    """Analyzes the code repository at the given path."""
    click.echo(f"🚀 Starting analysis of '{path}'...")
    
    code_files = list(find_code_files(path))
    
    if not code_files:
        click.secho("No supported code files (.py, .js) found in the specified path.", fg="yellow")
        return
        
    click.echo(f"Found {len(code_files)} code files to analyze.")
    click.echo("1. Parsing files into ASTs...")

    all_issues = []
    for file_path in code_files:
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
        except Exception as e:
            click.secho(f"  -> Error reading {os.path.basename(file_path)}: {e}", fg="red")
            continue

        parse_result = parse_file_to_ast(file_path)
        if parse_result:
            tree, language = parse_result 
            lang_name = "python" if file_path.endswith('.py') else "javascript"
            
            complexity_issues = detect_complexity_issues(tree, language, file_path, file_content, lang_name)
            all_issues.extend(complexity_issues)
            
        else:
            click.secho(f"  -> Failed to parse {os.path.basename(file_path)}", fg="red")

    click.echo("\n2. Analyzing for issues...")
    if not all_issues:
        click.secho("✅ No issues found. Great job!", fg="green")
    else:
        click.secho(f"Found {len(all_issues)} issue(s):", fg="yellow")
        for issue in sorted(all_issues, key=lambda i: i.file_path):
            click.echo(f"  - [{issue.severity}] {issue.file_path}:{issue.line_number}")
            click.echo(f"    {issue.message}")

    click.secho("\n✅ Analysis complete!", fg="green")





@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, resolve_path=True))
def ask(path):
    """Starts an interactive Q&A session about the codebase."""
    click.echo(f"🤖 Starting interactive Q&A for '{path}'. Type 'exit' to end.")
    
    
    while True:
        question = click.prompt("Ask a question about the code")
        if question.lower() == 'exit':
            break
        
        answer = f"Thinking about '{question}'... (Q&A logic not implemented yet)"
        click.echo(answer)

if __name__ == "__main__":
    cli()