import asyncio
import json
import signal
import sys
from pathlib import Path
from typing import Optional, List

import click
import yaml
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from roostai.back_end.chatbot.types import Document
from roostai.back_end.main import UniversityChatbot
from .base import ChatbotInterface


class CLIInterface(ChatbotInterface):
    def __init__(self):
        self.console = Console()
        self.chatbot: Optional[UniversityChatbot] = None
        self._cleanup_done = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up handlers for various signals."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.console.print(
            "\n[yellow]Received shutdown signal. Cleaning up...[/yellow]"
        )
        asyncio.create_task(self.cleanup())
        sys.exit(0)

    def _create_progress(self, description: str) -> Progress:
        """Create a progress bar with spinner."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

    async def initialize(self) -> None:
        """Initialize the CLI interface."""
        try:
            with self._create_progress("Initializing chatbot...") as progress:
                task = progress.add_task("Initializing...", total=1)
                self.chatbot = UniversityChatbot()
                progress.update(task, advance=1)

            doc_count = await self.chatbot.get_document_count()
            self.console.print(
                f"[green]✓ Chatbot initialized successfully with {doc_count} documents!"
            )
        except Exception as e:
            self.console.print(f"[red]Error initializing chatbot: {str(e)}")
            sys.exit(1)

    async def handle_query(self, query: str) -> None:
        """Handle a user query."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                # Create main task
                main_task = progress.add_task("Processing query...", total=5)

                # Step 1: Process query
                progress.update(main_task, description="Generating query embedding...")
                (
                    cleaned_query,
                    query_embedding,
                ) = await self.chatbot.query_processor.process_query(query)
                progress.advance(main_task)

                # Step 2: Search vector store
                progress.update(main_task, description="Searching knowledge base...")
                documents = await self.chatbot.vector_store.query(
                    query_embedding, k=self.chatbot.config.vector_db.top_k
                )
                progress.advance(main_task)

                if not documents:
                    self.console.print("[yellow]No relevant documents found.[/yellow]")
                    return

                # Step 3: Rerank results
                progress.update(main_task, description="Reranking results...")
                reranked_docs = await self.chatbot.reranker.rerank(
                    cleaned_query,
                    documents,
                    threshold=self.chatbot.config.thresholds.reranking_threshold,
                )
                progress.advance(main_task)

                # Step 4: Quality check
                progress.update(main_task, description="Checking result quality...")
                result = await self.chatbot.quality_checker.check_quality(
                    cleaned_query, reranked_docs
                )
                progress.advance(main_task)

                # Step 5: Generate response
                progress.update(main_task, description="Generating response...")
                response = await self.chatbot.llm_manager.generate_response(
                    cleaned_query, result
                )
                progress.advance(main_task)

            # Display response
            self.console.print("\n[bold blue]Response:[/bold blue]")
            self.console.print(Markdown(response))

        except Exception as e:
            await self.handle_error(e)

    async def handle_document_addition(self, documents: List[Document]) -> None:
        """Handle adding new documents."""
        try:
            with self._create_progress("Adding documents...") as progress:
                task = progress.add_task("Adding...", total=1)
                success = await self.chatbot.add_documents(documents)
                progress.update(task, advance=1)

            if success:
                doc_count = await self.chatbot.get_document_count()
                self.console.print(
                    f"[green]✓ Documents added successfully! Total documents: {doc_count}"
                )
            else:
                self.console.print("[red]Failed to add documents.")

        except Exception as e:
            await self.handle_error(e)

    async def handle_error(self, error: Exception) -> None:
        """Handle errors."""
        self.console.print(f"[red]Error: {str(error)}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._cleanup_done:
            return

        self.console.print("[yellow]Cleaning up resources...[/yellow]")

        try:
            if self.chatbot:
                await self.chatbot.cleanup()
            self.console.print("[green]Cleanup completed successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]Error during cleanup: {str(e)}[/red]")
        finally:
            self._cleanup_done = True

    async def show_help(self) -> None:
        """Show help information."""
        help_text = """
# Available Commands

- `/help` - Show this help message
- `/add` - Add a new document interactively
- `/add_file <path>` - Add documents from a JSON or YAML file
- `/info` - Show system information
- `/exit` - Exit the chat
- Any other input will be treated as a question to the chatbot
        """
        self.console.print(Markdown(help_text))

    async def show_info(self) -> None:
        """Show system information."""
        try:
            doc_count = await self.chatbot.get_document_count()

            info_text = f"""
# USC Chatbot System Information

## Configuration
- Embedding Model: {self.chatbot.config.model.embedding_model}
- Cross-Encoder Model: {self.chatbot.config.model.cross_encoder_model}
- LLM Model: {self.chatbot.config.model.llm_model}

## Statistics
- Total Documents: {doc_count}
- Collection Name: {self.chatbot.config.vector_db.collection_name}

## Thresholds
- Reranking Threshold: {self.chatbot.config.thresholds.reranking_threshold}
- Quality Minimum Score: {self.chatbot.config.thresholds.quality_min_score}
- Quality Minimum Docs: {self.chatbot.config.thresholds.quality_min_docs}
            """
            self.console.print(Markdown(info_text))
        except Exception as e:
            await self.handle_error(e)

    async def add_document_interactive(self) -> None:
        """Add a document interactively."""
        try:
            self.console.print("\n[cyan]Adding a new document:[/cyan]")
            content = Prompt.ask("Enter document content")

            # Get metadata
            metadata = {}
            if Confirm.ask("Would you like to add metadata?"):
                while True:
                    key = Prompt.ask("Enter metadata key (or press Enter to finish)")
                    if not key:
                        break
                    value = Prompt.ask(f"Enter value for {key}")
                    metadata[key] = value

            document = Document(content=content, metadata=metadata)
            await self.handle_document_addition([document])

        except Exception as e:
            await self.handle_error(e)

    async def add_documents_from_file(self, file_path: str) -> None:
        """Add documents from a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.console.print(f"[red]File not found: {file_path}")
                return

            if path.suffix == ".json":
                with open(path) as f:
                    data = json.load(f)
            elif path.suffix in [".yaml", ".yml"]:
                with open(path) as f:
                    data = yaml.safe_load(f)
            else:
                self.console.print("[red]File must be JSON or YAML format")
                return

            documents = [
                Document(
                    content=doc["content"], metadata=doc.get("metadata", {}), score=None
                )
                for doc in data
            ]

            await self.handle_document_addition(documents)

        except Exception as e:
            await self.handle_error(e)


@click.command()
# @click.option('--config', '-c', type=str, help='Path to config file')
def chat():
    """Start an interactive chat session."""

    async def run_chat():
        interface = CLIInterface()
        try:
            await interface.initialize()
            await interface.show_help()  # Show help first

            while True:
                try:
                    query = Prompt.ask(
                        "\n[bold cyan]Enter your question or command[/bold cyan]"
                    ).strip()

                    # Skip empty queries
                    if not query:
                        continue

                    # Handle commands
                    if query.startswith("/"):
                        cmd = query.lower().split()
                        command = cmd[0]

                        if command == "/exit":
                            break
                        elif command == "/help":
                            await interface.show_help()
                        elif command == "/info":
                            await interface.show_info()
                        elif command == "/add":
                            await interface.add_document_interactive()
                        elif command == "/add_file" and len(cmd) > 1:
                            await interface.add_documents_from_file(cmd[1])
                        else:
                            interface.console.print(
                                "[yellow]Unknown command. Type /help for available commands.[/yellow]"
                            )
                    else:
                        # Handle regular queries
                        await interface.handle_query(query)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    await interface.handle_error(e)
        finally:
            await interface.cleanup()

    try:
        asyncio.run(run_chat())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    chat()
