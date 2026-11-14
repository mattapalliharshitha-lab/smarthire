import React, { useState, useRef } from "react";
import {
  ArrowRight,
  Upload,
  FileText,
  Target,
  Brain,
  BriefcaseBusiness,
  CheckCircle2,
  TrendingUp,
  Menu,
  X,
  MapPin,
  Download,
  AlertCircle,
  LoaderCircle,
  GraduationCap
} from "lucide-react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

function App() {
  const [mobileMenu, setMobileMenu] = useState(false);

  // =====================================
  // STATE
  // =====================================
  const [view, setView] = useState("home");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null);

  // =====================================
  // SCROLL
  // =====================================
  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  };

  // =====================================
  // UPLOAD RESUME
  // =====================================
  const openUpload = () => {
    setError("");
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const extension = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(extension)) {
      setError("Please upload a PDF or DOCX resume.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("Resume size must be less than 10 MB.");
      return;
    }

    setFileName(file.name);
    setError("");
    setAnalysis(null);
    setLoading(true);
    setView("dashboard"); // Transition to dashboard view on upload

    const formData = new FormData();
    formData.append("resume", file);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Resume analysis failed.");
      }

      setAnalysis(data);

      setTimeout(() => {
        scrollTo("analysis-results");
      }, 200);

    } catch (err) {
      setError(err.message || "Could not analyze the resume.");
    } finally {
      setLoading(false);
    }
  };

  // =====================================
  // DOWNLOAD REPORT
  // =====================================
  const downloadReport = () => {
    if (!analysis) return;

    const blob = new Blob(
      [JSON.stringify(analysis, null, 2)],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "SmartHire_Resume_Report.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  // =====================================
  // RESULT VARIABLES
  // =====================================
  const jobs = analysis?.recommended_jobs || [];
  const topJob = jobs[0];
  const score = analysis?.resume_score;
  const sections = analysis?.detected_sections || [];
  const missingSections = analysis?.missing_sections || [];
  const skillsByCategory = analysis?.skills_by_category || {};

  // =====================================
  // MAIN APP
  // =====================================
  return (
    <div className="website">
      {/* =================================
          NAVBAR
      ================================= */}
      <header className="navbar">
        <button
          className="brand"
          onClick={() => {
            setView("home");
            scrollTo("home");
          }}
        >
          <span className="brand-mark">S</span>
          <span>
            SmartHire<span className="brand-dot">.</span>
          </span>
        </button>

        {view === "home" && (
          <nav className="nav-links">
            <button onClick={() => scrollTo("home")}>Home</button>
            <button onClick={() => scrollTo("features")}>Features</button>
            <button onClick={() => scrollTo("how-it-works")}>How It Works</button>
            <button onClick={() => scrollTo("about")}>About</button>
          </nav>
        )}

        <button
          className="mobile-menu-button"
          onClick={() => setMobileMenu(!mobileMenu)}
        >
          {mobileMenu ? <X /> : <Menu />}
        </button>
      </header>

      {/* =================================
          HOME PAGE
      ================================= */}
      {view === "home" && (
        <main>
          <section className="hero section-wrap" id="home">
            <div className="hero-content">
              <div className="eyebrow">
                <span className="status-dot" />
                RESUME INTELLIGENCE & CAREER MATCHING
              </div>

              <h1>
                Make your next career move
                <span> with clarity.</span>
              </h1>

              <p className="hero-description">
                Upload your resume to understand your skills,
                discover relevant opportunities and identify
                what you need to improve.
              </p>

              <div className="hero-actions">
                <button
                  className="button button-primary hero-upload"
                  onClick={openUpload}
                >
                  <Upload size={18} />
                  Analyze My Resume
                  <ArrowRight size={17} />
                </button>

                <button
                  className="button button-outline"
                  onClick={() => scrollTo("features")}
                >
                  Explore Features
                </button>
              </div>

              <div className="hero-stats">
                <div>
                  <strong>PDF / DOCX</strong>
                  <span>Resume formats</span>
                </div>
                <div>
                  <strong>ML</strong>
                  <span>Smart matching</span>
                </div>
                <div>
                  <strong>24/7</strong>
                  <span>Career insights</span>
                </div>
              </div>
            </div>

            <div className="hero-visual">
              <div className="preview-card">
                <div className="preview-header">
                  <div className="preview-icon">
                    <FileText size={25} />
                  </div>
                  <div>
                    <strong>Resume Intelligence</strong>
                    <small>SmartHire Career Engine</small>
                  </div>
                </div>

                <div className="preview-divider" />

                {[
                  "Skills Identification",
                  "Job Matching",
                  "Resume Completeness",
                  "Career Guidance"
                ].map((item) => (
                  <div className="preview-item" key={item}>
                    <span>{item}</span>
                    <CheckCircle2 size={17} />
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="features-section section-wrap" id="features">
            <div className="section-heading">
              <span className="section-kicker">CORE CAPABILITIES</span>
              <h2>Everything You Need to Get Hired</h2>
              <p>One resume upload gives you a complete career analysis.</p>
            </div>

            <div className="feature-grid">
              <article className="feature-card">
                <div className="feature-icon blue">
                  <Target size={25} />
                </div>
                <h3>Job Matching</h3>
                <p>
                  Discover relevant job profiles through
                  resume-text similarity and skill coverage.
                </p>
              </article>

              <article className="feature-card">
                <div className="feature-icon green">
                  <Brain size={25} />
                </div>
                <h3>Skill Gap Analysis</h3>
                <p>
                  Identify existing skills and missing
                  requirements for target job roles.
                </p>
              </article>

              <article className="feature-card">
                <div className="feature-icon purple">
                  <GraduationCap size={25} />
                </div>
                <h3>Career Guidance</h3>
                <p>
                  Understand suitable job domains and
                  receive improvement recommendations.
                </p>
              </article>
            </div>
          </section>

          <section className="how-section section-wrap" id="how-it-works">
            <div className="section-heading">
              <span className="section-kicker">HOW IT WORKS</span>
              <h2>Two Steps to Better Career Decisions</h2>
            </div>

            <div className="steps-grid">
              <div className="step-card">
                <span>01</span>
                <h3>Upload Resume</h3>
                <p>Let our machine learning engine analyze your resume.</p>
              </div>
              <div className="step-card">
                <span>02</span>
                <h3>Explore Results</h3>
                <p>Discover job matches and your skill gaps.</p>
              </div>
            </div>
          </section>

          <section id="about" className="about-section section-wrap">
            <div className="about-mark">S</div>
            <div>
              <span className="section-kicker">ABOUT SMARTHIRE</span>
              <h2>Career decisions backed by evidence.</h2>
              <p>
                A machine-learning-based resume-to-job
                matching and career guidance platform.
              </p>
            </div>
          </section>
        </main>
      )}

      {/* =================================
          DASHBOARD / ANALYSIS VIEW
      ================================= */}
      {view === "dashboard" && (
        <main className="dashboard section-wrap">
          
          <section className="dashboard-upload-panel">
            <div>
              <span className="section-kicker">RESUME ANALYSIS</span>
              <h2>Ready to discover your opportunities?</h2>
              <p>
                Upload your latest resume to receive
                a structured career analysis report.
              </p>
            </div>

            <button
              className="button button-primary dashboard-upload"
              onClick={openUpload}
              disabled={loading}
            >
              {loading ? <LoaderCircle className="spin" /> : <Upload size={18} />}
              {loading ? "Analyzing..." : "Upload Your Resume"}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept=".pdf,.docx"
              onChange={handleFileChange}
            />

            {error && (
              <div className="error-message">
                <AlertCircle size={17} />
                {error}
              </div>
            )}

            {loading && (
              <div className="loading-message">
                <LoaderCircle className="spin" />
                Processing {fileName}...
              </div>
            )}
          </section>

          {/* EMPTY DASHBOARD */}
          {!analysis && !loading && (
            <section className="empty-dashboard">
              <div className="empty-icon">
                <FileText size={36} />
              </div>
              <h2>Your analysis will appear here</h2>
              <p>
                Upload your resume to see completeness scores,
                recommended jobs, detected skills and improvement plans.
              </p>
            </section>
          )}

          {/* ANALYSIS RESULTS */}
          {analysis && (
            <section className="results-section" id="analysis-results">
              <div className="results-header">
                <div>
                  <span className="section-kicker">
                    YOUR PERSONALIZED REPORT
                  </span>
                  <h2>Resume Analysis</h2>
                  <p>
                    <FileText size={15} />
                    {analysis.resume_filename}
                  </p>
                </div>

                <button
                  className="button button-outline"
                  onClick={downloadReport}
                >
                  <Download size={16} />
                  Download Report
                </button>
              </div>

              {/* SUMMARY */}
              <div className="summary-grid">
                <div className="summary-card primary-summary">
                  <span>Resume Completeness</span>
                  <strong>{analysis.resume_score?.score ?? 0}%</strong>
                  <small>{analysis.resume_score?.label}</small>
                  <div className="score-track">
                    <div style={{ width: `${analysis.resume_score?.score ?? 0}%` }} />
                  </div>
                </div>

                <div className="summary-card">
                  <span>Top Matching Role</span>
                  <strong>{analysis.top_matching_role}</strong>
                  <small>Best matching profile</small>
                </div>

                <div className="summary-card">
                  <span>Skills Detected</span>
                  <strong>{analysis.detected_skills?.length ?? 0}</strong>
                  <small>Identified skills</small>
                </div>

                <div className="summary-card">
                  <span>Words Extracted</span>
                  <strong>{analysis.word_count ?? 0}</strong>
                  <small>Resume word count</small>
                </div>
              </div>

              {/* RESUME INFORMATION */}
              <div className="report-grid">
                <article className="report-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="section-kicker">DOCUMENT DETAILS</span>
                      <h3>Resume Overview</h3>
                    </div>
                    <FileText size={22} />
                  </div>
                  <div className="overview-list">
                    <div>
                      <span>Email</span>
                      <strong>{analysis.contact?.email || "Not detected"}</strong>
                    </div>
                    <div>
                      <span>Phone</span>
                      <strong>{analysis.contact?.phone || "Not detected"}</strong>
                    </div>
                    <div>
                      <span>Extracted characters</span>
                      <strong>{analysis.character_count}</strong>
                    </div>
                  </div>
                </article>

                <article className="report-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="section-kicker">RESUME STRUCTURE</span>
                      <h3>Sections Identified</h3>
                    </div>
                    <CheckCircle2 size={22} />
                  </div>
                  <div className="pill-wrap">
                    {analysis.detected_sections?.map((item) => (
                      <span className="skill-pill good" key={item}>
                        {item}
                      </span>
                    ))}
                  </div>

                  <h4 className="subheading">Missing Sections</h4>
                  <div className="pill-wrap">
                    {analysis.missing_sections?.map((item) => (
                      <span className="skill-pill missing" key={item}>
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
              </div>

              {/* SKILLS */}
              <article className="report-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-kicker">SKILL EXTRACTION</span>
                    <h3>Your Detected Skills</h3>
                  </div>
                  <Brain size={22} />
                </div>
                {Object.entries(analysis.skills_by_category || {}).map(
                  ([category, skills]) => (
                    <div className="skill-category" key={category}>
                      <h4>{category}</h4>
                      <div className="pill-wrap">
                        {skills.map((skill) => (
                          <span className="skill-pill good" key={skill}>
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </article>

              {/* JOB MATCHES */}
              <article className="report-panel" id="job-recommendations">
                <div className="panel-heading">
                  <div>
                    <span className="section-kicker">RANKED RESULTS</span>
                    <h3>Recommended Job Roles</h3>
                  </div>
                  <BriefcaseBusiness size={22} />
                </div>
                <p className="score-disclaimer">
                  Match scores are prototype similarity-based rankings,
                  not probabilities of getting hired.
                </p>

                <div className="job-list">
                  {jobs.map((job, index) => (
                    <div
                      className="job-card"
                      key={`${job.title}-${index}`}
                    >
                      <div className="job-card-header">
                        <div>
                          <span className="job-rank">RANK #{index + 1}</span>
                          <h3>{job.title}</h3>
                          <p>{job.category}</p>
                          <div className="job-meta">
                            <span>
                              <BriefcaseBusiness size={13} />
                              {job.experience}
                            </span>
                            <span>
                              <MapPin size={13} />
                              {job.location}
                            </span>
                          </div>
                        </div>

                        <div className="job-match">
                          <strong>
                            {Number(job.match_score).toFixed(1)}%
                          </strong>
                          <span>Match</span>
                        </div>
                      </div>

                      <div className="score-track">
                        <div
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(100, Number(job.match_score))
                            )}%`
                          }}
                        />
                      </div>

                      <div className="job-breakdown">
                        <span>Text similarity: {job.text_similarity}%</span>
                        <span>Skill coverage: {job.skill_coverage}%</span>
                      </div>

                      <div className="job-skills-grid">
                        <div>
                          <h4>Matching Skills</h4>
                          <div className="pill-wrap">
                            {job.matched_skills.map((skill) => (
                              <span
                                className="skill-pill good"
                                key={skill}
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h4>Missing Skills</h4>
                          <div className="pill-wrap">
                            {job.missing_skills.map((skill) => (
                              <span
                                className="skill-pill missing"
                                key={skill}
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              {/* IMPROVEMENT PLAN */}
              <article className="report-panel" id="career-guidance">
                <div className="panel-heading">
                  <div>
                    <span className="section-kicker">CAREER IMPROVEMENT</span>
                    <h3>Your Improvement Plan</h3>
                  </div>
                  <TrendingUp size={22} />
                </div>
                <ol className="improvement-list">
                  {analysis.improvement_plan?.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ol>
              </article>

              {/* ANALYZE ANOTHER */}
              <button
                className="button button-primary"
                onClick={openUpload}
              >
                <Upload size={17} />
                Analyze Another Resume
              </button>
            </section>
          )}
        </main>
      )}

      {/* FOOTER */}
      <footer className="footer section-wrap">
        <span>© 2026 SmartHire</span>
        <span>Resume-to-Job Matching and Career Guidance</span>
      </footer>
    </div>
  );
}

export default App;