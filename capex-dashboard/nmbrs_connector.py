"""
Wakuli Retail Analytics - Nmbrs (Visma) Connector
===================================================
Fetches employee, salary, and schedule data from the Nmbrs HR/payroll
platform via the official Python SDK (SOAP API v3).

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
3. Set NMBRS_COMPANY_ID in config.py (or in secrets)
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


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_nmbrs_employees(company_id=None):
    """Fetch all active employees from Nmbrs with their department and contract info.

    Returns a DataFrame with columns:
        employee_id, name, department, cost_center, store_code, store_name,
        job_title, start_date, fte_factor
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    if company_id is None:
        company_id = NMBRS_CONFIG.get("company_id") or int(_get_secret("NMBRS_COMPANY_ID", "0"))

    if not company_id:
        st.warning("NMBRS_COMPANY_ID not configured.")
        return pd.DataFrame()

    try:
        from nmbrs import serialize

        # Get all employees for the company
        employees = api.employee.get_by_company(company_id=company_id)
        if not employees:
            return pd.DataFrame()

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
                        # Full-time = 40h/week in NL
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
            })

        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"Error fetching Nmbrs employees: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────
# SALARY DATA
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_nmbrs_salary_data(company_id=None, year=None):
    """Fetch salary/wage component data for all employees.

    Retrieves the current salary per employee and calculates monthly
    labor cost including employer burden (social charges, pension, etc.).

    Returns a DataFrame with columns:
        employee_id, name, store_code, store_name, gross_salary_month,
        employer_cost_month, fte_factor
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    if company_id is None:
        company_id = NMBRS_CONFIG.get("company_id") or int(_get_secret("NMBRS_COMPANY_ID", "0"))

    if not company_id:
        return pd.DataFrame()

    # First get employee list with store mapping
    emp_df = fetch_nmbrs_employees(company_id)
    if emp_df.empty:
        return pd.DataFrame()

    try:
        from nmbrs import serialize

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
            })

        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"Error fetching Nmbrs salary data: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────
# LABOR DATA BUILDER (dashboard-ready format)
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def build_labor_data_from_nmbrs(revenue_df, years_tuple, company_id=None):
    """Build the labor DataFrame in the format expected by the KPI engine.

    Combines Nmbrs employee/salary data with revenue data to produce
    the same columns as demo_data.generate_labor_data():
        year, month, store_code, store_name, revenue, fte_count,
        total_labor_hours, labor_cost, labor_cost_pct,
        revenue_per_labor_hour, transactions_per_labor_hour,
        revenue_per_employee

    The approach:
    - Employee headcount + FTE factor → fte_count per store
    - Salary data → labor_cost per store per month
    - Schedule hours → total_labor_hours per store per month
    - Revenue data → compute efficiency ratios
    """
    if company_id is None:
        company_id = NMBRS_CONFIG.get("company_id") or int(_get_secret("NMBRS_COMPANY_ID", "0"))

    salary_df = fetch_nmbrs_salary_data(company_id)
    if salary_df.empty:
        return pd.DataFrame()

    emp_df = fetch_nmbrs_employees(company_id)
    if emp_df.empty:
        return pd.DataFrame()

    # Aggregate FTE and salary by store
    store_agg = salary_df.groupby(["store_code", "store_name"]).agg(
        headcount=("employee_id", "count"),
        total_fte=("fte_factor", "sum"),
        total_monthly_cost=("employer_cost_month", "sum"),
    ).reset_index()

    # We produce one row per store per month, using the current snapshot
    # of headcount/salary (Nmbrs gives current state; historical payroll
    # runs would require the ReportService which needs extra permissions)
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

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# DIAGNOSTICS
# ──────────────────────────────────────────────

def check_nmbrs_connection():
    """Test the Nmbrs connection and return status info.

    Returns a dict with: connected, company_name, employee_count, error
    """
    result = {
        "connected": False,
        "company_name": "",
        "employee_count": 0,
        "error": "",
    }

    if not is_nmbrs_configured():
        result["error"] = "Nmbrs credentials not configured"
        return result

    api = _get_nmbrs_client()
    if api is None:
        result["error"] = "Failed to create Nmbrs client"
        return result

    company_id = NMBRS_CONFIG.get("company_id") or int(_get_secret("NMBRS_COMPANY_ID", "0"))

    try:
        from nmbrs import serialize

        # Try to get companies the user has access to
        companies = api.company.get_all()
        if companies:
            result["connected"] = True
            for c in companies:
                c_data = serialize(c) if not isinstance(c, dict) else c
                c_id = c_data.get("id") or c_data.get("Id")
                c_name = c_data.get("name") or c_data.get("Name") or ""
                if c_id == company_id:
                    result["company_name"] = c_name
                    break

            if not result["company_name"] and companies:
                first = serialize(companies[0]) if not isinstance(companies[0], dict) else companies[0]
                result["company_name"] = first.get("name") or first.get("Name") or "Unknown"

        # Count employees
        if company_id:
            employees = api.employee.get_by_company(company_id=company_id)
            result["employee_count"] = len(employees) if employees else 0

    except Exception as e:
        result["error"] = str(e)

    return result


def fetch_nmbrs_departments(company_id=None):
    """Fetch all departments from Nmbrs for mapping configuration.

    Returns a DataFrame with: id, description (department name).
    Use this to set up NMBRS_DEPARTMENT_TO_STORE mapping.
    """
    api = _get_nmbrs_client()
    if api is None:
        return pd.DataFrame()

    if company_id is None:
        company_id = NMBRS_CONFIG.get("company_id") or int(_get_secret("NMBRS_COMPANY_ID", "0"))

    try:
        from nmbrs import serialize

        # Departments are at the debtor level, but we can read them
        # from employee data or company-level methods
        employees = api.employee.get_by_company(company_id=company_id)
        if not employees:
            return pd.DataFrame()

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

        rows = []
        for d_id, desc in departments:
            rows.append({"type": "department", "id": d_id, "description": desc})
        for code, desc in cost_centers:
            rows.append({"type": "cost_center", "id": code, "description": desc})

        return pd.DataFrame(rows) if rows else pd.DataFrame()

    except Exception as e:
        st.error(f"Error fetching Nmbrs departments: {e}")
        return pd.DataFrame()
