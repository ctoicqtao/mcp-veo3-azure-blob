#!/usr/bin/env python3
"""
Log viewer for MCP Veo3 Azure Blob server
"""

import os
import sys
from datetime import datetime
import argparse

def view_logs(log_file="mcp_server.log", lines=50, follow=False, filter_term=None):
    """View MCP server logs with filtering options"""
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        print("Make sure the MCP server has been started at least once.")
        return
    
    print(f"📋 Viewing MCP Server Logs: {log_file}")
    print("=" * 60)
    
    try:
        if follow:
            # Follow mode - tail the log file
            import subprocess
            cmd = ["tail", "-f", log_file]
            if lines:
                cmd.extend(["-n", str(lines)])
            subprocess.run(cmd)
        else:
            # Read mode - show last N lines
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # Filter lines if filter term is provided
                if filter_term:
                    all_lines = [line for line in all_lines if filter_term.lower() in line.lower()]
                
                # Show last N lines
                if lines and len(all_lines) > lines:
                    all_lines = all_lines[-lines:]
                
                for line in all_lines:
                    print(line.rstrip())
                    
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def main():
    parser = argparse.ArgumentParser(description="View MCP Veo3 server logs")
    parser.add_argument("--file", "-f", default="mcp_server.log", help="Log file to view")
    parser.add_argument("--lines", "-n", type=int, default=50, help="Number of lines to show")
    parser.add_argument("--follow", action="store_true", help="Follow log file (like tail -f)")
    parser.add_argument("--filter", help="Filter logs containing this term")
    parser.add_argument("--azure", action="store_true", help="Show only Azure-related logs")
    parser.add_argument("--errors", action="store_true", help="Show only error logs")
    parser.add_argument("--requests", action="store_true", help="Show only request logs")
    
    args = parser.parse_args()
    
    # Set filter based on flags
    filter_term = args.filter
    if args.azure:
        filter_term = "azure"
    elif args.errors:
        filter_term = "ERROR"
    elif args.requests:
        filter_term = "veo3_"
    
    print("🔍 MCP Veo3 Azure Blob Log Viewer")
    print("=" * 40)
    
    if filter_term:
        print(f"📌 Filter: '{filter_term}'")
    
    if args.follow:
        print("👀 Following log file (Ctrl+C to exit)")
    else:
        print(f"📄 Showing last {args.lines} lines")
    
    print()
    
    view_logs(
        log_file=args.file,
        lines=args.lines,
        follow=args.follow,
        filter_term=filter_term
    )

if __name__ == "__main__":
    main()
