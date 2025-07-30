"""
Primavera P6 XER MCP Server
========================

This is a server for Primavera P6 XER files using the MCP framework.
run: uv run --with mcp mcp run server.py
"""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from xerparser.reader import Reader  # type: ignore

# Create an MCP server
mcp = FastMCP("p6xer-mcp-server")


# Add tools below
@mcp.tool()
def parse_xer_file(file_path: str) -> Dict[str, Any]:
    """Parse a Primavera P6 XER file and return basic project information"""
    try:
        xer = Reader(file_path)

        result = {
            "file_path": file_path,
            "projects": [],
            "total_activities": len(list(xer.activities)),
            "total_resources": len(list(xer.resources)),
            "total_calendars": len(list(xer.calendars)),
        }

        # Get project information
        for project in xer.projects:
            project_info = {
                "proj_id": str(project.proj_id),
                "proj_short_name": str(project.proj_short_name)
                if project.proj_short_name
                else "",
                "proj_name": str(getattr(project, "proj_name", "")),
                "activities_count": len(list(project.activities))
                if hasattr(project, "activities")
                else 0,
                "start_date": str(getattr(project, "scd_start_date", None))
                if getattr(project, "scd_start_date", None)
                else None,
                "finish_date": str(getattr(project, "scd_end_date", None))
                if getattr(project, "scd_end_date", None)
                else None,
            }
            result["projects"].append(project_info)

        return result
    except Exception as e:
        return {"error": f"Failed to parse XER file: {str(e)}"}


@mcp.tool()
def get_project_activities(
    file_path: str, project_id: str | None = None
) -> Dict[str, Any]:
    """Get activities from an XER file, optionally filtered by project ID"""
    try:
        xer = Reader(file_path)
        activities = []

        # Filter activities by project if specified
        if project_id:
            target_activities = [
                act for act in xer.activities if str(act.proj_id) == project_id
            ]
        else:
            target_activities = list(xer.activities)

        for activity in target_activities:
            activity_info = {
                "task_id": str(activity.task_id),
                "task_code": str(activity.task_code) if activity.task_code else "",
                "task_name": str(activity.task_name) if activity.task_name else "",
                "duration": getattr(activity, "duration", None),
                "status_code": str(getattr(activity, "status_code", "")),
                "percent_complete": getattr(activity, "phys_complete_pct", None),
                "start_date": str(getattr(activity, "act_start_date", None))
                if getattr(activity, "act_start_date", None)
                else None,
                "finish_date": str(getattr(activity, "act_end_date", None))
                if getattr(activity, "act_end_date", None)
                else None,
                "total_float": getattr(activity, "total_float_hr_cnt", None),
            }
            activities.append(activity_info)

        return {
            "file_path": file_path,
            "project_id": project_id,
            "activities_count": len(activities),
            "activities": activities,
        }
    except Exception as e:
        return {"error": f"Failed to get activities: {str(e)}"}


@mcp.tool()
def get_critical_path(file_path: str, project_id: str | None = None) -> Dict[str, Any]:
    """Find critical path activities (activities with zero or negative total float)"""
    try:
        xer = Reader(file_path)
        critical_activities = []

        # Filter activities by project if specified
        if project_id:
            target_activities = [
                act for act in xer.activities if str(act.proj_id) == project_id
            ]
        else:
            target_activities = list(xer.activities)

        for activity in target_activities:
            total_float = getattr(activity, "total_float_hr_cnt", None)
            if total_float is not None and total_float <= 0:
                activity_info = {
                    "task_id": str(activity.task_id),
                    "task_code": str(activity.task_code) if activity.task_code else "",
                    "task_name": str(activity.task_name) if activity.task_name else "",
                    "duration": getattr(activity, "duration", None),
                    "total_float": total_float,
                    "start_date": str(getattr(activity, "act_start_date", None))
                    if getattr(activity, "act_start_date", None)
                    else None,
                    "finish_date": str(getattr(activity, "act_end_date", None))
                    if getattr(activity, "act_end_date", None)
                    else None,
                }
                critical_activities.append(activity_info)

        return {
            "file_path": file_path,
            "project_id": project_id,
            "critical_activities_count": len(critical_activities),
            "critical_activities": critical_activities,
        }
    except Exception as e:
        return {"error": f"Failed to get critical path: {str(e)}"}


