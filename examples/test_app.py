#!/usr/bin/env python3
"""
Yod SDK Test Application

Interactive CLI to test the full Yod memory SDK functionality.
Tests ingestion, chat with LLM-powered memory retrieval, and memory management.

Usage:
    python test_app.py --api-key sk-yod-xxx
    python test_app.py --base-url http://localhost:8000 --user-id test-user
    python test_app.py --test  # Run automated test suite

Environment variables:
    YOD_API_KEY, YOD_TOKEN, YOD_USER_ID, YOD_BASE_URL
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

# Add the SDK src directory to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich import box

from yod import YodClient
from yod.exceptions import (
    YodError,
    YodAPIError,
    YodConnectionError,
    YodTimeoutError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Yod SDK Test Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_app.py --base-url http://localhost:8000 --user-id test-user
  python test_app.py --api-key sk-yod-xxxx
  python test_app.py --test  # Run automated tests
        """,
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("YOD_API_KEY"),
        help="Yod API key (or set YOD_API_KEY env var)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("YOD_TOKEN"),
        help="JWT bearer token (or set YOD_TOKEN env var)",
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("YOD_USER_ID"),
        help="User ID for dev mode (or set YOD_USER_ID env var)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("YOD_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run automated test suite instead of interactive mode",
    )
    return parser.parse_args()


def create_client(args: argparse.Namespace) -> YodClient:
    """Create and return a YodClient with the provided configuration."""
    return YodClient(
        api_key=args.api_key,
        bearer_token=args.token,
        user_id=args.user_id,
        base_url=args.base_url,
        timeout=60.0,  # Longer timeout for LLM operations
    )


