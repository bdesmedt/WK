"""
Wakuli Retail Analytics - Nmbrs (Visma) Connector
===================================================
Fetches employee, salary, and schedule data from the Nmbrs HR/payroll
platform via the official Python SDK (SOAP API v3).

Supports MULTIPLE Nmbrs companies — data from all configured companies
is merged into one unified dataset.

Data is transformed into the same labor DataFrame format that the KPI
engine expects, allowing seamless replacement of demo labor data with
real HR/payroll figures.

SETUP
-----
1. pip install nmbrs
2. Add credentials to .streamlit/secrets.toml:
       NMBRS_USERNAME = "user@company.com"
       NMBRS_TOKEN    = "your-api-token"
       NMBRS_DOMAIN   = "your-domain"          # optional
       NMBRS_ENV      = "production"            # or "sandbox"
3. Configure company IDs in config.py → NMBRS_CONFIG["companies"]
   (use the "List All Companies" button in Settings to discover IDs)
4. Map Nmbrs departments/cost centers to store codes in
   config.py → NMBRS_DEPARTMENT_TO_STORE
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from config import (
    STORE_LOCATIONS, APP_CONFIG,
    NMBRS_CONFIG, NMBRS_DEPARTMENT_TO_STORE,
)


# ──────────────────────────────────────────────
# CONNECTION HELPERS
# ──────────────────────────────────────────────

def _get_secret(key, default=""):
    """Safely get a secret from Streamlit secrets or environment."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)


def _get_nmbrs_client():
    """Create and authenticate an Nmbrs API client.

    Returns an authenticated Nmbrs client or None if credentials
    are missing or authentication fails.
    """
    username = _get_secret("NMBRS_USERNAME", "")
    token = _get_secret("NMBRS_TOKEN", "")
    domain = _get_secret("NMBRS_DOMAIN", "")
    env = _get_secret("NMBRS_ENV", "production")

    if not username or not token:
        return None

    try:
        from nmbrs import Nmbrs
        sandbox = (env.lower() == "sandbox")

        if domain:
            api = Nmbrs(
                username=username,
                token=token,
                domain=domain,
                auth_type="domain",
                sandbox=sandbox,
            )
        else:
            api = Nmbrs(
                username=username,
                token=token,
                sandbox=sandbox,
            )
        return api
    except ImportError:
        st.warning("Nmbrs package not installed. Run: pip install nmbrs")
        return None
    except Exception as e:
        st.error(f"Nmbrs authentication failed: {e}")
        return None


def _get_company_ids():
    """Get the list of configured Nmbrs company IDs.

    Returns a dict of {company_id: label} from NMBRS_CONFIG["companies"].
    """
    companies = NMBRS_CONFIG.get("companies", {})
    if companies:
        return companies
    return {}


def is_nmbrs_configured():
    """Check whether Nmbrs credentials are present (without connecting)."""
    return bool(_get_secret("NMBRS_USERNAME", "")) and bool(_get_secret("NMBRS_TOKEN", ""))


# ──────────────────────────────────────────────
# EMPLOYEE DATA
# ──────────────────────────────────────────────

def _resolve_store_from_department(department_name, cost_center=None):
    """Map an Nmbrs department or cost center to a Wakuli store code.

    Checks NMBRS_DEPARTMENT_TO_STORE for:
      1. Exact department name match
      2. Exact cost center match
      3. Substring match on department name
    Falls back to "OOH" (overhead) if no mapping found.
    """
    mapping = NMBRS_DEPARTMENT_TO_STORE

    # Exact match on department
    if department_name and department_name in mapping:
        return mapping[department_name]

    # Exact match on cost center
    if cost_center and cost_center in mapping:
        return mapping[cost_center]

    # Substring match (e.g. "Linnaeusstraat" in "Store - Linnaeusstraat")
    if department_name:
        dept_lower = department_name.lower()
        for key, store_code in mapping.items():
            if key.lower() in dept_lower or dept_lower in key.lower():
                return store_code

    return "OOH"


