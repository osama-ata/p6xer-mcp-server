"""
Primavera P6 XER MCP Server
============================
A full-featured MCP server for PyP6XER, exposing:
  • 13 Tools   – parse, query, analyze, and quality-check XER schedules
  • 3 Resources – live project / activities / resources data feeds
  • 2 Prompts   – guided analysis and reporting prompt generators

Run (development / inspector):
    uv run mcp dev src/p6xer_mcp_server/server.py

Run (stdio, for Claude Desktop / Claude Code):
    uv run p6xer-mcp-server
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# ── MCP ──────────────────────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: mcp not installed. Run: pip install 'mcp[cli]'", file=sys.stderr)
    sys.exit(1)

# ── PyP6XER ──────────────────────────────────────────────────────────────────
try:
    from xerparser.reader import Reader  # type: ignore
except ImportError:
    print("Error: PyP6XER not installed. Run: pip install PyP6XER", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP(
    "p6xer-mcp-server",
    instructions=(
        "P6XER — Primavera P6 Schedule Analyzer\n"
        "Use this server to parse, query, and analyze Primavera P6 XER schedule files. "
        "Start with parse_xer_file to load a file, then use the other tools to query "
        "activities, resources, critical path, earned value, and schedule quality."
    ),
)

# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _load(file_path: str) -> Reader:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"XER file not found: {file_path}")
    return Reader(file_path)


def _s(val: Any) -> Any:
    """Safe JSON-serialisable value."""
    if val is None:
        return None
    try:
        json.dumps(val)
        return val
    except (TypeError, ValueError):
        return str(val)


def _d(val: Any) -> str | None:
    """Stringify a date/None safely."""
    return str(val) if val is not None else None


def _activity_dict(a) -> dict:
    return {
        "task_id":            _s(getattr(a, "task_id", None)),
        "task_code":          _s(getattr(a, "task_code", None)),
        "task_name":          _s(getattr(a, "task_name", None)),
        "status_code":        _s(getattr(a, "status_code", None)),
        "task_type":          _s(getattr(a, "task_type", None)),
        "duration":           _s(getattr(a, "duration", None)),
        "total_float_hr_cnt": _s(getattr(a, "total_float_hr_cnt", None)),
        "free_float_hr_cnt":  _s(getattr(a, "free_float_hr_cnt", None)),
        "phys_complete_pct":  _s(getattr(a, "phys_complete_pct", None)),
        "early_start_date":   _d(getattr(a, "early_start_date", None)),
        "early_end_date":     _d(getattr(a, "early_end_date", None)),
        "late_start_date":    _d(getattr(a, "late_start_date", None)),
        "late_end_date":      _d(getattr(a, "late_end_date", None)),
        "act_start_date":     _d(getattr(a, "act_start_date", None)),
        "act_end_date":       _d(getattr(a, "act_end_date", None)),
        "target_start_date":  _d(getattr(a, "target_start_date", None)),
        "target_end_date":    _d(getattr(a, "target_end_date", None)),
        "wbs_id":             _s(getattr(a, "wbs_id", None)),
        "clndr_id":           _s(getattr(a, "clndr_id", None)),
        "proj_id":            _s(getattr(a, "proj_id", None)),
    }


def _project_dict(p) -> dict:
    activities = list(getattr(p, "activities", []))
    return {
        "proj_id":          _s(getattr(p, "proj_id", None)),
        "proj_short_name":  _s(getattr(p, "proj_short_name", None)),
        "proj_name":        _s(getattr(p, "proj_long_name", getattr(p, "proj_name", None))),
        "scd_start_date":   _d(getattr(p, "scd_start_date", getattr(p, "plan_start_date", None))),
        "scd_end_date":     _d(getattr(p, "scd_end_date",   getattr(p, "plan_end_date",   None))),
        "last_recalc_date": _d(getattr(p, "last_recalc_date", None)),
        "activity_count":   len(activities),
        "completed":   sum(1 for a in activities if getattr(a, "status_code", "") == "TK_Complete"),
        "in_progress": sum(1 for a in activities if getattr(a, "status_code", "") == "TK_Active"),
        "not_started": sum(1 for a in activities if getattr(a, "status_code", "") == "TK_NotStart"),
    }


def _resource_dict(r) -> dict:
    return {
        "rsrc_id":        _s(getattr(r, "rsrc_id", None)),
        "rsrc_name":      _s(getattr(r, "rsrc_name", None)),
        "rsrc_short_name":_s(getattr(r, "rsrc_short_name", None)),
        "rsrc_type":      _s(getattr(r, "rsrc_type", None)),
        "email_addr":     _s(getattr(r, "email_addr", None)),
        "parent_rsrc_id": _s(getattr(r, "parent_rsrc_id", None)),
    }


def _wbs_dict(w) -> dict:
    return {
        "wbs_id":        _s(getattr(w, "wbs_id", None)),
        "wbs_name":      _s(getattr(w, "wbs_name", None)),
        "wbs_short_name":_s(getattr(w, "wbs_short_name", None)),
        "parent_wbs_id": _s(getattr(w, "parent_wbs_id", None)),
        "proj_id":       _s(getattr(w, "proj_id", None)),
        "seq_num":       _s(getattr(w, "seq_num", None)),
    }


def _filter_activities(xer: Reader, project_id: str | None, project_short_name: str | None):
    """Return activities filtered by project_id OR project_short_name (both optional)."""
    acts = list(xer.activities)
    if project_id:
        acts = [a for a in acts if str(getattr(a, "proj_id", "")) == str(project_id)]
    elif project_short_name:
        ids = {
            getattr(p, "proj_id", None) for p in xer.projects
            if getattr(p, "proj_short_name", "") == project_short_name
        }
        acts = [a for a in acts if getattr(a, "proj_id", None) in ids]
    return acts


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def parse_xer_file(file_path: str) -> dict:
    """
    Parse a Primavera P6 XER file and return basic project information:
    project list with status breakdowns, total activities, resources, calendars,
    WBS elements, and relationships.
    """
    try:
        xer = _load(file_path)
        return {
            "file_path":           file_path,
            "projects":            [_project_dict(p) for p in xer.projects],
            "total_projects":      len(list(xer.projects)),
            "total_activities":    len(list(xer.activities)),
            "total_resources":     len(list(xer.resources)),
            "total_calendars":     len(list(xer.calendars)),
            "total_wbs":           len(list(xer.wbss)),
            "total_relationships": len(list(xer.relations)),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_project_activities(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
    status: str | None = None,
    task_type: str | None = None,
    limit: int = 100,
) -> dict:
    """
    Get activities from an XER file.

    Filter options:
    - project_id: numeric P6 project ID
    - project_short_name: project short name string
    - status: TK_NotStart | TK_Active | TK_Complete
    - task_type: TT_Task | TT_Mile | TT_FinMile | TT_WBS
    - limit: max rows returned (default 100)
    """
    try:
        xer = _load(file_path)
        acts = _filter_activities(xer, project_id, project_short_name)
        if status:
            acts = [a for a in acts if getattr(a, "status_code", "") == status]
        if task_type:
            acts = [a for a in acts if getattr(a, "task_type", "") == task_type]
        total = len(acts)
        return {
            "file_path":           file_path,
            "project_id":          project_id,
            "project_short_name":  project_short_name,
            "total_matching":      total,
            "returned":            min(total, limit),
            "activities":          [_activity_dict(a) for a in acts[:limit]],
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_critical_path(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
) -> dict:
    """
    Find critical path activities (total float <= 0, incomplete only).
    Results are sorted by early start date ascending.
    Accepts either project_id (numeric) or project_short_name as a filter.
    """
    try:
        xer = _load(file_path)
        acts = _filter_activities(xer, project_id, project_short_name)
        critical = sorted(
            [
                a for a in acts
                if getattr(a, "total_float_hr_cnt", None) is not None
                and float(getattr(a, "total_float_hr_cnt", 1)) <= 0
                and getattr(a, "status_code", "") != "TK_Complete"
            ],
            key=lambda a: str(getattr(a, "early_start_date", None) or ""),
        )
        return {
            "file_path":                file_path,
            "project_id":               project_id,
            "project_short_name":       project_short_name,
            "critical_activities_count":len(critical),
            "critical_activities":      [_activity_dict(a) for a in critical],
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def analyze_resource_utilization(
    file_path: str,
    max_hours_per_year: float = 2080,
) -> dict:
    """
    Summarize resource utilization: planned/actual hours and costs per resource.
    Labor resources (RT_Labor) are flagged as over_allocated if planned hours
    exceed max_hours_per_year (default 2080 = 40 hrs/week x 52 weeks).
    Results are sorted by planned hours descending.
    """
    try:
        xer = _load(file_path)
        rsrc_map = {r.rsrc_id: r for r in xer.resources}
        util: dict[Any, dict] = {}

        for a in xer.activityresources:
            rid = getattr(a, "rsrc_id", None)
            if rid is None:
                continue
            if rid not in util:
                rsrc = rsrc_map.get(rid)
                util[rid] = {
                    "rsrc_id":          _s(rid),
                    "rsrc_name":        _s(getattr(rsrc, "rsrc_name", None)) if rsrc else None,
                    "rsrc_type":        _s(getattr(rsrc, "rsrc_type", None)) if rsrc else None,
                    "assignments_count":0,
                    "total_target_qty": 0.0,
                    "total_target_cost":0.0,
                    "total_actual_qty": 0.0,
                    "total_actual_cost":0.0,
                }
            u = util[rid]
            u["assignments_count"] += 1
            u["total_target_qty"]  += float(getattr(a, "target_qty",  0) or 0)
            u["total_target_cost"] += float(getattr(a, "target_cost", 0) or 0)
            u["total_actual_qty"]  += float(getattr(a, "act_reg_qty", 0) or 0) + float(getattr(a, "act_ot_qty",  0) or 0)
            u["total_actual_cost"] += float(getattr(a, "act_reg_cost",0) or 0) + float(getattr(a, "act_ot_cost", 0) or 0)

        result = []
        for u in util.values():
            u["total_target_qty"]  = round(u["total_target_qty"],  2)
            u["total_target_cost"] = round(u["total_target_cost"], 2)
            u["total_actual_qty"]  = round(u["total_actual_qty"],  2)
            u["total_actual_cost"] = round(u["total_actual_cost"], 2)
            if u["rsrc_type"] == "RT_Labor":
                u["over_allocated"]  = u["total_target_qty"] > max_hours_per_year
                u["utilization_pct"] = round(u["total_target_qty"] / max_hours_per_year * 100, 1)
            result.append(u)

        result.sort(key=lambda x: x["total_target_qty"], reverse=True)
        return {
            "file_path":           file_path,
            "resources_count":     len(result),
            "max_hours_threshold": max_hours_per_year,
            "resources":           result,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def check_schedule_quality(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
    long_duration_days: float = 20,
    high_float_days: float = 44,
) -> dict:
    """
    DCMA-style schedule quality check on open/in-progress activities.

    Identifies:
    - Activities missing predecessors (excluding start milestones)
    - Activities missing successors (excluding finish milestones)
    - Long-duration activities (threshold: long_duration_days, default 20)
    - High-float activities (threshold: high_float_days, default 44)
    - TT_Task activities without any resource assignment
    - Activities missing early start dates
    """
    try:
        xer = _load(file_path)
        HOURS_PER_DAY = 8.0
        acts = _filter_activities(xer, project_id, project_short_name)
        open_acts = [a for a in acts if getattr(a, "status_code", "") in ("TK_NotStart", "TK_Active")]

        # Use relation table for accurate pred/succ detection
        tasks_with_preds = {getattr(r, "task_id",      None) for r in xer.relations}
        tasks_with_succs = {getattr(r, "pred_task_id", None) for r in xer.relations}
        tasks_with_rsrc  = {getattr(a, "task_id",      None) for a in xer.activityresources}

        issues: dict[str, list] = {
            "no_predecessors":        [],
            "no_successors":          [],
            "long_duration":          [],
            "high_float":             [],
            "no_resource_assignment": [],
            "missing_dates":          [],
        }

        for act in open_acts:
            tid    = getattr(act, "task_id",           None)
            tcode  = getattr(act, "task_code",         "?")
            tname  = getattr(act, "task_name",         "?")
            ttype  = getattr(act, "task_type",         "")
            dur    = getattr(act, "duration",          None)
            tfloat = getattr(act, "total_float_hr_cnt",None)
            estart = getattr(act, "early_start_date",  None)
            ref    = {"task_code": tcode, "task_name": tname}

            if tid not in tasks_with_preds and ttype != "TT_Mile":
                issues["no_predecessors"].append(ref)

            if tid not in tasks_with_succs and ttype not in ("TT_FinMile", "TT_Mile"):
                issues["no_successors"].append(ref)

            if dur is not None:
                dur_days = float(dur) / HOURS_PER_DAY
                if dur_days > long_duration_days:
                    issues["long_duration"].append({**ref, "duration_days": round(dur_days, 1)})

            if tfloat is not None:
                float_days = float(tfloat) / HOURS_PER_DAY
                if float_days > high_float_days:
                    issues["high_float"].append({**ref, "float_days": round(float_days, 1)})

            if ttype == "TT_Task" and tid not in tasks_with_rsrc:
                issues["no_resource_assignment"].append(ref)

            if estart is None and ttype != "TT_Mile":
                issues["missing_dates"].append(ref)

        counts = {k: len(v) for k, v in issues.items()}
        return {
            "file_path":                      file_path,
            "project_id":                     project_id,
            "project_short_name":             project_short_name,
            "total_open_activities_checked":  len(open_acts),
            "total_issues_found":             sum(counts.values()),
            "summary":                        counts,
            "details":                        issues,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_resources(
    file_path: str,
    rsrc_type: str | None = None,
) -> dict:
    """
    List all resources in an XER file.
    Optionally filter by type: RT_Labor | RT_Mat | RT_Equip
    """
    try:
        xer = _load(file_path)
        resources = list(xer.resources)
        if rsrc_type:
            resources = [r for r in resources if getattr(r, "rsrc_type", "") == rsrc_type]
        return {"count": len(resources), "resources": [_resource_dict(r) for r in resources]}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_resource_assignments(
    file_path: str,
    rsrc_name: str | None = None,
    task_code: str | None = None,
    limit: int = 100,
) -> dict:
    """
    Get resource-activity assignments, enriched with resource and activity names.
    - rsrc_name: partial match on resource name (case-insensitive)
    - task_code: exact match on activity task code
    """
    try:
        xer = _load(file_path)
        rsrc_map = {r.rsrc_id: r for r in xer.resources}
        task_map = {a.task_id: a for a in xer.activities}
        assignments = list(xer.activityresources)

        if rsrc_name:
            ids = {r.rsrc_id for r in xer.resources
                   if rsrc_name.lower() in (getattr(r, "rsrc_name", "") or "").lower()}
            assignments = [a for a in assignments if getattr(a, "rsrc_id", None) in ids]

        if task_code:
            ids2 = {t.task_id for t in xer.activities
                    if (getattr(t, "task_code", "") or "").lower() == task_code.lower()}
            assignments = [a for a in assignments if getattr(a, "task_id", None) in ids2]

        total = len(assignments)
        result = []
        for a in assignments[:limit]:
            rsrc = rsrc_map.get(getattr(a, "rsrc_id", None))
            task = task_map.get(getattr(a, "task_id", None))
            result.append({
                "taskrsrc_id":  _s(getattr(a,    "taskrsrc_id", None)),
                "task_id":      _s(getattr(a,    "task_id",     None)),
                "task_code":    _s(getattr(task, "task_code",   None)) if task else None,
                "task_name":    _s(getattr(task, "task_name",   None)) if task else None,
                "rsrc_id":      _s(getattr(a,    "rsrc_id",     None)),
                "rsrc_name":    _s(getattr(rsrc,  "rsrc_name",  None)) if rsrc else None,
                "rsrc_type":    _s(getattr(rsrc,  "rsrc_type",  None)) if rsrc else None,
                "target_qty":   _s(getattr(a, "target_qty",     None)),
                "target_cost":  _s(getattr(a, "target_cost",    None)),
                "act_reg_qty":  _s(getattr(a, "act_reg_qty",    None)),
                "act_reg_cost": _s(getattr(a, "act_reg_cost",   None)),
                "act_ot_qty":   _s(getattr(a, "act_ot_qty",     None)),
                "act_ot_cost":  _s(getattr(a, "act_ot_cost",    None)),
            })
        return {"total_matching": total, "returned": len(result), "assignments": result}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_wbs(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
) -> dict:
    """Get the Work Breakdown Structure (WBS) hierarchy, optionally filtered by project."""
    try:
        xer = _load(file_path)
        wbs_list = list(xer.wbss)
        if project_id:
            wbs_list = [w for w in wbs_list if str(getattr(w, "proj_id", "")) == str(project_id)]
        elif project_short_name:
            ids = {getattr(p, "proj_id", None) for p in xer.projects
                   if getattr(p, "proj_short_name", "") == project_short_name}
            wbs_list = [w for w in wbs_list if getattr(w, "proj_id", None) in ids]
        return {"count": len(wbs_list), "wbs": [_wbs_dict(w) for w in wbs_list]}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_relationships(
    file_path: str,
    task_code: str | None = None,
    limit: int = 100,
) -> dict:
    """
    Get activity predecessor/successor relationships, enriched with task codes.
    If task_code is supplied, returns only relationships where that activity
    appears as the successor or as the predecessor.
    """
    try:
        xer = _load(file_path)
        task_map = {a.task_id: a for a in xer.activities}
        rels = list(xer.relations)

        if task_code:
            target = {t.task_id for t in xer.activities
                      if (getattr(t, "task_code", "") or "").lower() == task_code.lower()}
            rels = [r for r in rels
                    if getattr(r, "task_id",      None) in target
                    or getattr(r, "pred_task_id", None) in target]

        total = len(rels)
        result = []
        for r in rels[:limit]:
            task = task_map.get(getattr(r, "task_id",      None))
            pred = task_map.get(getattr(r, "pred_task_id", None))
            result.append({
                "task_pred_id":   _s(getattr(r, "task_pred_id",  None)),
                "task_id":        _s(getattr(r, "task_id",       None)),
                "task_code":      _s(getattr(task, "task_code",  None)) if task else None,
                "pred_task_id":   _s(getattr(r, "pred_task_id",  None)),
                "pred_task_code": _s(getattr(pred, "task_code",  None)) if pred else None,
                "pred_type":      _s(getattr(r, "pred_type",     None)),
                "lag_hr_cnt":     _s(getattr(r, "lag_hr_cnt",    None)),
            })
        return {"total_matching": total, "returned": len(result), "relationships": result}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_calendars(file_path: str) -> dict:
    """List all calendar definitions in the XER file with hours-per-period data."""
    try:
        xer = _load(file_path)
        cals = [
            {
                "clndr_id":    _s(getattr(c, "clndr_id",    None)),
                "clndr_name":  _s(getattr(c, "clndr_name",  None)),
                "clndr_type":  _s(getattr(c, "clndr_type",  None)),
                "day_hr_cnt":  _s(getattr(c, "day_hr_cnt",  None)),
                "week_hr_cnt": _s(getattr(c, "week_hr_cnt", None)),
                "month_hr_cnt":_s(getattr(c, "month_hr_cnt",None)),
                "year_hr_cnt": _s(getattr(c, "year_hr_cnt", None)),
            }
            for c in xer.calendars
        ]
        return {"count": len(cals), "calendars": cals}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_schedule_summary(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
) -> dict:
    """
    Comprehensive schedule summary: activity counts by status, critical activity count,
    milestone count, resource/calendar/WBS/relationship totals, and date range.
    """
    try:
        xer = _load(file_path)
        acts = _filter_activities(xer, project_id, project_short_name)
        total       = len(acts)
        not_started = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_NotStart")
        in_progress = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_Active")
        completed   = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_Complete")
        milestones  = sum(1 for a in acts if getattr(a, "task_type", "") in ("TT_Mile", "TT_FinMile"))
        critical    = sum(
            1 for a in acts
            if getattr(a, "total_float_hr_cnt", None) is not None
            and float(getattr(a, "total_float_hr_cnt", 1)) <= 0
            and getattr(a, "status_code", "") != "TK_Complete"
        )
        starts  = [getattr(a, "target_start_date", None) or getattr(a, "early_start_date", None) for a in acts]
        ends    = [getattr(a, "target_end_date",   None) or getattr(a, "early_end_date",   None) for a in acts]
        starts  = [d for d in starts if d]
        ends    = [d for d in ends   if d]

        return {
            "file_path":          file_path,
            "project_id":         project_id,
            "project_short_name": project_short_name,
            "total_projects":     len(list(xer.projects)),
            "total_activities":   total,
            "status_breakdown": {
                "not_started": not_started,
                "in_progress": in_progress,
                "completed":   completed,
                "other":       total - not_started - in_progress - completed,
            },
            "milestones":          milestones,
            "critical_activities": critical,
            "total_resources":     len(list(xer.resources)),
            "total_calendars":     len(list(xer.calendars)),
            "total_wbs_elements":  len(list(xer.wbss)),
            "total_relationships": len(list(xer.relations)),
            "schedule_start":      str(min(starts)) if starts else None,
            "schedule_finish":     str(max(ends))   if ends   else None,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_earned_value(
    file_path: str,
    project_id: str | None = None,
    project_short_name: str | None = None,
) -> dict:
    """
    Calculate Earned Value Management (EVM) metrics per project:
    PV (Planned Value), EV (Earned Value), AC (Actual Cost),
    CV (Cost Variance), SV (Schedule Variance), CPI, SPI, EAC.
    """
    try:
        xer = _load(file_path)
        projs = list(xer.projects)
        if project_id:
            projs = [p for p in projs if str(getattr(p, "proj_id", "")) == str(project_id)]
        elif project_short_name:
            projs = [p for p in projs if getattr(p, "proj_short_name", "") == project_short_name]

        task_map = {a.task_id: a for a in xer.activities}
        results = []

        for proj in projs:
            pid      = getattr(proj, "proj_id", None)
            task_ids = {a.task_id for a in xer.activities if getattr(a, "proj_id", None) == pid}
            assigns  = [a for a in xer.activityresources if getattr(a, "task_id", None) in task_ids]

            pv = ev = ac = 0.0
            for a in assigns:
                task = task_map.get(getattr(a, "task_id", None))
                tc   = float(getattr(a, "target_cost",  0) or 0)
                arc  = float(getattr(a, "act_reg_cost", 0) or 0)
                aoc  = float(getattr(a, "act_ot_cost",  0) or 0)
                pct  = float(getattr(task, "phys_complete_pct", 0) or 0) if task else 0.0
                pv  += tc
                ev  += tc * (pct / 100.0)
                ac  += arc + aoc

            cpi = round(ev / ac,  4) if ac > 0 else None
            spi = round(ev / pv,  4) if pv > 0 else None
            eac = round(pv / cpi, 2) if cpi and cpi > 0 else None

            results.append({
                "project":           _s(getattr(proj, "proj_short_name", None)),
                "project_id":        _s(pid),
                "planned_value":     round(pv, 2),
                "earned_value":      round(ev, 2),
                "actual_cost":       round(ac, 2),
                "cost_variance":     round(ev - ac, 2),
                "schedule_variance": round(ev - pv, 2),
                "cpi": cpi,
                "spi": spi,
                "eac": eac,
            })

        return {"projects": results}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_activity_detail(file_path: str, task_code: str) -> dict:
    """
    Get full detail for a single activity by its task_code (case-insensitive).
    Returns all scheduling fields plus enriched predecessors, successors,
    and resource assignments with names and costs.
    """
    try:
        xer = _load(file_path)
        activity = next(
            (a for a in xer.activities
             if (getattr(a, "task_code", "") or "").lower() == task_code.lower()),
            None,
        )
        if activity is None:
            return {"error": f"Activity '{task_code}' not found."}

        tid      = getattr(activity, "task_id", None)
        detail   = _activity_dict(activity)
        task_map = {a.task_id: a for a in xer.activities}
        rsrc_map = {r.rsrc_id: r for r in xer.resources}

        preds = [r for r in xer.relations if getattr(r, "task_id",      None) == tid]
        succs = [r for r in xer.relations if getattr(r, "pred_task_id", None) == tid]

        detail["predecessors"] = [
            {
                "pred_task_code": _s(getattr(task_map.get(getattr(r, "pred_task_id", None)), "task_code", None)),
                "pred_task_name": _s(getattr(task_map.get(getattr(r, "pred_task_id", None)), "task_name", None)),
                "pred_type":      _s(getattr(r, "pred_type",  None)),
                "lag_hr_cnt":     _s(getattr(r, "lag_hr_cnt", None)),
            }
            for r in preds
        ]
        detail["successors"] = [
            {
                "succ_task_code": _s(getattr(task_map.get(getattr(r, "task_id", None)), "task_code", None)),
                "succ_task_name": _s(getattr(task_map.get(getattr(r, "task_id", None)), "task_name", None)),
                "pred_type":      _s(getattr(r, "pred_type",  None)),
                "lag_hr_cnt":     _s(getattr(r, "lag_hr_cnt", None)),
            }
            for r in succs
        ]
        detail["resource_assignments"] = [
            {
                "rsrc_name":    _s(getattr(rsrc_map.get(getattr(a, "rsrc_id", None)), "rsrc_name", None)),
                "rsrc_type":    _s(getattr(rsrc_map.get(getattr(a, "rsrc_id", None)), "rsrc_type", None)),
                "target_qty":   _s(getattr(a, "target_qty",   None)),
                "target_cost":  _s(getattr(a, "target_cost",  None)),
                "act_reg_qty":  _s(getattr(a, "act_reg_qty",  None)),
                "act_reg_cost": _s(getattr(a, "act_reg_cost", None)),
            }
            for a in xer.activityresources if getattr(a, "task_id", None) == tid
        ]
        return detail
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES  (live URI-addressed data feeds)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("xer-project://{file_path}/{project_id}")
def xer_project_resource(file_path: str, project_id: str) -> str:
    """Detailed text summary for a specific project from an XER file."""
    try:
        xer  = _load(file_path)
        proj = next(
            (p for p in xer.projects if str(getattr(p, "proj_id", "")) == str(project_id)),
            None,
        )
        if not proj:
            return f"Project '{project_id}' not found in {file_path}"

        acts      = list(getattr(proj, "activities", []))
        completed = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_Complete")
        in_prog   = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_Active")
        not_start = sum(1 for a in acts if getattr(a, "status_code", "") == "TK_NotStart")
        critical  = sum(
            1 for a in acts
            if getattr(a, "total_float_hr_cnt", None) is not None
            and float(getattr(a, "total_float_hr_cnt", 1)) <= 0
            and getattr(a, "status_code", "") != "TK_Complete"
        )
        scd_start = getattr(proj, "scd_start_date", getattr(proj, "plan_start_date", "N/A"))
        scd_end   = getattr(proj, "scd_end_date",   getattr(proj, "plan_end_date",   "N/A"))

        return (
            f"Project Details\n"
            f"===============\n"
            f"ID:           {proj.proj_id}\n"
            f"Short Name:   {getattr(proj, 'proj_short_name', 'N/A')}\n"
            f"Full Name:    {getattr(proj, 'proj_long_name', getattr(proj, 'proj_name', 'N/A'))}\n"
            f"Start Date:   {scd_start}\n"
            f"Finish Date:  {scd_end}\n"
            f"\nActivity Summary\n"
            f"----------------\n"
            f"Total:        {len(acts)}\n"
            f"Not Started:  {not_start}\n"
            f"In Progress:  {in_prog}\n"
            f"Completed:    {completed}\n"
            f"Critical:     {critical}\n"
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("xer-activities://{file_path}")
def xer_activities_resource(file_path: str) -> str:
    """Activities summary: status breakdown and duration statistics for an XER file."""
    try:
        xer  = _load(file_path)
        acts = list(xer.activities)

        status_counts: dict[str, int] = {}
        for a in acts:
            s = getattr(a, "status_code", "Unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        durations = [float(getattr(a, "duration", 0) or 0) for a in acts if getattr(a, "duration", None)]
        dur_section = ""
        if durations:
            avg = sum(durations) / len(durations)
            dur_section = (
                f"\nDuration Statistics (hours)\n"
                f"---------------------------\n"
                f"Average: {avg:.1f}\n"
                f"Max:     {max(durations):.1f}\n"
                f"Min:     {min(durations):.1f}\n"
            )

        status_lines = "\n".join(f"  {k}: {v}" for k, v in sorted(status_counts.items()))
        return (
            f"Activities Summary\n"
            f"==================\n"
            f"File:  {file_path}\n"
            f"Total: {len(acts)}\n"
            f"\nStatus Breakdown\n"
            f"----------------\n"
            f"{status_lines}\n"
            f"{dur_section}"
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("xer-resources://{file_path}")
def xer_resources_resource(file_path: str) -> str:
    """Resources summary: type breakdown and assignment statistics for an XER file."""
    try:
        xer       = _load(file_path)
        resources = list(xer.resources)

        type_counts: dict[str, int] = {}
        for r in resources:
            rt = getattr(r, "rsrc_type", "Unknown")
            type_counts[rt] = type_counts.get(rt, 0) + 1

        total_assigns = len(list(xer.activityresources))
        avg_assign    = total_assigns / len(resources) if resources else 0

        type_lines = "\n".join(f"  {k}: {v}" for k, v in sorted(type_counts.items()))
        return (
            f"Resources Summary\n"
            f"=================\n"
            f"File:              {file_path}\n"
            f"Total Resources:   {len(resources)}\n"
            f"\nResource Types\n"
            f"--------------\n"
            f"{type_lines}\n"
            f"\nAssignment Statistics\n"
            f"---------------------\n"
            f"Total Assignments:            {total_assigns}\n"
            f"Avg Assignments per Resource: {avg_assign:.1f}\n"
        )
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS  (guided AI analysis starters)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.prompt()
def analyze_xer_project(file_path: str, analysis_type: str = "general") -> str:
    """
    Generate an analysis prompt for a Primavera P6 XER project file.

    analysis_type options:
    - general    – comprehensive overview (default)
    - schedule   – critical path, milestones, timeline risks
    - resources  – allocation, over-allocation, optimisation
    - progress   – completion %, earned value, variances
    - quality    – DCMA-style logic and schedule health
    """
    focus_map = {
        "general":  "Provide a comprehensive analysis: project overview, schedule health, resource utilisation, and key insights.",
        "schedule": "Analyse the schedule: critical path activities, milestone tracking, schedule quality issues, and timeline risks.",
        "resources":"Analyse resource allocation and utilisation patterns, flag over-allocated resources, and suggest optimisation opportunities.",
        "progress": "Analyse project progress via completion percentages, earned value metrics (CPI/SPI), schedule/cost variances, and forecast to complete.",
        "quality":  "Perform a DCMA-style schedule quality assessment: missing logic, inappropriate constraints, long durations, high float, and best-practice violations.",
    }
    focus = focus_map.get(analysis_type, focus_map["general"])
    return (
        f"Please analyse the Primavera P6 XER file at: {file_path}\n\n"
        f"Analysis focus ({analysis_type}):\n{focus}\n\n"
        f"Use the available MCP tools — parse_xer_file, get_project_activities, "
        f"get_critical_path, analyze_resource_utilization, check_schedule_quality, "
        f"get_earned_value — to gather the data, then present a clear, structured report."
    )


@mcp.prompt()
def xer_reporting_prompt(file_path: str, report_type: str = "executive") -> str:
    """
    Generate a prompt for creating a professional project report from XER data.

    report_type options:
    - executive      – high-level KPIs and risks for stakeholders (default)
    - detailed       – full activity, resource, and schedule detail
    - critical_path  – critical activities and risk mitigation
    - resource       – utilisation, costs, and optimisation
    - milestone      – milestone status and forecast dates
    """
    report_map = {
        "executive":    "Create an executive summary: key metrics (CPI, SPI, % complete), top risks, and recommendations for senior stakeholders.",
        "detailed":     "Create a detailed report covering all activities, resource assignments, schedule dates, float values, and variance analysis.",
        "critical_path":"Create a critical path report: all critical activities, their dates, float values, schedule risks, and recommended mitigation.",
        "resource":     "Create a resource utilisation report: planned vs actual hours and costs per resource, over-allocation flags, and optimisation recommendations.",
        "milestone":    "Create a milestone tracking report: all milestone activities, planned vs actual dates, and any forecast delays.",
    }
    focus = report_map.get(report_type, report_map["executive"])
    return (
        f"Generate a professional {report_type.title()} Report from: {file_path}\n\n"
        f"{focus}\n\n"
        f"Structure the report with: Executive Summary, Key Findings, Detailed Analysis, "
        f"Risks & Issues, and Recommendations. Use MCP tool data to populate each section."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def run() -> None:
    """Run the MCP server via console script entry point."""
    mcp.run()


if __name__ == "__main__":
    run()