def print_header():
    """Print the application header."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Yod Memory Test App[/bold cyan]\n"
            "[dim]Interactive SDK Testing Tool[/dim]",
            box=box.DOUBLE,
            padding=(1, 4),
        )
    )
    console.print()


def print_menu():
    """Print the main menu."""
    menu = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
    menu.add_column("Option", style="cyan", width=4)
    menu.add_column("Action", style="white")

    menu.add_row("1", "Ingest Text (add to memory)")
    menu.add_row("2", "Chat (query memories with LLM)")
    menu.add_row("3", "List Memories")
    menu.add_row("4", "Get Memory Details")
    menu.add_row("5", "Update Memory")
    menu.add_row("6", "Delete Memory")
    menu.add_row("7", "View Memory History")
    menu.add_row("8", "Health Check")
    menu.add_row("9", "Run Test Suite")
    menu.add_row("0", "Exit")

    console.print(menu)
    console.print()


def print_success(message: str):
    """Print a success message."""
    console.print(f"[green][OK][/green] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red][FAIL][/red] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[blue][INFO][/blue] {message}")


def handle_error(e: Exception):
    """Handle and display SDK errors nicely."""
    if isinstance(e, AuthenticationError):
        print_error(f"Authentication failed: {e}")
        console.print("[dim]Check your API key or token[/dim]")
    elif isinstance(e, NotFoundError):
        print_error(f"Not found: {e}")
    elif isinstance(e, ValidationError):
        print_error(f"Validation error: {e}")
        if hasattr(e, "response_body") and e.response_body:
            console.print(f"[dim]Details: {e.response_body}[/dim]")
    elif isinstance(e, RateLimitError):
        print_error(f"Rate limited: {e}")
        if e.retry_after:
            console.print(f"[dim]Retry after: {e.retry_after}s[/dim]")
    elif isinstance(e, YodConnectionError):
        print_error(f"Connection error: {e}")
        console.print("[dim]Is the server running?[/dim]")
    elif isinstance(e, YodTimeoutError):
        print_error(f"Request timed out: {e}")
    elif isinstance(e, YodAPIError):
        print_error(f"API error ({e.status_code}): {e}")
        if e.request_id:
            console.print(f"[dim]Request ID: {e.request_id}[/dim]")
    else:
        print_error(f"Unexpected error: {e}")


# ============================================================
# Feature Implementations
# ============================================================


def do_ingest(client: YodClient):
    """Ingest text into memory."""
    console.print("\n[bold]Ingest Text[/bold]")
    console.print("[dim]Enter text to store in memory (facts, preferences, conversations)[/dim]\n")

    text = Prompt.ask("Text to ingest")
    if not text.strip():
        print_error("Text cannot be empty")
        return

    source_id = Prompt.ask("Source ID (optional)", default="")
    timestamp = Prompt.ask("Timestamp ISO8601 (optional)", default="")

    try:
        with console.status("[cyan]Ingesting text...[/cyan]"):
            response = client.ingest_chat(
                text=text,
                source_id=source_id if source_id else None,
                timestamp=timestamp if timestamp else None,
            )

        print_success("Text ingested successfully!")
        console.print(f"[dim]Source ID: {response.source_id}[/dim]")
        console.print(f"[dim]Chunks created: {response.chunks}[/dim]")

        # Show extracted entities
        if response.entities:
            console.print("\n[bold]Extracted Entities:[/bold]")
            entity_table = Table(box=box.SIMPLE)
            entity_table.add_column("ID", style="dim")
            entity_table.add_column("Name", style="cyan")
            entity_table.add_column("Type", style="green")

            for entity in response.entities:
                entity_table.add_row(
                    entity.entity_id[:12] + "...",
                    entity.canonical_name,
                    entity.type,
                )
            console.print(entity_table)

        # Show extracted memories
        if response.memories:
            console.print("\n[bold]Extracted Memories:[/bold]")
            memory_table = Table(box=box.SIMPLE)
            memory_table.add_column("ID", style="dim")
            memory_table.add_column("Kind", style="magenta")
            memory_table.add_column("Summary", style="white", max_width=50)
            memory_table.add_column("Confidence", style="yellow")

            for memory in response.memories:
                memory_table.add_row(
                    memory.memory_id[:12] + "...",
                    memory.kind,
                    memory.summary[:50] + "..." if len(memory.summary) > 50 else memory.summary,
                    f"{memory.confidence:.2f}",
                )
            console.print(memory_table)

    except YodError as e:
        handle_error(e)


def do_chat(client: YodClient):
    """Query memories with chat."""
    console.print("\n[bold]Chat with Memory[/bold]")
    console.print("[dim]Ask a question - the LLM will use your memories to answer[/dim]\n")

    question = Prompt.ask("Your question")
    if not question.strip():
        print_error("Question cannot be empty")
        return

    language = Prompt.ask("Language (optional, e.g., 'en', 'fa')", default="")
    as_of = Prompt.ask("As-of timestamp (optional, for temporal queries)", default="")

    try:
        with console.status("[cyan]Thinking...[/cyan]"):
            response = client.chat(
                question=question,
                language=language if language else None,
                as_of=as_of if as_of else None,
            )

        # Display answer
        console.print()
        console.print(Panel(response.answer, title="[bold green]Answer[/bold green]", box=box.ROUNDED))

        # Show citations
        if response.citations:
            console.print("\n[bold]Citations:[/bold]")
            for i, citation in enumerate(response.citations, 1):
                console.print(f"  [{i}] Source: [dim]{citation.source_id[:12]}...[/dim]")
                if citation.quote:
                    console.print(f"      Quote: [italic]\"{citation.quote}\"[/italic]")

        # Show used memories
        if response.used_memory_ids:
            console.print(f"\n[dim]Used {len(response.used_memory_ids)} memories[/dim]")

    except YodError as e:
        handle_error(e)


def do_list_memories(client: YodClient):
    """List memories with optional filters."""
    console.print("\n[bold]List Memories[/bold]\n")

    limit = Prompt.ask("Limit", default="20")
    kind = Prompt.ask("Filter by kind (optional, e.g., 'preference', 'fact')", default="")
    search = Prompt.ask("Search term (optional)", default="")
    include_inactive = Confirm.ask("Include inactive/superseded?", default=False)

    try:
        with console.status("[cyan]Fetching memories...[/cyan]"):
            response = client.list_memories(
                limit=int(limit),
                kind=kind if kind else None,
                search=search if search else None,
                include_inactive=include_inactive,
            )

        if not response.items:
            print_info("No memories found")
            return

        print_success(f"Found {len(response.items)} memories")
        console.print()

        table = Table(box=box.SIMPLE)
        table.add_column("ID", style="dim", width=14)
        table.add_column("Kind", style="magenta", width=12)
        table.add_column("Summary", style="white", max_width=45)
        table.add_column("Conf", style="yellow", width=5)
        table.add_column("Status", style="cyan", width=10)

        for item in response.items:
            status = item.status or "active"
            status_style = "green" if status == "active" else "dim"
            table.add_row(
                item.memory_id[:12] + "...",
                item.kind,
                item.summary[:42] + "..." if len(item.summary) > 42 else item.summary,
                f"{item.confidence:.2f}",
                f"[{status_style}]{status}[/{status_style}]",
            )

        console.print(table)

    except YodError as e:
        handle_error(e)


def do_get_memory(client: YodClient):
    """Get a single memory by ID."""
    console.print("\n[bold]Get Memory Details[/bold]\n")

    memory_id = Prompt.ask("Memory ID")
    if not memory_id.strip():
        print_error("Memory ID is required")
        return

    try:
        with console.status("[cyan]Fetching memory...[/cyan]"):
            memory = client.get_memory(memory_id)

        console.print()
        console.print(Panel(
            f"[bold]ID:[/bold] {memory.memory_id}\n"
            f"[bold]Kind:[/bold] {memory.kind}\n"
            f"[bold]Summary:[/bold] {memory.summary}\n"
            f"[bold]Confidence:[/bold] {memory.confidence:.2f}\n"
            f"[bold]Status:[/bold] {memory.status or 'active'}\n"
            f"[bold]Key:[/bold] {memory.key or 'N/A'}\n"
            f"[bold]Updated:[/bold] {memory.updated_at or 'N/A'}\n"
            f"[bold]Valid From:[/bold] {memory.valid_from or 'N/A'}\n"
            f"[bold]Valid To:[/bold] {memory.valid_to or 'N/A'}",
            title="[bold cyan]Memory Details[/bold cyan]",
            box=box.ROUNDED,
        ))

        if memory.entity_ids:
            console.print(f"\n[bold]Linked Entities:[/bold] {', '.join(memory.entity_ids[:5])}")
            if len(memory.entity_ids) > 5:
                console.print(f"[dim]...and {len(memory.entity_ids) - 5} more[/dim]")

        if memory.support:
            console.print("\n[bold]Supporting Evidence:[/bold]")
            for support in memory.support[:3]:
                console.print(f"  Source: [dim]{support.source_id[:12]}...[/dim]")
                for quote in support.quotes[:2]:
                    console.print(f"    • [italic]\"{quote[:60]}...\"[/italic]" if len(quote) > 60 else f"    • [italic]\"{quote}\"[/italic]")

    except YodError as e:
        handle_error(e)


def do_update_memory(client: YodClient):
    """Update a memory's fields."""
    console.print("\n[bold]Update Memory[/bold]\n")

    memory_id = Prompt.ask("Memory ID to update")
    if not memory_id.strip():
        print_error("Memory ID is required")
        return

    console.print("[dim]Leave fields empty to keep current value[/dim]\n")

    kind = Prompt.ask("New kind (optional)", default="")
    summary = Prompt.ask("New summary (optional)", default="")
    confidence = Prompt.ask("New confidence 0.0-1.0 (optional)", default="")

    try:
        with console.status("[cyan]Updating memory...[/cyan]"):
            result = client.update_memory(
                memory_id,
                kind=kind if kind else None,
                summary=summary if summary else None,
                confidence=float(confidence) if confidence else None,
            )

        if result.get("ok"):
            print_success("Memory updated successfully!")
        else:
            print_error("Update failed")

    except YodError as e:
        handle_error(e)