def _fetch_employees_for_company(api, company_id, company_label):
    """Fetch employees for a single Nmbrs company. Internal helper.

    Returns a list of dicts (rows), one per employee.
    """
    try:
        from nmbrs import serialize
    except ImportError:
        return []

    try:
        employees = api.employee.get_by_company(company_id=company_id)
        if not employees:
            return []
    except Exception as e:
        st.warning(f"Could not fetch employees from {company_label}: {e}")
        return []

    rows = []
    for emp in employees:
        emp_data = serialize(emp) if not isinstance(emp, dict) else emp
        emp_id = emp_data.get("id") or emp_data.get("Id") or emp_data.get("employee_id")
        name = emp_data.get("display_name") or emp_data.get("DisplayName") or emp_data.get("name", "")

        # Fetch department for this employee
        department = ""
        cost_center = ""
        try:
            dept_obj = api.employee.department.get_current(employee_id=emp_id)
            if dept_obj:
                dept_data = serialize(dept_obj) if not isinstance(dept_obj, dict) else dept_obj
                department = (dept_data.get("description") or dept_data.get("Description")
                              or dept_data.get("name") or "")
        except Exception:
            pass

        try:
            cc_list = api.employee.cost_center.get_current(employee_id=emp_id)
            if cc_list:
                cc_data = serialize(cc_list) if not isinstance(cc_list, (dict, list)) else cc_list
                if isinstance(cc_data, list) and cc_data:
                    cc_data = cc_data[0]
                if isinstance(cc_data, dict):
                    cost_center = (cc_data.get("code") or cc_data.get("Code")
                                   or cc_data.get("description") or "")
        except Exception:
            pass

        # Resolve store
        store_code = _resolve_store_from_department(department, cost_center)

        # Fetch schedule for FTE factor
        fte_factor = 1.0
        try:
            schedule = api.employee.schedule.get_current(employee_id=emp_id)
            if schedule:
                sched_data = serialize(schedule) if not isinstance(schedule, dict) else schedule
                hours_per_week = (sched_data.get("hours_per_week")
                                  or sched_data.get("HoursPerWeek")
                                  or 0)
                if hours_per_week and float(hours_per_week) > 0:
                    ft_hours = NMBRS_CONFIG.get("full_time_hours", 40)
                    fte_factor = float(hours_per_week) / ft_hours
        except Exception:
            pass

        # Fetch employment info for start date
        start_date = ""
        job_title = ""
        try:
            employments = api.employee.employment.get_all(employee_id=emp_id)
            if employments:
                emp_list = serialize(employments) if not isinstance(employments, list) else employments
                if isinstance(emp_list, list) and emp_list:
                    latest = emp_list[-1] if isinstance(emp_list[-1], dict) else serialize(emp_list[-1])
                    start_date = (latest.get("start_date") or latest.get("StartDate")
                                  or latest.get("start_period") or "")
                    job_title = (latest.get("job_title") or latest.get("JobTitle")
                                 or latest.get("jobtitle") or "")
        except Exception:
            pass

        rows.append({
            "employee_id": emp_id,
            "name": name,
            "department": department,
            "cost_center": cost_center,
            "store_code": store_code,
            "store_name": STORE_LOCATIONS.get(store_code, {}).get("name", store_code),
            "job_title": job_title,
            "start_date": str(start_date)[:10] if start_date else "",
            "fte_factor": round(fte_factor, 2),
            "nmbrs_company_id": company_id,
            "nmbrs_company": company_label,
        })

    return rows


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_nmbrs_employees(company_id=None):
    """Fetch all active employees from Nmbrs across all configured companies.

    If company_id is provided, fetches only that company.
    Otherwise fetches all companies listed in NMBRS_CONFIG["companies"].

    Returns a DataFrame with columns:
        employee_id, name, department, cost_center, store_code, store_name,
        job_title, start_date, fte_factor, nmbrs_company_id, nmbrs_company
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    # Determine which companies to query
    if company_id is not None:
        companies = {company_id: _get_company_ids().get(company_id, f"Company {company_id}")}
    else:
        companies = _get_company_ids()

    if not companies:
        st.warning("No Nmbrs companies configured. Use the Settings tab to discover company IDs "
                    "and add them to NMBRS_CONFIG['companies'] in config.py.")
        return pd.DataFrame()

    all_rows = []
    for cid, label in companies.items():
        rows = _fetch_employees_for_company(api, cid, label)
        all_rows.extend(rows)

    if not all_rows:
        return pd.DataFrame()

    return pd.DataFrame(all_rows)


# ──────────────────────────────────────────────
# SALARY DATA
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_nmbrs_salary_data(company_id=None):
    """Fetch salary/wage data for all employees across all configured companies.

    If company_id is provided, fetches only that company.

    Returns a DataFrame with columns:
        employee_id, name, store_code, store_name, department,
        gross_salary_month, employer_cost_month, fte_factor,
        nmbrs_company_id, nmbrs_company
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    # Get employees first (handles multi-company internally)
    emp_df = fetch_nmbrs_employees(company_id)
    if emp_df.empty:
        return pd.DataFrame()

    try:
        from nmbrs import serialize
    except ImportError:
        return pd.DataFrame()

    rows = []
    for _, emp_row in emp_df.iterrows():
        emp_id = emp_row["employee_id"]

        # Get current salary
        gross_salary = 0
        try:
            salary = api.employee.salary.get_current(employee_id=emp_id)
            if salary:
                sal_data = serialize(salary) if not isinstance(salary, dict) else salary
                gross_salary = float(
                    sal_data.get("value") or sal_data.get("Value")
                    or sal_data.get("gross_salary") or 0
                )
        except Exception:
            pass

        # Estimated employer cost (gross + ~30% social charges in NL)
        employer_burden = NMBRS_CONFIG.get("employer_burden_pct", 0.30)
        employer_cost = gross_salary * (1 + employer_burden)

        rows.append({
            "employee_id": emp_id,
            "name": emp_row["name"],
            "store_code": emp_row["store_code"],
            "store_name": emp_row["store_name"],
            "department": emp_row["department"],
            "gross_salary_month": round(gross_salary, 2),
            "employer_cost_month": round(employer_cost, 2),
            "fte_factor": emp_row["fte_factor"],
            "nmbrs_company_id": emp_row["nmbrs_company_id"],
            "nmbrs_company": emp_row["nmbrs_company"],
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ──────────────────────────────────────────────
# LABOR DATA BUILDER (dashboard-ready format)
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def build_labor_data_from_nmbrs(revenue_df, years_tuple, company_id=None):
    """Build the labor DataFrame in the format expected by the KPI engine.

    Combines Nmbrs employee/salary data (from ALL configured companies)
    with revenue data to produce the same columns as
    demo_data.generate_labor_data():
        year, month, store_code, store_name, revenue, fte_count,
        total_labor_hours, labor_cost, labor_cost_pct,
        revenue_per_labor_hour, transactions_per_labor_hour,
        revenue_per_employee

    The approach:
    - Employee headcount + FTE factor → fte_count per store (merged across companies)
    - Salary data → labor_cost per store per month (merged across companies)
    - Schedule hours → total_labor_hours per store per month
    - Revenue data → compute efficiency ratios
    """
    salary_df = fetch_nmbrs_salary_data(company_id)
    if salary_df.empty:
        return pd.DataFrame()

    # Aggregate FTE and salary by store (employees from multiple companies
    # working at the same store are summed together)
    store_agg = salary_df.groupby(["store_code", "store_name"]).agg(
        headcount=("employee_id", "count"),
        total_fte=("fte_factor", "sum"),
        total_monthly_cost=("employer_cost_month", "sum"),
    ).reset_index()

    if revenue_df.empty:
        return pd.DataFrame()

    monthly_rev = revenue_df.groupby(
        ["year", "month", "store_code", "store_name"]
    )["revenue"].sum().reset_index()

    ft_hours_week = NMBRS_CONFIG.get("full_time_hours", 40)
    avg_weeks_per_month = 4.33

    rows = []
    for _, rev_row in monthly_rev.iterrows():
        sc = rev_row["store_code"]
        store_info = store_agg[store_agg["store_code"] == sc]

        if store_info.empty:
            # No Nmbrs employees mapped to this store — skip
            continue

        info = store_info.iloc[0]
        fte_count = info["total_fte"]
        labor_cost = info["total_monthly_cost"]
        total_labor_hours = fte_count * ft_hours_week * avg_weeks_per_month

        revenue = rev_row["revenue"]
        rev_per_hour = revenue / total_labor_hours if total_labor_hours > 0 else 0
        labor_pct = labor_cost / revenue if revenue > 0 else 0

        # Estimate transactions (using avg ticket from config targets)
        avg_ticket = 6.50  # fallback
        transactions = int(revenue / avg_ticket) if avg_ticket > 0 else 0
        trans_per_hour = transactions / total_labor_hours if total_labor_hours > 0 else 0

        rows.append({
            "year": rev_row["year"],
            "month": rev_row["month"],
            "store_code": sc,
            "store_name": rev_row["store_name"],
            "revenue": round(revenue, 2),
            "fte_count": round(fte_count, 1),
            "total_labor_hours": round(total_labor_hours, 0),
            "labor_cost": round(labor_cost, 2),
            "labor_cost_pct": round(labor_pct, 3),
            "revenue_per_labor_hour": round(rev_per_hour, 2),
            "transactions_per_labor_hour": round(trans_per_hour, 1),
            "revenue_per_employee": round(revenue / fte_count, 2) if fte_count > 0 else 0,
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ──────────────────────────────────────────────
# DIAGNOSTICS
# ──────────────────────────────────────────────

def check_nmbrs_connection():
    """Test the Nmbrs connection and return status info.

    Returns a dict with: connected, companies (list of {id, name, employee_count}), error
    """
    result = {
        "connected": False,
        "companies": [],
        "all_companies": [],
        "total_employees": 0,
        "error": "",
    }

    if not is_nmbrs_configured():
        result["error"] = "Nmbrs credentials not configured"
        return result

    api = _get_nmbrs_client()
    if api is None:
        result["error"] = "Failed to create Nmbrs client"
        return result

    configured_ids = set(_get_company_ids().keys())

    try:
        from nmbrs import serialize

        # Get ALL companies the user has access to
        companies = api.company.get_all()
        if companies:
            result["connected"] = True

            for c in companies:
                c_data = serialize(c) if not isinstance(c, dict) else c
                c_id = c_data.get("id") or c_data.get("Id")
                c_name = c_data.get("name") or c_data.get("Name") or ""
                c_number = c_data.get("number") or c_data.get("Number") or ""

                # Count employees for this company
                emp_count = 0
                try:
                    emps = api.employee.get_by_company(company_id=c_id)
                    emp_count = len(emps) if emps else 0
                except Exception:
                    pass

                entry = {
                    "id": c_id,
                    "name": c_name,
                    "number": c_number,
                    "employee_count": emp_count,
                    "configured": c_id in configured_ids,
                }
                result["all_companies"].append(entry)

                if c_id in configured_ids:
                    result["companies"].append(entry)
                    result["total_employees"] += emp_count

    except Exception as e:
        result["error"] = str(e)

    return result


def fetch_nmbrs_departments(company_id=None):
    """Fetch all departments from Nmbrs for mapping configuration.

    If company_id is None, fetches from all configured companies.
    Returns a DataFrame with: type, id, description, nmbrs_company_id, nmbrs_company.
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    if company_id is not None:
        companies = {company_id: _get_company_ids().get(company_id, f"Company {company_id}")}
    else:
        companies = _get_company_ids()

    if not companies:
        return pd.DataFrame()

    try:
        from nmbrs import serialize
    except ImportError:
        return pd.DataFrame()

    all_rows = []
    for cid, label in companies.items():
        try:
            employees = api.employee.get_by_company(company_id=cid)
            if not employees:
                continue
        except Exception:
            continue

        departments = set()
        cost_centers = set()

        for emp in employees:
            emp_data = serialize(emp) if not isinstance(emp, dict) else emp
            emp_id = emp_data.get("id") or emp_data.get("Id") or emp_data.get("employee_id")

            try:
                dept = api.employee.department.get_current(employee_id=emp_id)
                if dept:
                    d = serialize(dept) if not isinstance(dept, dict) else dept
                    desc = d.get("description") or d.get("Description") or d.get("name") or ""
                    d_id = d.get("id") or d.get("Id") or ""
                    if desc:
                        departments.add((d_id, desc))
            except Exception:
                pass

            try:
                cc = api.employee.cost_center.get_current(employee_id=emp_id)
                if cc:
                    cc_data = serialize(cc) if not isinstance(cc, (dict, list)) else cc
                    if isinstance(cc_data, list):
                        for item in cc_data:
                            if isinstance(item, dict):
                                code = item.get("code") or item.get("Code") or ""
                                desc = item.get("description") or item.get("Description") or ""
                                if code or desc:
                                    cost_centers.add((code, desc))
                    elif isinstance(cc_data, dict):
                        code = cc_data.get("code") or cc_data.get("Code") or ""
                        desc = cc_data.get("description") or cc_data.get("Description") or ""
                        if code or desc:
                            cost_centers.add((code, desc))
            except Exception:
                pass

        for d_id, desc in departments:
            all_rows.append({
                "type": "department",
                "id": d_id,
                "description": desc,
                "nmbrs_company_id": cid,
                "nmbrs_company": label,
            })
        for code, desc in cost_centers:
            all_rows.append({
                "type": "cost_center",
                "id": code,
                "description": desc,
                "nmbrs_company_id": cid,
                "nmbrs_company": label,
            })

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
