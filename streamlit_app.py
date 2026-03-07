import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import re
from datetime import datetime

st.set_page_config(
    page_title="Project Management Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CONSTANTS ──────────────────────────────────────────────────
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

STATUS_COLORS = {
    'Todo':                    '#64748b',
    'Preparing Scope of Work': '#8b5cf6',
    'In Dev':                  '#2563eb',
    'Paused':                  '#dc2626',
    'Dev Complete':            '#0f766e',
    'In QA':                   '#7c3aed',
    'In UAT':                  '#0891b2',
    'Pending for Release':     '#d97706',
    'Released':                '#16a34a',
}

STATUS_ORDER = list(STATUS_COLORS.keys())

DEFAULT_PROJECTS = [
    dict(name="Documents V3 Migration",      type="Tech Project",  status="In QA",               priority="", developer="Faizal",   qa="Amruta",  devStart="",              devEnd="",             qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="9th Mar 2026",  description="", link=""),
    dict(name="Payments V3 Migration",        type="Tech Project",  status="Pending for Release",  priority="", developer="Pratik",   qa="",        devStart="",              devEnd="",             qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="3rd Mar 2026",  description="", link=""),
    dict(name="Oncall [2 Mar - 8 Mar '26]",   type="Oncall",        status="In Dev",               priority="", developer="Neeraj",   qa="",        devStart="2nd Mar 2026",  devEnd="8th Mar 2026", qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="",              description="Round-robin rotation every 2 weeks", link=""),
    dict(name="TS 71",                         type="Tech Sprint",   status="In Dev",               priority="", developer="Shreyash", qa="",        devStart="27th Feb 2026", devEnd="4th Mar 2026", qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="",              description="", link=""),
    dict(name="TS 72",                         type="Tech Sprint",   status="In Dev",               priority="", developer="Deveshi",  qa="",        devStart="18th Feb 2026", devEnd="25th Feb 2026",qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="",              description="", link=""),
    dict(name="TS 73",                         type="Tech Sprint",   status="In Dev",               priority="", developer="Himanshu", qa="",        devStart="",              devEnd="",             qaStart="",             qaEnd="",            uatStart="", uatEnd="", releaseDate="",              description="Dates TBD", link=""),
    dict(name="TS 74",                         type="Tech Sprint",   status="In QA",                priority="", developer="Himanshu", qa="Sumanth", devStart="",              devEnd="",             qaStart="27th Feb 2026", qaEnd="5th Mar 2026",uatStart="", uatEnd="", releaseDate="",              description="", link=""),
]

# ── SESSION STATE ───────────────────────────────────────────────
for key, val in [
    ('sheet_url', ''), ('admin_pwd', ''), ('apps_script_url', ''),
    ('admin_mode', False), ('descriptions', {}),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── HELPERS ────────────────────────────────────────────────────
def extract_sheet_id(url):
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    return m.group(1) if m else url

def fmt_date(v, f=None):
    if f:
        s = str(f).strip()
        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%y']:
            try:
                dt = datetime.strptime(s, fmt)
                day = dt.day
                suf = 'th' if day in [11,12,13] else {1:'st',2:'nd',3:'rd'}.get(day % 10, 'th')
                return f"{day}{suf} {MONTHS[dt.month-1]} {dt.year}"
            except:
                pass
        return s
    if not v:
        return ''
    s = str(v)
    m = re.match(r'Date\((\d+),(\d+),(\d+)\)', s)
    if m:
        yr, mo, dy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        suf = 'th' if dy in [11,12,13] else {1:'st',2:'nd',3:'rd'}.get(dy % 10, 'th')
        return f"{dy}{suf} {MONTHS[mo]} {yr}"
    return s

@st.cache_data(ttl=300)
def fetch_data(sheet_url):
    if not sheet_url:
        return pd.DataFrame(DEFAULT_PROJECTS)

    sheet_id = extract_sheet_id(sheet_url)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        match = re.search(r'setResponse\(([\s\S]*?)\);?\s*$', resp.text)
        if not match:
            raise ValueError("Unexpected response format")

        data   = json.loads(match.group(1))
        table  = data['table']
        cols   = [c.get('label', '').lower().strip() for c in table['cols']]

        def get_cell(row, label):
            idx = cols.index(label) if label in cols else -1
            if idx < 0 or idx >= len(row['c']) or not row['c'][idx]:
                return ''
            cell = row['c'][idx]
            v, f = cell.get('v'), cell.get('f')
            if f or (v and str(v).startswith('Date(')):
                return fmt_date(v, f)
            return str(v).strip() if v is not None else ''

        rows = []
        for row in table['rows']:
            if not row or not row.get('c'):
                continue
            name = get_cell(row, 'project name')
            if not name.strip():
                continue
            rows.append(dict(
                name=name,
                type=get_cell(row, 'project type'),
                status=get_cell(row, 'status'),
                priority=get_cell(row, 'priority'),
                developer=get_cell(row, 'developer'),
                qa=get_cell(row, 'qa assignee'),
                devStart=get_cell(row, 'dev start date'),
                devEnd=get_cell(row, 'dev end date'),
                qaStart=get_cell(row, 'qa start date'),
                qaEnd=get_cell(row, 'qa end date'),
                uatStart=get_cell(row, 'uat start date'),
                uatEnd=get_cell(row, 'uat end date'),
                releaseDate=get_cell(row, 'release date'),
                description=get_cell(row, 'description'),
                link=get_cell(row, 'link'),
            ))

        return pd.DataFrame(rows) if rows else pd.DataFrame(DEFAULT_PROJECTS)

    except Exception as e:
        st.warning(f"Could not load sheet: {e}. Showing default data.")
        return pd.DataFrame(DEFAULT_PROJECTS)

# ── PROJECT DETAIL DIALOG ──────────────────────────────────────
@st.dialog("Project Details", width="large")
def project_dialog(project):
    st.markdown(f"### {project['name']}")

    c1, c2, c3 = st.columns(3)
    color = STATUS_COLORS.get(project['status'], '#64748b')
    c1.markdown(f"**Type**  \n{project['type'] or '—'}")
    c2.markdown(
        f"**Status**  \n<span style='background:{color}22;color:{color};"
        f"padding:2px 10px;border-radius:4px;font-size:13px;font-weight:500'>"
        f"{project['status'] or '—'}</span>",
        unsafe_allow_html=True
    )
    c3.markdown(f"**Priority**  \n{project['priority'] or '—'}")

    st.divider()

    c1, c2 = st.columns(2)
    c1.markdown(f"**Developer:** {project['developer'] or '—'}")
    c1.markdown(f"**Dev Start:** {project['devStart'] or '—'}")
    c1.markdown(f"**Dev End:** {project['devEnd'] or '—'}")
    c2.markdown(f"**QA:** {project['qa'] or '—'}")
    c2.markdown(f"**QA Start:** {project['qaStart'] or '—'}")
    c2.markdown(f"**QA End:** {project['qaEnd'] or '—'}")

    if any([project['uatStart'], project['uatEnd'], project['releaseDate']]):
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**UAT Start:** {project['uatStart'] or '—'}")
        c2.markdown(f"**UAT End:** {project['uatEnd'] or '—'}")
        c3.markdown(f"**Release Date:** {project['releaseDate'] or '—'}")

    st.divider()

    stored = st.session_state.descriptions.get(project['name'], {})
    desc   = stored.get('description', project.get('description', ''))
    link   = stored.get('link',        project.get('link', ''))

    if st.session_state.admin_mode:
        new_desc = st.text_area("Description", value=desc, height=120)
        new_link = st.text_input("Link / Document URL", value=link)

        if st.button("Save Changes", type="primary"):
            st.session_state.descriptions[project['name']] = {
                'description': new_desc, 'link': new_link
            }
            apps_url = st.session_state.apps_script_url
            if apps_url:
                try:
                    requests.post(apps_url, json={
                        'name': project['name'], 'description': new_desc,
                        'link': new_link, 'token': st.session_state.admin_pwd
                    }, timeout=5)
                except:
                    pass
            st.success("Saved!")
            st.rerun()
    else:
        if desc:
            st.markdown(f"**Description**")
            st.write(desc)
        else:
            st.caption("No description added yet.")
        if link:
            st.markdown(f"**Link:** [{link}]({link})")

# ── MAIN ───────────────────────────────────────────────────────
def main():
    # Custom CSS
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] > .main { background: #f4f6f8; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    [data-testid="metric-container"] {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 16px !important;
    }
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    [data-testid="stSidebar"] input { color: #1a2332 !important; }
    div[data-testid="stDataFrame"] { background: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("### ⚙ Connect Sheet")
        url   = st.text_input("Google Sheet URL",  value=st.session_state.sheet_url,       placeholder="Paste your Google Sheet URL")
        pwd   = st.text_input("Admin Password",    value=st.session_state.admin_pwd,        type="password", placeholder="Set admin password")
        apps  = st.text_input("Apps Script URL",   value=st.session_state.apps_script_url,  placeholder="Paste Apps Script URL")
        if st.button("Save Settings", type="primary", use_container_width=True):
            st.session_state.sheet_url       = url
            st.session_state.admin_pwd       = pwd
            st.session_state.apps_script_url = apps
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.markdown("### 🔐 Admin")
        if not st.session_state.admin_mode:
            pwd_try = st.text_input("Password", type="password", key="pwd_try",
                                    placeholder="Enter admin password",
                                    label_visibility="collapsed")
            if st.button("Unlock Edit Mode", use_container_width=True):
                if pwd_try and pwd_try == st.session_state.admin_pwd:
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            st.success("✓ Edit mode active")
            if st.button("Lock", use_container_width=True):
                st.session_state.admin_mode = False
                st.rerun()

    # ── HEADER ──
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(
            "<h2 style='margin:0;color:#0f172a;'>Project Management Dashboard</h2>"
            "<p style='margin:0;color:#64748b;font-size:13px;'>letstranzact.com</p>",
            unsafe_allow_html=True
        )
    with h2:
        st.markdown(f"<p style='text-align:right;color:#64748b;font-size:12px;margin-top:8px;'>"
                    f"Last updated {datetime.now().strftime('%I:%M %p')}</p>",
                    unsafe_allow_html=True)
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    # ── FETCH DATA ──
    df = fetch_data(st.session_state.sheet_url)

    # Apply stored descriptions
    for name, detail in st.session_state.descriptions.items():
        mask = df['name'] == name
        if mask.any():
            if not df.loc[mask, 'description'].values[0]:
                df.loc[mask, 'description'] = detail.get('description', '')
            if not df.loc[mask, 'link'].values[0]:
                df.loc[mask, 'link'] = detail.get('link', '')

    # ── KPI ROW ──
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Projects",   len(df))
    k2.metric("In Dev",           len(df[df['status'] == 'In Dev']))
    k3.metric("In QA",            len(df[df['status'] == 'In QA']))
    k4.metric("In UAT",           len(df[df['status'] == 'In UAT']))
    k5.metric("Pending Release",  len(df[df['status'] == 'Pending for Release']))
    k6.metric("Released",         len(df[df['status'] == 'Released']))

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    # ── CHARTS ──
    c1, c2, c3 = st.columns(3)

    with c1:
        sc = df['status'].value_counts().reset_index()
        sc.columns = ['Status', 'Count']
        colors = [STATUS_COLORS.get(s, '#64748b') for s in sc['Status']]
        fig = px.pie(sc, values='Count', names='Status', title='Status Distribution',
                     color_discrete_sequence=colors)
        fig.update_traces(textposition='inside', textinfo='label+value')
        fig.update_layout(height=260, margin=dict(t=40,b=10,l=10,r=10),
                          showlegend=False, paper_bgcolor='white',
                          font=dict(family='system-ui', size=12))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        tc = df['type'].value_counts().reset_index()
        tc.columns = ['Type', 'Count']
        fig2 = px.bar(tc, x='Type', y='Count', title='By Project Type',
                      color_discrete_sequence=['#2563eb','#7c3aed','#0891b2'])
        fig2.update_layout(height=260, margin=dict(t=40,b=10,l=10,r=10),
                           paper_bgcolor='white', showlegend=False,
                           xaxis=dict(showgrid=False, title=''),
                           yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title=''),
                           font=dict(family='system-ui', size=12))
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        dev_df = df[df['developer'].str.strip() != '']
        dc = dev_df['developer'].value_counts().reset_index()
        dc.columns = ['Developer', 'Count']
        fig3 = px.bar(dc, x='Developer', y='Count', title='Developer Workload',
                      color_discrete_sequence=['#0f766e'])
        fig3.update_layout(height=260, margin=dict(t=40,b=10,l=10,r=10),
                           paper_bgcolor='white', showlegend=False,
                           xaxis=dict(showgrid=False, title=''),
                           yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title=''),
                           font=dict(family='system-ui', size=12))
        st.plotly_chart(fig3, use_container_width=True)

    # ── FILTERS ──
    f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
    types    = ['All'] + sorted(df['type'].dropna().unique().tolist())
    statuses = ['All'] + [s for s in STATUS_ORDER if s in df['status'].values]
    devs     = ['All'] + sorted(df[df['developer'].str.strip() != '']['developer'].unique().tolist())

    sel_type   = f1.selectbox("Project Type", types)
    sel_status = f2.selectbox("Status",       statuses)
    sel_dev    = f3.selectbox("Developer",    devs)
    f4.markdown(f"<p style='padding-top:32px;color:#64748b;font-size:12px;'>{len(df)} projects total</p>",
                unsafe_allow_html=True)

    # Apply filters
    filtered = df.copy()
    if sel_type   != 'All': filtered = filtered[filtered['type']      == sel_type]
    if sel_status != 'All': filtered = filtered[filtered['status']    == sel_status]
    if sel_dev    != 'All': filtered = filtered[filtered['developer'] == sel_dev]

    # ── TABLE ──
    col_map = {
        'name': 'Project', 'type': 'Type', 'status': 'Status', 'priority': 'Priority',
        'developer': 'Developer', 'devStart': 'Dev Start', 'devEnd': 'Dev End',
        'qa': 'QA', 'qaStart': 'QA Start', 'qaEnd': 'QA End',
        'uatStart': 'UAT Start', 'uatEnd': 'UAT End', 'releaseDate': 'Release Date',
    }
    table_df = filtered[list(col_map.keys())].rename(columns=col_map).reset_index(drop=True)

    st.markdown(
        f"<p style='font-weight:600;color:#374151;margin-bottom:4px;'>All Projects "
        f"<span style='font-weight:400;color:#64748b;font-size:12px;'>{len(filtered)} results</span></p>",
        unsafe_allow_html=True
    )

    event = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        height=min(420, 45 + len(filtered) * 35),
    )

    # Show detail dialog on row click
    if event.selection.rows:
        idx = event.selection.rows[0]
        if idx < len(filtered):
            project_dialog(filtered.iloc[idx].to_dict())


main()
