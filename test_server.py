#!/usr/bin/env python3
"""
Test script to demonstrate the P6 XER MCP Server functionality
"""


def demonstrate_functionality():
    """
    This script demonstrates how the MCP server tools would work.
    Note: This requires an actual XER file to test with.
    """

    print("P6 XER MCP Server - Tool Demonstrations")
    print("=" * 50)

    print("\n🔧 Available Tools:")
    tools = [
        "parse_xer_file(file_path) - Parse XER file and get basic project info",
        "get_project_activities(file_path, project_id?) - Get activities from project",
        "get_critical_path(file_path, project_id?) - Find critical path activities",
        "analyze_resource_utilization(file_path) - Analyze resource usage",
        "check_schedule_quality(file_path, project_id?) - Check schedule quality",
    ]

    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool}")

    print("\n📋 Available Resources:")
    resources = [
        "xer-project://{file_path}/{project_id} - Get detailed project information",
        "xer-activities://{file_path} - Get activities summary",
        "xer-resources://{file_path} - Get resources summary",
    ]

    for i, resource in enumerate(resources, 1):
        print(f"{i}. {resource}")

    print("\n💬 Available Prompts:")
    prompts = [
        "analyze_xer_project(file_path, analysis_type) - Generate analysis prompts",
        "xer_reporting_prompt(file_path, report_type) - Generate reporting prompts",
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"{i}. {prompt}")

    print("\n🎯 Analysis Types for prompts:")
    analysis_types = ["general", "schedule", "resources", "progress", "quality"]
    print(f"- Analysis types: {', '.join(analysis_types)}")

    report_types = ["executive", "detailed", "critical_path", "resource", "milestone"]
    print(f"- Report types: {', '.join(report_types)}")

    print("\n📝 Example Usage:")
    print("1. Start the MCP server: uv run --with mcp mcp run server.py")
    print("2. Connect from your AI assistant or MCP client")
    print("3. Use tools like: parse_xer_file('/path/to/project.xer')")
    print("4. Access resources like: xer-project:///path/to/project.xer/1")
    print("5. Generate prompts for analysis and reporting")

    print("\n✅ Server ready! The MCP server provides comprehensive")
    print("   Primavera P6 XER file analysis capabilities including:")
    print("   • Project parsing and data extraction")
    print("   • Critical path analysis")
    print("   • Resource utilization analysis")
    print("   • Schedule quality checks")
    print("   • Flexible reporting and analysis prompts")


if __name__ == "__main__":
    demonstrate_functionality()
