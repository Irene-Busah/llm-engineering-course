import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight, BriefcaseBusiness, Check, ChevronDown, CircleHelp, Clock3,
  ExternalLink, FileText, Filter, Globe2, Laptop, MapPin, RefreshCw,
  Search, ShieldCheck, Sparkles, UserRound, X, Building2, SlidersHorizontal,
  LogOut, CheckCircle2, AlertCircle, CalendarDays, Banknote, Menu
} from "lucide-react";
import "./styles.css";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const PAGE_SIZE = 12;
const roleOptions = [
  "Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer",
  "Data Scientist", "Machine Learning Engineer", "AI Engineer", "Data Engineer",
  "Product Manager", "Business Analyst", "DevOps Engineer", "Cloud Engineer"
];
const locationOptions = [
  "United States", "United Kingdom", "Canada", "Germany", "Netherlands", "Rwanda",
  "Ghana", "Remote – Worldwide", "Europe", "Africa"
];
const workModes = ["Flexible", "Remote", "Hybrid", "Onsite"];

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join("; ")
      : detail || `Request failed (${response.status}).`;
    throw new Error(message);
  }
  return data;
}

function formatDate(value) {
  if (!value) return "Date not specified";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date not specified" : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function salaryLabel(job) {
  if (job.salary_min == null && job.salary_max == null) return null;
  const currency = job.salary_currency || "";
  const format = (amount) => new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(amount);
  if (job.salary_min != null && job.salary_max != null) return `${currency} ${format(job.salary_min)} – ${format(job.salary_max)}`.trim();
  return `${job.salary_min != null ? "From" : "Up to"} ${currency} ${format(job.salary_min ?? job.salary_max)}`.trim();
}

function MultiSelect({ label, placeholder, options, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const filtered = options.filter((item) => item.toLowerCase().includes(search.toLowerCase()));
  const toggle = (item) => onChange(value.includes(item) ? value.filter((v) => v !== item) : [...value, item]);
  return <div className="field">
    <label className="field-label">{label}</label>
    <div className={`multi-select ${open ? "focused" : ""}`}>
      <div className="selected-values" onClick={() => setOpen((current) => !current)} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setOpen((current) => !current)}>
        {value.length ? value.map((item) => <span className="tag" key={item}>{item}<button type="button" aria-label={`Remove ${item}`} onClick={(e) => { e.stopPropagation(); toggle(item); }}><X size={12}/></button></span>) : <span className="placeholder">{placeholder}</span>}
        <ChevronDown size={16} className="chevron"/>
      </div>
      {open && <div className="options-menu">
        <input autoFocus value={search} onChange={(e) => setSearch(e.target.value)} placeholder={`Search ${label.toLowerCase()}...`} />
        <div className="options-list">{filtered.map((item) => <button type="button" className="option" key={item} onClick={() => toggle(item)}><span className={`option-check ${value.includes(item) ? "checked" : ""}`}>{value.includes(item) && <Check size={12}/>}</span>{item}</button>)}{!filtered.length && <p className="empty-options">No matches found</p>}</div>
        <button type="button" className="done-button" onClick={() => { setOpen(false); setSearch(""); }}>Done</button>
      </div>}
    </div>
  </div>;
}

function Alert({ error, children, onClose }) {
  if (!children) return null;
  return <div className={`alert ${error ? "error-alert" : "success-alert"}`}><span className="alert-icon">{error ? <AlertCircle size={18}/> : <CheckCircle2 size={18}/>}</span><span>{children}</span>{onClose && <button type="button" onClick={onClose} aria-label="Dismiss"><X size={16}/></button>}</div>;
}