def do_delete_memory(client: YodClient):
    """Delete a memory."""
    console.print("\n[bold]Delete Memory[/bold]\n")

    memory_id = Prompt.ask("Memory ID to delete")
    if not memory_id.strip():
        print_error("Memory ID is required")
        return

    if not Confirm.ask(f"Are you sure you want to delete memory {memory_id[:12]}...?", default=False):
        print_info("Cancelled")
        return

    try:
        with console.status("[cyan]Deleting memory...[/cyan]"):
            result = client.delete_memory(memory_id)

        if result.get("ok"):
            print_success("Memory deleted successfully!")
            console.print(f"[dim]Qdrant vectors deleted: {result.get('qdrant_deleted', 0)}[/dim]")
        else:
            print_error("Delete failed")

    except YodError as e:
        handle_error(e)


def do_view_history(client: YodClient):
    """View memory version history."""
    console.print("\n[bold]Memory History[/bold]\n")

    memory_id = Prompt.ask("Memory ID")
    if not memory_id.strip():
        print_error("Memory ID is required")
        return

    try:
        with console.status("[cyan]Fetching history...[/cyan]"):
            response = client.get_memory_history(memory_id)

        if not response.items:
            print_info("No history found for this memory")
            return

        print_success(f"Found {len(response.items)} versions")
        console.print()

        table = Table(box=box.SIMPLE, title="Version History")
        table.add_column("Version", style="cyan")
        table.add_column("Summary", style="white", max_width=40)
        table.add_column("Status", style="magenta")
        table.add_column("Valid From", style="dim")
        table.add_column("Valid To", style="dim")

        for i, item in enumerate(response.items, 1):
            table.add_row(
                str(i),
                item.summary[:37] + "..." if len(item.summary) > 37 else item.summary,
                item.status or "active",
                item.valid_from[:10] if item.valid_from else "N/A",
                item.valid_to[:10] if item.valid_to else "current",
            )

        console.print(table)

    except YodError as e:
        handle_error(e)