@mcp.tool()
def analyze_resource_utilization(file_path: str) -> Dict[str, Any]:
    """Analyze resource utilization from an XER file"""
    try:
        xer = Reader(file_path)
        resource_analysis = []

        for resource in xer.resources:
            # Find all assignments for this resource
            assignments = [
                a
                for a in xer.activityresources
                if str(a.rsrc_id) == str(resource.rsrc_id)
            ]

            total_hours = sum(getattr(a, "target_qty", 0) or 0 for a in assignments)
            total_cost = sum(getattr(a, "target_cost", 0) or 0 for a in assignments)

            resource_info = {
                "rsrc_id": str(resource.rsrc_id),
                "rsrc_name": str(getattr(resource, "rsrc_name", "")),
                "rsrc_type": str(getattr(resource, "rsrc_type", "")),
                "assignments_count": len(assignments),
                "total_hours": total_hours,
                "total_cost": total_cost,
            }
            resource_analysis.append(resource_info)

        return {
            "file_path": file_path,
            "resources_count": len(resource_analysis),
            "resources": resource_analysis,
        }
    except Exception as e:
        return {"error": f"Failed to analyze resources: {str(e)}"}


@mcp.tool()
def check_schedule_quality(
    file_path: str, project_id: str | None = None
) -> Dict[str, Any]:
    """Perform schedule quality checks on an XER file"""
    try:
        xer = Reader(file_path)
        issues = []

        # Filter activities by project if specified
        if project_id:
            target_activities = [
                act for act in xer.activities if str(act.proj_id) == project_id
            ]
        else:
            target_activities = list(xer.activities)

        # Check for multiple start activities
        no_predecessors = [
            a
            for a in target_activities
            if not hasattr(a, "predecessors") or not getattr(a, "predecessors", None)
        ]
        if len(no_predecessors) > 1:
            issues.append(
                {
                    "type": "multiple_starts",
                    "description": f"Multiple activities without predecessors: {len(no_predecessors)}",
                    "count": len(no_predecessors),
                }
            )

        # Check for long duration activities (>20 days)
        long_activities = [
            a
            for a in target_activities
            if getattr(a, "duration", 0) and getattr(a, "duration", 0) > 20
        ]
        if long_activities:
            issues.append(
                {
                    "type": "long_duration",
                    "description": f"Activities with duration > 20 days: {len(long_activities)}",
                    "count": len(long_activities),
                }
            )

        # Check for activities without successors
        no_successors = [
            a
            for a in target_activities
            if not hasattr(a, "successors") or not getattr(a, "successors", None)
        ]
        if len(no_successors) > 1:
            issues.append(
                {
                    "type": "multiple_ends",
                    "description": f"Multiple activities without successors: {len(no_successors)}",
                    "count": len(no_successors),
                }
            )

        return {
            "file_path": file_path,
            "project_id": project_id,
            "issues_found": len(issues),
            "issues": issues,
        }
    except Exception as e:
        return {"error": f"Failed to check schedule quality: {str(e)}"}


# Add resources below
@mcp.resource("xer-project://{file_path}/{project_id}")
def xer_project_resource(file_path: str, project_id: str) -> str:
    """Get detailed information about a specific project from an XER file"""
    try:
        xer = Reader(file_path)

        # Find the specific project
        project = None
        for proj in xer.projects:
            if proj.proj_id == project_id:
                project = proj
                break

        if not project:
            return f"Project with ID {project_id} not found in {file_path}"

        # Build detailed project information
        project_details = f"""
Project Details:
================
Project ID: {project.proj_id}
Short Name: {project.proj_short_name}
Full Name: {getattr(project, "proj_name", "N/A")}
Activities: {len(project.activities)}
Start Date: {getattr(project, "scd_start_date", "N/A")}
Finish Date: {getattr(project, "scd_end_date", "N/A")}

Activity Summary:
- Total Activities: {len(project.activities)}
- Completed: {len([a for a in project.activities if getattr(a, "status_code", "") == "TK_Complete"])}
- In Progress: {len([a for a in project.activities if getattr(a, "status_code", "") == "TK_Active"])}
- Not Started: {len([a for a in project.activities if getattr(a, "status_code", "") == "TK_NotStart"])}
"""
        return project_details

    except Exception as e:
        return f"Error accessing project resource: {str(e)}"