function JobCard({ job, label, onOpen }) {
  const salary = salaryLabel(job);
  return <article className="job-card">
    <div className="job-card-top"><div className="company-avatar">{(job.company || "?").trim().charAt(0).toUpperCase()}</div><div className="job-heading"><h3>{job.role_title}</h3><p>{job.company || "Company not specified"}</p></div>{label && <span className={`match-badge ${label === "Confirmed match" ? "confirmed" : "potential"}`}>{label}</span>}</div>
    <div className="job-meta"><span><MapPin size={14}/>{job.locations?.length ? job.locations.join(", ") : "Location not specified"}</span><span><Globe2 size={14}/>{job.remote_policy || "unknown"}</span>{job.employment_type && <span><BriefcaseBusiness size={14}/>{job.employment_type}</span>}</div>
    {job.description && <p className="job-description">{job.description}</p>}
    <div className="skill-list">{(job.required_skills || []).slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}</div>
    <div className="job-card-bottom"><div className="job-extra">{salary && <span><Banknote size={14}/>{salary}</span>}<span><CalendarDays size={14}/>Posted {formatDate(job.published_at)}</span></div><button className="text-button" type="button" onClick={() => onOpen(job)}>View details <ArrowRight size={15}/></button></div>
  </article>;
}

function JobDetails({ job, onClose }) {
  if (!job) return null;
  const salary = salaryLabel(job);
  return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
    <section className="details-modal" role="dialog" aria-modal="true" aria-labelledby="job-detail-title">
      <button className="modal-close" type="button" onClick={onClose} aria-label="Close"><X size={19}/></button>
      <div className="company-avatar large">{(job.company || "?").trim().charAt(0).toUpperCase()}</div>
      <p className="section-kicker">OPPORTUNITY DETAILS</p><h2 id="job-detail-title">{job.role_title}</h2><p className="detail-company">{job.company || "Company not specified"}</p>
      <div className="detail-meta"><span><MapPin size={15}/>{job.locations?.join(", ") || "Location not specified"}</span><span><Globe2 size={15}/>{job.remote_policy}</span>{job.employment_type && <span><BriefcaseBusiness size={15}/>{job.employment_type}</span>}{salary && <span><Banknote size={15}/>{salary}</span>}</div>
      {job.description && <><h3>About the role</h3><p className="detail-description">{job.description}</p></>}
      {job.required_skills?.length > 0 && <><h3>Skills and requirements</h3><div className="skill-list detail-skills">{job.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div></>}
      <div className="detail-facts"><span>Status <b>{job.status}</b></span><span>Visa sponsorship <b>{job.visa_sponsorship || "unknown"}</b></span><span>Deadline <b>{formatDate(job.deadline)}</b></span></div>
      <div className="modal-actions"><button className="secondary-button" type="button" onClick={onClose}>Close</button>{job.application_url ? <a className="primary-button" href={job.application_url} target="_blank" rel="noreferrer">Visit application <ExternalLink size={16}/></a> : <span className="muted-note">No application link provided</span>}</div>
    </section>
  </div>;
}

function App() {
  const [candidateId, setCandidateId] = useState(() => localStorage.getItem("opportunity_finder_candidate_id") || "");
  const [profile, setProfile] = useState(null);
  const [activeTab, setActiveTab] = useState("matches");
  const [file, setFile] = useState(null);
  const [roles, setRoles] = useState([]);
  const [locations, setLocations] = useState([]);
  const [mode, setMode] = useState("Flexible");
  const [sponsorship, setSponsorship] = useState("yes");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [matches, setMatches] = useState({ confirmed_matches: [], potential_matches: [], total: 0, query: "" });
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [opportunities, setOpportunities] = useState([]);
  const [opportunityTotal, setOpportunityTotal] = useState(0);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [filters, setFilters] = useState({ role: "", company: "", location: "", status: "", remote_policy: "" });
  const [page, setPage] = useState(0);
  const [selectedJob, setSelectedJob] = useState(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [editRoles, setEditRoles] = useState([]);
  const [editLocations, setEditLocations] = useState([]);
  const [editMode, setEditMode] = useState("Flexible");
  const [editSponsorship, setEditSponsorship] = useState(false);
  const [resumeInput, setResumeInput] = useState(null);

  const loadProfile = useCallback(async (id = candidateId) => {
    if (!id) return;
    setProfileLoading(true); setError("");
    try {
      const data = await apiRequest(`/api/candidates/${encodeURIComponent(id)}`);
      setProfile(data);
      setEditRoles(data.preferred_roles || []);
      setEditLocations(data.preferred_locations || []);
      setEditMode(data.remote_preference || "Flexible");
      setEditSponsorship(Boolean(data.visa_sponsorship_required));
    } catch (err) { setError(err.message); }
    finally { setProfileLoading(false); }
  }, [candidateId]);

  const loadMatches = useCallback(async (searchQuery = "") => {
    if (!candidateId) return;
    setMatchesLoading(true); setError("");
    try {
      const params = new URLSearchParams({ limit: "10" });
      if (searchQuery.trim()) params.set("query", searchQuery.trim());
      const data = await apiRequest(`/api/candidates/${encodeURIComponent(candidateId)}/matches?${params}`);
      setMatches(data);
    } catch (err) { setError(err.message); }
    finally { setMatchesLoading(false); }
  }, [candidateId]);

  const loadOpportunities = useCallback(async (nextPage = page, nextFilters = filters) => {
    setBrowseLoading(true); setError("");
    try {
      const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(nextPage * PAGE_SIZE) });
      Object.entries(nextFilters).forEach(([key, value]) => { if (value) params.set(key, value); });
      const data = await apiRequest(`/api/opportunities?${params}`);
      setOpportunities(data.items || []); setOpportunityTotal(data.total || 0);
    } catch (err) { setError(err.message); }
    finally { setBrowseLoading(false); }
  }, [filters, page]);

  useEffect(() => {
    if (candidateId) { loadProfile(candidateId); loadMatches(); }
  }, [candidateId, loadProfile, loadMatches]);

  useEffect(() => { if (candidateId && activeTab === "explore") loadOpportunities(page, filters); }, [candidateId, activeTab, page, filters, loadOpportunities]);

  const chooseFile = (candidate) => {
    if (!candidate) return;
    const ext = candidate.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(ext)) { setError("Please choose a PDF or DOCX file."); return; }
    if (candidate.size > 10 * 1024 * 1024) { setError("Your resume must be 10 MB or smaller."); return; }
    setFile(candidate); setError("");
  };

  const submitOnboarding = async (event) => {
    event.preventDefault(); setError(""); setNotice("");
    if (!file) { setError("Upload your resume to continue."); return; }
    const form = new FormData(); form.append("resume", file);
    roles.forEach((role) => form.append("preferred_roles", role));
    locations.forEach((location) => form.append("preferred_locations", location));
    form.append("remote_preference", mode);
    form.append("visa_sponsorship_required", sponsorship === "yes" ? "true" : "false");
    setLoading(true);
    try {
      const data = await apiRequest("/api/candidates/onboard", { method: "POST", body: form });
      localStorage.setItem("opportunity_finder_candidate_id", data.candidate_id);
      setCandidateId(data.candidate_id); setProfile(null); setActiveTab("matches");
      setNotice("Your profile is ready. We're finding opportunities that fit your background.");
      setFile(null);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const runSearch = async (event) => {
    event.preventDefault();
    if (!searchInput.trim()) { setError("Enter what kind of opportunity you're looking for."); return; }
    setQuery(searchInput.trim()); setActiveTab("matches"); setMatchesLoading(true); setError("");
    try {
      const data = await apiRequest("/api/opportunities/search", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: candidateId, query: searchInput.trim(), limit: 10 })
      });
      setMatches(data);
    } catch (err) { setError(err.message); }
    finally { setMatchesLoading(false); }
  };

  const savePreferences = async (event) => {
    event.preventDefault(); setProfileLoading(true); setError(""); setNotice("");
    try {
      const updated = await apiRequest(`/api/candidates/${encodeURIComponent(candidateId)}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferred_roles: editRoles, preferred_locations: editLocations, remote_preference: editMode, visa_sponsorship_required: editSponsorship })
      });
      setProfile(updated); setNotice("Your preferences have been updated.");
      setActiveTab("matches"); setQuery(""); await loadMatches("");
    } catch (err) { setError(err.message); }
    finally { setProfileLoading(false); }
  };

  const signOut = () => {
    localStorage.removeItem("opportunity_finder_candidate_id"); setCandidateId(""); setProfile(null);
    setMatches({ confirmed_matches: [], potential_matches: [], total: 0, query: "" }); setActiveTab("matches");
  };

  const allMatches = useMemo(() => [
    ...(matches.confirmed_matches || []).map((job) => ({ job, label: "Confirmed match" })),
    ...(matches.potential_matches || []).map((job) => ({ job, label: "Potential match" }))
  ], [matches]);

  if (!candidateId) return <div className="app-shell">
    <header className="hero"><nav className="nav wrap"><a className="brand" href="#"><span className="brand-mark"><Sparkles size={21}/></span><span>opportunity<span className="brand-light">finder</span></span></a><span className="nav-status"><i/> CAREER DISCOVERY, REIMAGINED</span></nav>
      <div className="hero-content wrap"><div className="hero-copy"><div className="eyebrow"><span/> CAREER DISCOVERY, REIMAGINED</div><h1>Make your next move<br/><em>your best one.</em></h1><p>Tell us where you want to go. We'll help you discover opportunities that align with your skills, ambitions, and the way you want to work.</p><div className="hero-proof"><span><CheckCircle2 size={16}/> Opportunities matched to you</span><span><ShieldCheck size={16}/> Your profile stays private</span></div></div>
        <div className="hero-art" aria-hidden="true"><div className="orbit-ring ring-a"/><div className="orbit-ring ring-b"/><div className="floating-card card-back"><span className="mini-logo blue"><Sparkles size={15}/></span><div><b>New opportunities</b><small>Curated around your goals</small></div></div><div className="floating-card card-main"><div className="match-topline"><span className="mini-logo"><BriefcaseBusiness size={16}/></span><span className="match-label">YOUR CAREER MATCH</span><span className="match-dot"/></div><div className="match-role">The right role is<br/>closer than you think.</div><div className="match-progress"><span/></div><div className="match-foot"><span>Skills aligned</span><b>92%</b></div></div><div className="floating-card card-bottom"><span className="sparkle-dot"><Sparkles size={15}/></span><div><b>A better way forward</b><small>Built around you</small></div><ArrowRight size={17}/></div><div className="hero-spark spark-one">✦</div><div className="hero-spark spark-two">✧</div></div>
      </div></header>
    <main className="main wrap"><div className="section-heading"><div><div className="section-kicker">LET'S GET TO KNOW YOU</div><h2>Start with the essentials</h2><p>A few details help us find opportunities worth your attention.</p></div><div className="step-indicator"><span>01</span><i/><span className="muted-step">02</span><small>YOUR PROFILE</small></div></div>
      <form onSubmit={submitOnboarding}><div className="form-grid">
        <section className="panel resume-panel"><div className="panel-heading"><div className="panel-icon"><FileText size={19}/></div><div><h3>Your resume</h3><p>Give us a starting point</p></div><span className="required-label">REQUIRED</span></div>
          <div className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(e) => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files[0]); }}>
            {file ? <><div className="upload-icon success-icon"><Check size={25}/></div><div className="file-info"><b>{file.name}</b><span>{(file.size / 1024 / 1024).toFixed(2)} MB · Ready to upload</span></div><button type="button" className="remove-file" onClick={() => setFile(null)}><X size={17}/></button></> : <><div className="upload-icon"><FileText size={27}/></div><h4>Drop your resume here</h4><p>or <button type="button" className="browse-link" onClick={() => resumeInput?.click()}>browse files</button> from your device</p><div className="file-types"><span>PDF</span><span>DOCX</span><i>·</i> Up to 10 MB</div></>}
            <input ref={setResumeInput} type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden onChange={(e) => chooseFile(e.target.files[0])}/>
          </div><div className="privacy-note"><ShieldCheck size={16}/><span><b>Your information is safe.</b> Your resume is used only to build your private candidate profile.</span></div><div className="resume-benefits"><div><span className="benefit-icon"><Sparkles size={15}/></span><span><b>Smart profile creation</b><small>We extract your skills and experience automatically.</small></span></div><div><span className="benefit-icon"><ZapIcon/></span><span><b>Less effort, better matches</b><small>No need to manually enter your career history.</small></span></div></div>
        </section>
        <section className="panel preferences-panel"><div className="panel-heading"><div className="panel-icon"><BriefcaseBusiness size={19}/></div><div><h3>Career preferences</h3><p>What does your next role look like?</p></div><span className="optional-label">PERSONALIZE</span></div>
          <MultiSelect label="Roles you're interested in" placeholder="Select your preferred roles" options={roleOptions} value={roles} onChange={setRoles}/><MultiSelect label="Preferred work locations" placeholder="Where would you like to work?" options={locationOptions} value={locations} onChange={setLocations}/>
          <div className="field"><label className="field-label">How would you like to work?</label><div className="work-options">{workModes.map((value) => <button type="button" key={value} onClick={() => setMode(value)} className={`work-option ${mode === value ? "selected" : ""}`}><span className="work-option-icon">{value === "Remote" ? <Globe2 size={18}/> : value === "Hybrid" ? <Laptop size={18}/> : value === "Onsite" ? <Building2 size={18}/> : <Sparkles size={18}/>}</span><b>{value === "Onsite" ? "On-site" : value}</b><small>{value === "Remote" ? "Work from anywhere" : value === "Hybrid" ? "A mix of both" : value === "Onsite" ? "At the office" : "Open to options"}</small>{mode === value && <span className="selected-check"><Check size={11}/></span>}</button>)}</div></div>
          <div className="field sponsorship-field"><div className="sponsor-title"><label className="field-label">Will you require visa sponsorship?</label><span className="help-tip" title="This helps us identify roles with compatible work authorization policies."><CircleHelp size={15}/></span></div><div className="sponsor-options"><button type="button" className={sponsorship === "yes" ? "selected" : ""} onClick={() => setSponsorship("yes")}><span className="radio-dot"/>Yes, I do</button><button type="button" className={sponsorship === "no" ? "selected" : ""} onClick={() => setSponsorship("no")}><span className="radio-dot"/>No, I don't</button></div></div>
        </section></div><Alert error>{error}</Alert><div className="submit-row"><div className="submit-note"><ShieldCheck size={16}/><span>Your details are only used to personalize your opportunity search.</span></div><button className="submit-button" type="submit" disabled={loading}>{loading ? <><span className="spinner"/> Creating your profile...</> : <>Create my profile <ArrowRight size={18}/></>}</button></div></form><div className="bottom-note">✦ A little about you goes a long way. Let's find what's next.</div>
    </main><footer className="footer"><div className="wrap"><span>© 2026 Opportunity Finder</span><span>Built for your next opportunity <Sparkles size={13}/></span></div></footer>
  </div>;

  return <div className="dashboard-shell">
    <aside className={`sidebar ${mobileNavOpen ? "open" : ""}`}><a className="brand sidebar-brand" href="#"><span className="brand-mark"><Sparkles size={20}/></span><span>opportunity<span className="brand-light">finder</span></span></a>
      <div className="sidebar-label">WORKSPACE</div><nav className="side-nav">
        <button className={activeTab === "matches" ? "active" : ""} onClick={() => { setActiveTab("matches"); setMobileNavOpen(false); }}><Sparkles size={18}/>For you</button>
        <button className={activeTab === "explore" ? "active" : ""} onClick={() => { setActiveTab("explore"); setMobileNavOpen(false); }}><Search size={18}/>Explore opportunities</button>
        <button className={activeTab === "profile" ? "active" : ""} onClick={() => { setActiveTab("profile"); setMobileNavOpen(false); }}><UserRound size={18}/>My profile</button>
      </nav><div className="sidebar-bottom"><div className="sidebar-tip"><span><Sparkles size={16}/></span><b>Your next chapter starts here.</b><p>Keep your preferences up to date to get more relevant matches.</p></div><button className="signout-button" onClick={signOut}><LogOut size={17}/> Sign out</button></div>
    </aside>
    <main className="dashboard-main"><header className="dashboard-header"><button className="mobile-menu" onClick={() => setMobileNavOpen(!mobileNavOpen)}><Menu size={20}/></button><div><span className="header-eyebrow">OPPORTUNITY FINDER</span><h1>{activeTab === "matches" ? "Your opportunities" : activeTab === "explore" ? "Explore opportunities" : "Your profile"}</h1></div><div className="header-user"><div className="user-avatar">{(profile?.email || "Y").charAt(0).toUpperCase()}</div><div><b>{profile?.email || "Your profile"}</b><small>Candidate workspace</small></div></div></header>
      <div className="dashboard-content"><Alert error>{error}</Alert><Alert>{notice}</Alert>
        {activeTab === "matches" && <>
          <section className="welcome-banner"><div><span className="section-kicker">A LITTLE CLOSER TO WHAT'S NEXT</span><h2>Opportunities that move you forward.</h2><p>Based on your skills, experience and career preferences.</p></div><div className="welcome-art"><Sparkles size={46}/></div></section>
          <form className="search-bar" onSubmit={runSearch}><Search size={19}/><input value={searchInput} onChange={(e) => setSearchInput(e.target.value)} placeholder="Try ‘Remote data science roles in Europe’"/><button type="submit" disabled={matchesLoading}>Search opportunities <ArrowRight size={16}/></button></form>
          <div className="content-heading"><div><div className="section-kicker">PERSONALIZED DISCOVERY</div><h2>{query ? "Search results" : "Recommended for you"}</h2><p>{query ? `Results for “${query}”` : "Roles selected around your candidate profile."}</p></div><button className="subtle-button" onClick={() => { setQuery(""); setSearchInput(""); loadMatches(""); }} disabled={matchesLoading}><RefreshCw size={15}/> Refresh</button></div>
          {matchesLoading ? <div className="loading-state"><span className="spinner dark"/> Finding opportunities that fit your profile...</div> : allMatches.length ? <><div className="results-summary"><span>{matches.total} relevant {matches.total === 1 ? "opportunity" : "opportunities"}</span><span><i className="legend-confirmed"/> Confirmed <i className="legend-potential"/> Potential</span></div><div className="job-grid">{allMatches.map(({ job, label }) => <JobCard key={job.id} job={job} label={label} onOpen={setSelectedJob}/>)}</div></> : <div className="empty-state"><div className="empty-icon"><BriefcaseBusiness size={25}/></div><h3>No matches found just yet</h3><p>Try a broader search, update your preferences, or explore all available opportunities.</p><button className="primary-button" onClick={() => setActiveTab("explore")}>Explore opportunities <ArrowRight size={16}/></button></div>}
        </>}
        {activeTab === "explore" && <>
          <div className="explore-intro"><p>Browse opportunities collected by Opportunity Finder. Narrow the list to find roles that interest you.</p></div>
          <section className="filter-panel"><div className="filter-title"><Filter size={17}/><b>Filter opportunities</b><button type="button" className="clear-filters" onClick={() => { setFilters({ role: "", company: "", location: "", status: "", remote_policy: "" }); setPage(0); }}>Clear all</button></div><div className="filter-grid"><label><span>Role or title</span><input value={filters.role} onChange={(e) => { setFilters((f) => ({ ...f, role: e.target.value })); setPage(0); }} placeholder="e.g. Data Scientist"/></label><label><span>Company</span><input value={filters.company} onChange={(e) => { setFilters((f) => ({ ...f, company: e.target.value })); setPage(0); }} placeholder="Company name"/></label><label><span>Location</span><input value={filters.location} onChange={(e) => { setFilters((f) => ({ ...f, location: e.target.value })); setPage(0); }} placeholder="e.g. Remote, London"/></label><label><span>Work arrangement</span><select value={filters.remote_policy} onChange={(e) => { setFilters((f) => ({ ...f, remote_policy: e.target.value })); setPage(0); }}><option value="">Any arrangement</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">On-site</option><option value="unknown">Not specified</option></select></label><label><span>Status</span><select value={filters.status} onChange={(e) => { setFilters((f) => ({ ...f, status: e.target.value })); setPage(0); }}><option value="">Any status</option><option value="open">Open</option><option value="unknown">Unknown</option><option value="closed">Closed</option><option value="expired">Expired</option></select></label></div></section>
          <div className="content-heading compact-heading"><div><h2>All opportunities <span className="count-pill">{opportunityTotal}</span></h2></div><button className="subtle-button" onClick={() => loadOpportunities(page, filters)}><RefreshCw size={15}/> Refresh</button></div>
          {browseLoading ? <div className="loading-state"><span className="spinner dark"/> Loading opportunities...</div> : opportunities.length ? <><div className="job-grid">{opportunities.map((job) => <JobCard key={job.id} job={job} onOpen={setSelectedJob}/>)}</div><div className="pagination"><span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, opportunityTotal)} of {opportunityTotal}</span><div><button disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Previous</button><button disabled={(page + 1) * PAGE_SIZE >= opportunityTotal} onClick={() => setPage((p) => p + 1)}>Next <ArrowRight size={14}/></button></div></div></> : <div className="empty-state"><div className="empty-icon"><Search size={25}/></div><h3>No opportunities to show</h3><p>Try changing or clearing your filters. New opportunities appear as the collection pipeline processes posts.</p></div>}
        </>}
        {activeTab === "profile" && <>
          {profileLoading && !profile ? <div className="loading-state"><span className="spinner dark"/> Loading your profile...</div> : profile && <div className="profile-layout"><section className="profile-card"><div className="profile-card-head"><div className="profile-avatar"><UserRound size={25}/></div><div><h2>{profile.email || "Candidate profile"}</h2><p>Candidate ID · {profile.candidate_id}</p></div></div><div className="profile-summary"><span className="section-kicker">PROFESSIONAL SUMMARY</span><p>{profile.professional_summary || "No professional summary was extracted from your resume."}</p></div><div className="profile-stats"><div><b>{profile.skills?.length || 0}</b><span>Skills identified</span></div><div><b>{profile.years_of_experience ?? "—"}</b><span>Years experience</span></div><div><b>{profile.experience?.length || 0}</b><span>Experiences</span></div></div><div className="profile-section"><h3>Skills</h3><div className="skill-list">{profile.skills?.length ? profile.skills.map((skill) => <span key={skill}>{skill}</span>) : <small>No skills listed</small>}</div></div><div className="profile-section"><h3>Experience</h3>{profile.experience?.length ? profile.experience.map((item, index) => <div className="timeline-item" key={`${item.company}-${index}`}><b>{item.role}</b><span>{item.company}</span><p>{item.description}</p><small>{item.start_date || ""}{item.end_date ? ` – ${item.end_date}` : ""}</small></div>) : <p className="muted-note">No experience entries were extracted.</p>}</div><div className="profile-section"><h3>Education</h3>{profile.education?.length ? profile.education.map((item, index) => <div className="timeline-item" key={`${item.institution}-${index}`}><b>{item.qualification}</b><span>{item.institution}</span><p>{item.field_of_study || ""}</p><small>{item.graduation_year || ""}</small></div>) : <p className="muted-note">No education entries were extracted.</p>}</div></section>
            <form className="panel edit-preferences" onSubmit={savePreferences}><div className="panel-heading"><div className="panel-icon"><SlidersHorizontal size={19}/></div><div><h3>Career preferences</h3><p>Keep your opportunity matches relevant.</p></div></div><MultiSelect label="Preferred roles" placeholder="Select roles" options={roleOptions} value={editRoles} onChange={setEditRoles}/><MultiSelect label="Preferred locations" placeholder="Select locations" options={locationOptions} value={editLocations} onChange={setEditLocations}/><div className="field"><label className="field-label">Work arrangement</label><select className="full-select" value={editMode} onChange={(e) => setEditMode(e.target.value)}>{workModes.map((item) => <option key={item} value={item}>{item}</option>)}</select></div><div className="field"><label className="field-label">Visa sponsorship required?</label><div className="sponsor-options"><button type="button" className={editSponsorship ? "selected" : ""} onClick={() => setEditSponsorship(true)}><span className="radio-dot"/>Yes</button><button type="button" className={!editSponsorship ? "selected" : ""} onClick={() => setEditSponsorship(false)}><span className="radio-dot"/>No</button></div></div><button className="submit-button full-button" type="submit" disabled={profileLoading}>{profileLoading ? "Saving..." : "Save preferences"} <Check size={17}/></button></form></div>}
        </>}
      </div><footer className="dashboard-footer"><span>© 2026 Opportunity Finder</span><span>Built for your next opportunity <Sparkles size={13}/></span></footer>
    </main><JobDetails job={selectedJob} onClose={() => setSelectedJob(null)}/>
  </div>;
}

function ZapIcon() { return <Sparkles size={15}/>; }

export default App;
