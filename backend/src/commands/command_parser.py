"""
Command Parser for analytics commands in the banker terminal.

Parses command strings and routes to appropriate analytics functions.
"""

from typing import Dict, Any, Optional, Tuple
import re


def parse_command(command: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse a command string and return command type and arguments.
    
    Args:
        command: Command string (e.g., "/analytics portfolio", "/analytics region India")
    
    Returns:
        Tuple of (command_type, arguments_dict)
    """
    command = command.strip()
    
    if not command.startswith("/"):
        return ("invalid", {"error": "Commands must start with /"})
    
    # Remove leading slash
    command = command[1:]
    
    # Split into parts
    parts = command.split()
    
    if not parts:
        return ("help", {})
    
    command_type = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    # Route to appropriate handler
    if command_type == "analytics":
        return parse_analytics_command(args)
    elif command_type == "export":
        return parse_export_command(args)
    elif command_type == "help":
        return ("help", {})
    else:
        return ("unknown", {"command": command_type})


def parse_analytics_command(args: list) -> Tuple[str, Dict[str, Any]]:
    """Parse analytics subcommands."""
    if not args:
        return ("analytics_portfolio", {})
    
    subcommand = args[0].lower()
    
    if subcommand == "portfolio":
        return ("analytics_portfolio", {})
    elif subcommand == "region":
        region = " ".join(args[1:]) if len(args) > 1 else None
        return ("analytics_region", {"region": region})
    elif subcommand == "trend":
        metric = args[1].lower() if len(args) > 1 else "sustainability"
        return ("analytics_trend", {"metric": metric})
    elif subcommand == "carbon":
        return ("analytics_carbon", {})
    elif subcommand == "compliance":
        return ("analytics_compliance", {})
    else:
        return ("analytics_unknown", {"subcommand": subcommand})


def parse_export_command(args: list) -> Tuple[str, Dict[str, Any]]:
    """Parse export subcommands."""
    if not args:
        return ("export_help", {})
    
    format_type = args[0].lower()
    
    if format_type in ["pdf", "csv"]:
        return (f"export_{format_type}", {})
    else:
        return ("export_unknown", {"format": format_type})


def get_help_text() -> str:
    """Get help text for available commands."""
    return """
Available Commands:

/analytics portfolio          - Show portfolio-wide statistics
/analytics region [name]     - Analyze applications by region
/analytics trend [metric]    - Show trend analysis (sustainability/risk/ndvi)
/analytics carbon            - Calculate carbon impact
/analytics compliance        - Run compliance audit

/export pdf                  - Export portfolio report as PDF
/export csv                  - Export applications as CSV

/help                        - Show this help message
"""


def get_command_suggestions(partial_command: str) -> list:
    """Get command suggestions based on partial input."""
    suggestions = []
    
    if not partial_command or partial_command == "/":
        return [
            "/analytics",
            "/export",
            "/help"
        ]
    
    partial = partial_command.lower().strip()
    
    if partial.startswith("/analytics"):
        suggestions = [
            "/analytics portfolio",
            "/analytics region",
            "/analytics trend",
            "/analytics carbon",
            "/analytics compliance"
        ]
    elif partial.startswith("/export"):
        suggestions = [
            "/export pdf",
            "/export csv"
        ]
    elif partial.startswith("/"):
        suggestions = [
            "/analytics portfolio",
            "/export pdf",
            "/help"
        ]
    
    # Filter suggestions based on partial match
    if len(partial) > 1:
        suggestions = [s for s in suggestions if s.lower().startswith(partial.lower())]
    
    return suggestions[:5]  # Return top 5 suggestions


def execute_command(command: str) -> Dict[str, Any]:
    """
    Execute a command and return results.
    
    Args:
        command: Command string to execute
    
    Returns:
        Dictionary with command results
    """
    from services import analytics_service
    
    cmd_type, args = parse_command(command)
    
    try:
        if cmd_type == "analytics_portfolio":
            return {
                "type": "portfolio",
                "data": analytics_service.get_portfolio_stats(),
                "success": True
            }
        
        elif cmd_type == "analytics_region":
            region = args.get("region")
            return {
                "type": "region",
                "data": analytics_service.get_regional_analysis(region),
                "success": True
            }
        
        elif cmd_type == "analytics_trend":
            metric = args.get("metric", "sustainability")
            return {
                "type": "trend",
                "data": analytics_service.get_trend_analysis(metric),
                "success": True
            }
        
        elif cmd_type == "analytics_carbon":
            return {
                "type": "carbon",
                "data": analytics_service.calculate_carbon_impact(),
                "success": True
            }
        
        elif cmd_type == "analytics_compliance":
            return {
                "type": "compliance",
                "data": analytics_service.get_compliance_audit(),
                "success": True
            }
        
        elif cmd_type == "export_pdf":
            output_path = analytics_service.export_to_pdf()
            return {
                "type": "export",
                "format": "pdf",
                "path": output_path,
                "success": True,
                "message": f"PDF exported to: {output_path}"
            }
        
        elif cmd_type == "export_csv":
            output_path = analytics_service.export_to_csv()
            return {
                "type": "export",
                "format": "csv",
                "path": output_path,
                "success": True,
                "message": f"CSV exported to: {output_path}"
            }
        
        elif cmd_type == "help":
            return {
                "type": "help",
                "data": get_help_text(),
                "success": True
            }
        
        elif cmd_type == "unknown":
            command_name = args.get('command', '')
            suggestions = get_command_suggestions(f"/{command_name}")
            return {
                "type": "error",
                "error": f"Unknown command: '{command_name}'. Available commands: /analytics, /export, /help",
                "suggestions": suggestions,
                "success": False
            }
        
        elif cmd_type == "analytics_unknown":
            subcommand = args.get("subcommand", "")
            return {
                "type": "error",
                "error": f"Unknown analytics subcommand: '{subcommand}'. Available: portfolio, region, trend, carbon, compliance",
                "success": False
            }
        
        elif cmd_type == "export_unknown":
            format_type = args.get("format", "")
            return {
                "type": "error",
                "error": f"Unknown export format: '{format_type}'. Available: pdf, csv",
                "success": False
            }
        
        else:
            return {
                "type": "error",
                "error": f"Command not recognized: {cmd_type}. Type /help for available commands.",
                "success": False
            }
    
    except Exception as e:
        return {
            "type": "error",
            "error": str(e),
            "success": False
        }