@mcp.resource("xer-activities://{file_path}")
def xer_activities_resource(file_path: str) -> str:
    """Get a summary of all activities in an XER file"""
    try:
        xer = Reader(file_path)

        activities_summary = f"""
Activities Summary:
==================
File: {file_path}
Total Activities: {len(xer.activities)}

Status Breakdown:
"""

        # Count activities by status
        status_counts = {}
        for activity in xer.activities:
            status = getattr(activity, "status_code", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            activities_summary += f"- {status}: {count}\n"

        # Add duration statistics
        durations = [
            getattr(a, "duration", 0)
            for a in xer.activities
            if getattr(a, "duration", 0)
        ]
        if durations:
            avg_duration = sum(durations) / len(durations)
            activities_summary += "\nDuration Statistics:\n"
            activities_summary += f"- Average Duration: {avg_duration:.1f} days\n"
            activities_summary += f"- Max Duration: {max(durations)} days\n"
            activities_summary += f"- Min Duration: {min(durations)} days\n"

        return activities_summary

    except Exception as e:
        return f"Error accessing activities resource: {str(e)}"


@mcp.resource("xer-resources://{file_path}")
def xer_resources_resource(file_path: str) -> str:
    """Get a summary of all resources in an XER file"""
    try:
        xer = Reader(file_path)

        resources_summary = f"""
Resources Summary:
=================
File: {file_path}
Total Resources: {len(xer.resources)}

Resource Types:
"""

        # Count resources by type
        type_counts = {}
        for resource in xer.resources:
            res_type = getattr(resource, "rsrc_type", "Unknown")
            type_counts[res_type] = type_counts.get(res_type, 0) + 1

        for res_type, count in type_counts.items():
            resources_summary += f"- {res_type}: {count}\n"

        # Add assignment statistics
        total_assignments = len(list(xer.activityresources))
        resources_summary += "\nAssignment Statistics:\n"
        resources_summary += f"- Total Assignments: {total_assignments}\n"

        if xer.resources:
            avg_assignments = total_assignments / len(xer.resources)
            resources_summary += (
                f"- Average Assignments per Resource: {avg_assignments:.1f}\n"
            )

        return resources_summary

    except Exception as e:
        return f"Error accessing resources resource: {str(e)}"


# Add prompts below
@mcp.prompt()
def analyze_xer_project(file_path: str, analysis_type: str = "general") -> str:
    """Generate a prompt for analyzing a Primavera P6 XER project file"""
    analysis_types = {
        "general": "Provide a comprehensive analysis of this Primavera P6 project, including project overview, schedule health, resource utilization, and key insights.",
        "schedule": "Analyze the project schedule focusing on critical path, schedule quality issues, milestone analysis, and timeline risks.",
        "resources": "Analyze resource allocation, utilization patterns, over-allocation issues, and resource optimization opportunities.",
        "progress": "Analyze project progress including completion percentages, earned value metrics, schedule performance, and variance analysis.",
        "quality": "Perform a schedule quality assessment identifying logic issues, missing links, inappropriate constraints, and scheduling best practices violations.",
    }

    base_prompt = (
        f"Please analyze the Primavera P6 XER file located at: {file_path}\n\n"
    )
    specific_analysis = analysis_types.get(analysis_type, analysis_types["general"])

    return base_prompt + specific_analysis + f"\n\nFocus on: {analysis_type} analysis"


@mcp.prompt()
def xer_reporting_prompt(file_path: str, report_type: str = "executive") -> str:
    """Generate a prompt for creating reports from XER project data"""
    report_types = {
        "executive": "Create an executive summary report highlighting key project metrics, risks, and recommendations for stakeholders.",
        "detailed": "Create a detailed project report including all activities, resources, schedules, and comprehensive analysis.",
        "critical_path": "Create a critical path analysis report showing critical activities, schedule risks, and mitigation strategies.",
        "resource": "Create a resource utilization report showing allocation, costs, and optimization recommendations.",
        "milestone": "Create a milestone tracking report showing key project milestones, dates, and completion status.",
    }

    base_prompt = f"Generate a professional project report from the Primavera P6 XER file: {file_path}\n\n"
    report_focus = report_types.get(report_type, report_types["executive"])

    return base_prompt + f"Report Type: {report_type.title()} Report\n\n" + report_focus