def do_health_check(client: YodClient):
    """Check API health status."""
    console.print("\n[bold]Health Check[/bold]\n")

    try:
        # Basic health
        with console.status("[cyan]Checking health...[/cyan]"):
            health = client.health()
        print_success(f"API Health: {health.status}")

        # Detailed readiness
        with console.status("[cyan]Checking readiness...[/cyan]"):
            ready = client.ready()

        console.print()
        table = Table(box=box.SIMPLE, title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        # Overall
        overall_style = "green" if ready.status == "ok" else "yellow" if ready.status == "degraded" else "red"
        table.add_row("Overall", f"[{overall_style}]{ready.status}[/{overall_style}]", "")

        # Neo4j
        if ready.neo4j:
            neo4j_style = "green" if ready.neo4j.ok else "red"
            table.add_row(
                "Neo4j",
                f"[{neo4j_style}]{'OK' if ready.neo4j.ok else 'ERROR'}[/{neo4j_style}]",
                ready.neo4j.error or "",
            )

        # Qdrant
        if ready.qdrant:
            qdrant_style = "green" if ready.qdrant.ok else "red"
            table.add_row(
                "Qdrant",
                f"[{qdrant_style}]{'OK' if ready.qdrant.ok else 'ERROR'}[/{qdrant_style}]",
                ready.qdrant.error or "",
            )

        console.print(table)

    except YodError as e:
        handle_error(e)


# ============================================================
# Automated Test Suite
# ============================================================


def run_test_suite(client: YodClient):
    """Run automated test scenarios."""
    console.print("\n[bold cyan]Running Automated Test Suite[/bold cyan]\n")

    tests_passed = 0
    tests_failed = 0

    def test(name: str, func):
        nonlocal tests_passed, tests_failed
        console.print(f"[bold]Test:[/bold] {name}")
        try:
            func()
            print_success("PASSED")
            tests_passed += 1
        except AssertionError as e:
            print_error(f"FAILED: {e}")
            tests_failed += 1
        except YodError as e:
            print_error(f"ERROR: {e}")
            tests_failed += 1
        console.print()

    # Test 1: Health Check
    def test_health():
        health = client.health()
        assert health.status == "ok", f"Expected 'ok', got '{health.status}'"

    test("Health Check", test_health)

    # Test 2: Ingest basic text
    ingest_response = None

    def test_ingest():
        nonlocal ingest_response
        ingest_response = client.ingest_chat(
            text="My name is TestUser and I love Python programming. My favorite color is blue."
        )
        assert ingest_response.source_id, "No source_id returned"
        assert ingest_response.chunks > 0, "No chunks created"
        console.print(f"  [dim]Created {len(ingest_response.memories)} memories[/dim]")

    test("Ingest Text", test_ingest)

    # Test 3: List memories
    def test_list():
        response = client.list_memories(limit=10)
        assert response.items is not None, "No items returned"
        console.print(f"  [dim]Found {len(response.items)} memories[/dim]")

    test("List Memories", test_list)

    # Test 4: Chat query
    def test_chat():
        response = client.chat(question="What is my name?")
        assert response.answer, "No answer returned"
        console.print(f"  [dim]Answer: {response.answer[:60]}...[/dim]")

    test("Chat Query", test_chat)

    # Test 5: Chat with context
    def test_chat_context():
        response = client.chat(question="What programming language do I like?")
        assert response.answer, "No answer returned"
        # Check if Python is mentioned (case insensitive)
        assert "python" in response.answer.lower(), f"Expected 'Python' in answer: {response.answer}"
        console.print(f"  [dim]Answer mentions Python: YES[/dim]")

    test("Chat with Context", test_chat_context)

    # Test 6: Get memory (if we have one)
    memory_id_to_test = None

    def test_get_memory():
        nonlocal memory_id_to_test
        memories = client.list_memories(limit=1)
        if memories.items:
            memory_id_to_test = memories.items[0].memory_id
            memory = client.get_memory(memory_id_to_test)
            assert memory.memory_id == memory_id_to_test, "Memory ID mismatch"
            console.print(f"  [dim]Retrieved: {memory.summary[:40]}...[/dim]")
        else:
            raise AssertionError("No memories to test")

    test("Get Memory", test_get_memory)

    # Test 7: Update memory
    def test_update():
        if not memory_id_to_test:
            raise AssertionError("No memory to update")
        result = client.update_memory(memory_id_to_test, confidence=0.95)
        assert result.get("ok"), "Update failed"

    test("Update Memory", test_update)

    # Test 8: Memory history (may or may not have history)
    def test_history():
        if not memory_id_to_test:
            raise AssertionError("No memory to check history")
        try:
            response = client.get_memory_history(memory_id_to_test)
            console.print(f"  [dim]Found {len(response.items)} versions[/dim]")
        except NotFoundError:
            console.print("  [dim]No history (expected for new memories)[/dim]")

    test("Memory History", test_history)

    # Summary
    console.print()
    console.print(Panel(
        f"[green]Passed: {tests_passed}[/green]\n"
        f"[red]Failed: {tests_failed}[/red]\n"
        f"[bold]Total: {tests_passed + tests_failed}[/bold]",
        title="[bold]Test Results[/bold]",
        box=box.ROUNDED,
    ))

    return tests_failed == 0


# ============================================================
# Main Entry Point
# ============================================================


def main():
    """Main entry point."""
    args = parse_args()

    # Validate we have some form of authentication
    if not any([args.api_key, args.token, args.user_id]):
        console.print("[red]Error:[/red] No authentication provided")
        console.print("Use --api-key, --token, or --user-id (for dev mode)")
        console.print("Or set YOD_API_KEY, YOD_TOKEN, or YOD_USER_ID environment variables")
        sys.exit(1)

    # Create client
    client = create_client(args)
    console.print(f"[dim]Connecting to: {args.base_url}[/dim]")

    # Run automated tests if --test flag
    if args.test:
        success = run_test_suite(client)
        sys.exit(0 if success else 1)

    # Interactive mode
    print_header()

    while True:
        print_menu()
        choice = Prompt.ask("Select option", default="0")

        if choice == "1":
            do_ingest(client)
        elif choice == "2":
            do_chat(client)
        elif choice == "3":
            do_list_memories(client)
        elif choice == "4":
            do_get_memory(client)
        elif choice == "5":
            do_update_memory(client)
        elif choice == "6":
            do_delete_memory(client)
        elif choice == "7":
            do_view_history(client)
        elif choice == "8":
            do_health_check(client)
        elif choice == "9":
            run_test_suite(client)
        elif choice == "0":
            console.print("\n[cyan]Goodbye![/cyan]\n")
            break
        else:
            print_error("Invalid option")

        console.print()
        Prompt.ask("Press Enter to continue")
        console.clear()
        print_header()


if __name__ == "__main__":
    main()
