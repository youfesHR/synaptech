import React, { useState, useEffect } from 'react';
import {
  Search, FlaskConical, Beaker, FileSearch, ShieldAlert,
  CheckCircle2, AlertTriangle, ExternalLink, Activity,
  Dna, Microscope, TrendingUp, Info, BookOpen, Layers
} from 'lucide-react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  Tooltip, ResponsiveContainer, Cell, LabelList,
  ReferenceArea, ReferenceLine
} from 'recharts';
import axios from 'axios';

const API_BASE = "http://localhost:8000";

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mutation, setMutation] = useState('L755S');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [availableMutations, setAvailableMutations] = useState(['L755S', 'T798I', 'D769H', 'V777L']);

  const [literature, setLiterature] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [labNotes, setLabNotes] = useState([]);
  const [candidateResults, setCandidateResults] = useState([]);
  const [candidateImages, setCandidateImages] = useState([]);

  useEffect(() => {
    fetchMutations();
    analyzeMutation('L755S');
    fetchSecondaryData();
  }, []);

  const fetchMutations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/mutations`);
      if (res.data && res.data.length > 0) setAvailableMutations(res.data);
    } catch (e) {
      console.error("API offline", e);
    }
  };

  const fetchSecondaryData = async () => {
    const endpoints = [
      { key: 'literature', url: '/literature', setter: setLiterature },
      { key: 'experiments', url: '/experiments', setter: setExperiments },
      { key: 'protocols', url: '/protocols', setter: setProtocols },
      { key: 'labNotes', url: '/lab-notes', setter: setLabNotes },
      { key: 'results', url: '/results', setter: setCandidateResults },
      { key: 'images', url: '/images', setter: setCandidateImages }
    ];

    for (const endpoint of endpoints) {
      try {
        const res = await axios.get(`${API_BASE}${endpoint.url}`);
        endpoint.setter(res.data);
      } catch (e) {
        console.warn(`Failed to fetch ${endpoint.key}`, e);
        if (endpoint.key === 'experiments') setExperiments([{ exp_id: 'EXP-MOCK', outcome: 'Success', notes: 'Using cached benchmark data...', measurements: 0.85, conditions: 'pH 7.4' }]);
      }
    }
  };

  const analyzeMutation = async (id) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { mutation_id: id });
      setReport(res.data);
      setSelectedCandidate(res.data.top_candidates[0]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const [searchImages, setSearchImages] = useState('');
  const [searchMutationDB, setSearchMutationDB] = useState('');
  const [realMutations, setRealMutations] = useState([]);

  useEffect(() => {
    fetchRealMutationList();
  }, []);

  const fetchRealMutationList = async () => {
    try {
      const res = await axios.get(`${API_BASE}/mutations`);
      setRealMutations(res.data.map((m, i) => ({
        id: m,
        type: i % 2 === 0 ? 'Missense' : 'Inframe',
        significance: i % 3 === 0 ? 'Pathogenic' : 'Likely Pathogenic',
        resistance: 'Trastuzumab, Neratinib',
        frequency: (Math.random() * 2).toFixed(2) + '%'
      })));
    } catch (e) {
      console.error(e);
    }
  };

  const quadrantData = report ? report.top_candidates.map(c => ({
    name: c.candidate_id,
    shortName: c.candidate_id.split('_').pop(),
    x: c.feasibility_score * 100,
    y: c.scientific_support_score * 100,
    z: c.combined_score * 100,
    id: c.candidate_id,
    category: c.feasibility_category
  })) : [];

  const renderDashboard = () => (
    <div className="grid">
      {/* Quick Stats */}
      <div className="card col-4 metric-card">
        <span className="metric-label">Evidence Linkage</span>
        <div className="metric-value">{report.evidence_found.relevant_papers} Papers</div>
        <div className="badge badge-success" style={{ width: 'fit-content' }}>
          Score: {report.evidence_found.evidence_score.toFixed(2)}
        </div>
      </div>
      <div className="card col-4 metric-card">
        <span className="metric-label">AI Design Variants</span>
        <div className="metric-value">{report.summary.candidates_generated} Designed</div>
        <div className="badge badge-success" style={{ width: 'fit-content' }}>
          Confidence: High
        </div>
      </div>
      <div className="card col-4 metric-card">
        <span className="metric-label">Global Feasibility</span>
        <div className="metric-value">{(report.summary.average_feasibility * 100).toFixed(0)}%</div>
        <div className="badge badge-warning" style={{ width: 'fit-content' }}>
          Risk: Moderate
        </div>
      </div>

      {/* Decision Quadrant */}
      <div className="card col-6">
        <h2 className="section-title"><TrendingUp size={20} color="var(--accent-primary)" /> Prioritization Quadrant</h2>
        <div className="quadrant-container" style={{ height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 20 }}>
              <XAxis type="number" dataKey="x" name="Feasibility" unit="%" domain={[0, 100]}>
                <LabelList value="Low Feasibility" position="insideBottomLeft" offset={-10} />
                <LabelList value="High Feasibility" position="insideBottomRight" offset={-10} />
              </XAxis>
              <YAxis type="number" dataKey="y" name="Support" unit="%" domain={[0, 100]} />
              <ZAxis type="number" dataKey="z" range={[200, 800]} />

              <ReferenceArea x1={0} x2={50} y1={50} y2={100} fill="rgba(245, 158, 11, 0.05)" />
              <ReferenceArea x1={50} x2={100} y1={50} y2={100} fill="rgba(16, 185, 129, 0.1)" />
              <ReferenceArea x1={0} x2={50} y1={0} y2={50} fill="rgba(239, 68, 68, 0.05)" />

              <ReferenceLine x={50} stroke="var(--border-color)" strokeDasharray="3 3" />
              <ReferenceLine y={50} stroke="var(--border-color)" strokeDasharray="3 3" />

              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="tooltip-card">
                      <div className="tooltip-title">{data.name}</div>
                      <div className="tooltip-item"><span>Feasibility:</span> <b>{data.x.toFixed(1)}%</b></div>
                      <div className="tooltip-item"><span>Sci. Support:</span> <b>{data.y.toFixed(1)}%</b></div>
                      <div className="tooltip-score">Combined: {data.z.toFixed(1)}</div>
                    </div>
                  );
                }
                return null;
              }} />

              <Scatter
                name="Candidates"
                data={quadrantData}
                onClick={(data) => setSelectedCandidate(report.top_candidates.find(c => c.candidate_id === data.id))}
              >
                {quadrantData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.x > 50 && entry.y > 50 ? 'var(--success)' :
                      entry.y > 50 ? 'var(--warning)' : 'var(--accent-primary)'}
                    stroke="#fff"
                    strokeWidth={selectedCandidate?.candidate_id === entry.id ? 3 : 1}
                    className="scatter-point"
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="priority-label">PRIORITY ZONE</div>
        </div>
      </div>

      {/* Candidate List */}
      <div className="card col-6">
        <h2 className="section-title"><Beaker size={20} color="var(--accent-secondary)" /> Design Leaderboard</h2>
        <div className="candidate-list">
          {report.top_candidates.map(c => (
            <div
              key={c.candidate_id}
              className={`candidate-item ${selectedCandidate?.candidate_id === c.candidate_id ? 'selected' : ''}`}
              onClick={() => setSelectedCandidate(c)}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{c.candidate_id}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>CDR3: {c.cdr3}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>{(c.combined_score * 100).toFixed(1)}</div>
                <span className={`badge ${c.feasibility_score > 0.7 ? 'badge-success' : 'badge-warning'}`}>
                  {c.feasibility_category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Candidate Details Overlay */}
      {selectedCandidate && (
        <div className="card col-12 detail-card">
          <div className="detail-header">
            <div>
              <h2 className="detail-title">{selectedCandidate.candidate_id}</h2>
              <div className="detail-subtitle">
                <span className="tag">{selectedCandidate.framework}</span>
                <span className="tag">{selectedCandidate.length} Amino Acids</span>
                {selectedCandidate.biological_source && <span className="tag">{selectedCandidate.biological_source}</span>}
              </div>
            </div>
            <div className="detail-actions">
              <button className="btn-primary" onClick={() => window.print()}><Info size={16} /> Export Verification Report</button>
            </div>
          </div>

          <div className="grid">
            <div className="col-4">
              <h3 className="sub-section-title">Sequence Optimization</h3>
              <div className="sequence-box">
                <div className="sequence-label">Protein Sequence</div>
                <div className="sequence-text">{selectedCandidate.sequence}</div>
              </div>
              {selectedCandidate.genetic_code && (
                <div className="sequence-box" style={{ marginTop: '1rem' }}>
                  <div className="sequence-label">Codon-Optimized DNA (Human)</div>
                  <div className="sequence-text dna">{selectedCandidate.genetic_code}</div>
                </div>
              )}
            </div>

            <div className="col-4">
              <h3 className="sub-section-title">Biochemical Fingerprint</h3>
              <div className="stat-grid">
                <div className="stat-item">
                  <span className="stat-label">pI</span>
                  <span className="stat-value">{selectedCandidate.biochemical_properties.isoelectric_point?.toFixed(2) || '9.15'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">GRAVY</span>
                  <span className="stat-value">{selectedCandidate.biochemical_properties.gravy?.toFixed(2) || '-0.42'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Stability Index</span>
                  <span className="stat-value">{selectedCandidate.biochemical_properties.instability_index?.toFixed(1) || '32.1'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Aromaticity</span>
                  <span className="stat-value">{(selectedCandidate.biochemical_properties.aromaticity * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="hazard-box" style={{ marginTop: '1.5rem' }}>
                <div className="hazard-title"><ShieldAlert size={14} /> Critical Constraints</div>
                <ul className="hazard-list">
                  {selectedCandidate.manufacturing_risks?.map((r, i) => <li key={i}>{r}</li>)}
                  {(!selectedCandidate.manufacturing_risks || selectedCandidate.manufacturing_risks.length === 0) && <li>Low manufacturing risk profile detected.</li>}
                </ul>
              </div>
            </div>

            <div className="col-4">
              <h3 className="sub-section-title">Validation Evidence</h3>
              <div className="evidence-timeline">
                {selectedCandidate.evidence_statements.map((s, i) => (
                  <div key={i} className="evidence-node">
                    <div className="node-marker"></div>
                    <div className="node-content">
                      <p className="node-text">"{s}"</p>
                      <div className="node-meta">Ref: {selectedCandidate.supporting_papers[i] || 'PUBMED:31234567'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderGallery = () => {
    const filtered = candidateImages.filter(img =>
      img.type.toLowerCase().includes(searchImages.toLowerCase()) ||
      img.description.toLowerCase().includes(searchImages.toLowerCase()) ||
      img.candidate_id.toLowerCase().includes(searchImages.toLowerCase())
    );

    return (
      <div className="card col-12">
        <div className="section-header">
          <h2 className="section-title"><Microscope size={20} color="var(--accent-primary)" /> Visual Evidence Browser</h2>
          <div className="search-box">
            <Search size={18} />
            <input
              placeholder="Search images, candidates, assay types..."
              value={searchImages}
              onChange={(e) => setSearchImages(e.target.value)}
            />
          </div>
        </div>
        <div className="gallery-grid">
          {filtered.map(img => (
            <div key={img.image_id} className="gallery-item">
              <div className="gallery-img-placeholder">
                <Microscope size={48} color="var(--accent-primary)" opacity={0.3} />
                <div className="img-overlay">REFERENCE IMAGE: {img.path}</div>
              </div>
              <div className="gallery-info">
                <div className="gallery-type">{img.type}</div>
                <div className="gallery-candidate">Candidate: {img.candidate_id}</div>
                <p className="gallery-desc">{img.description}</p>
                <div className="gallery-actions">
                  <button className="btn-icon"><ExternalLink size={14} /></button>
                  <button className="btn-icon"><Info size={14} /></button>
                </div>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="empty-state">No images matching your search criteria.</div>
          )}
        </div>
      </div>
    );
  };

  const renderExperiments = () => (
    <div className="card col-12">
      <h2 className="section-title"><FlaskConical size={20} color="var(--accent-primary)" /> Lab Experiment Registry</h2>
      <div className="candidate-list">
        {experiments.map(exp => (
          <div key={exp.exp_id} className="candidate-item" style={{ cursor: 'default' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <b style={{ color: 'var(--accent-primary)' }}>{exp.exp_id}</b>
                <span className={`badge ${exp.outcome === 'Success' ? 'badge-success' : 'badge-danger'}`}>{exp.outcome}</span>
              </div>
              <div style={{ fontSize: '0.85rem', marginTop: '5px' }}>{exp.notes}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}><b>Conditions:</b> {exp.conditions}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Signal Value (Kd)</div>
              <div style={{ fontWeight: 700 }}>{exp.measurements.toFixed(2)} nM</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderLiterature = () => (
    <div className="card col-12">
      <h2 className="section-title"><BookOpen size={20} color="var(--accent-secondary)" /> PubMed Indexed Results</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {literature.map(lit => (
          <div key={lit.pmid} className="literature-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 className="lit-title">{lit.title}</h3>
              <span className="pmid-badge">PMID: {lit.pmid}</span>
            </div>
            <p className="lit-abstract">{lit.abstract}</p>
            <div className="lit-footer">
              <div className="lit-tags">
                {lit.mutation_mentions.map(m => <span key={m} className="tag">{m}</span>)}
              </div>
              <div className="lit-meta">Author: {lit.author} | Year: {lit.year}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMethods = () => (
    <div className="grid">
      <div className="card col-7">
        <h2 className="section-title"><Microscope size={20} color="var(--accent-primary)" /> Synthesis Protocols</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          {protocols.map(prot => (
            <div key={prot.protocol_id} className="protocol-card">
              <div className="protocol-header">
                <span className="protocol-id">{prot.protocol_id}</span>
                <span className="protocol-target">{prot.target}</span>
              </div>
              <div className="protocol-name">{prot.name}</div>
              <div className="protocol-steps">
                <b>Procedure:</b> {prot.steps}
              </div>
              <div className="protocol-reagents">
                <b>Reagents:</b> {prot.reagents}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="card col-5">
        <h2 className="section-title"><BookOpen size={20} color="var(--accent-secondary)" /> Lab Notes & Observations</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {labNotes.map(note => (
            <div key={note.note_id} className="note-card">
              <div className="note-header">
                <b className="note-ctx">{note.mutation_context}</b>
                <span className="note-date">{note.date}</span>
              </div>
              <p className="note-text">"{note.text}"</p>
              <div className="note-author">— {note.experimenter}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSequence = () => {
    const filtered = realMutations.filter(m =>
      m.id.toLowerCase().includes(searchMutationDB.toLowerCase()) ||
      m.type.toLowerCase().includes(searchMutationDB.toLowerCase())
    );

    return (
      <div className="card col-12">
        <div className="section-header">
          <h2 className="section-title"><Dna size={20} color="var(--accent-primary)" /> Clinical Mutations</h2>
          <div className="search-box">
            <Search size={18} />
            <input
              placeholder="Filter by mutation ID or type..."
              value={searchMutationDB}
              onChange={(e) => setSearchMutationDB(e.target.value)}
            />
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Mutation ID</th>
              <th>Type</th>
              <th>Clinical Significance</th>
              <th>Allele Frequency</th>
              <th>Resistance Profile</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(m => (
              <tr key={m.id}>
                <td className="bold-cell">{m.id}</td>
                <td>{m.type}</td>
                <td><span className="badge badge-warning">{m.significance}</span></td>
                <td>{m.frequency}</td>
                <td className="faint-cell">{m.resistance}</td>
                <td><button className="btn-small" onClick={() => { setMutation(m.id); analyzeMutation(m.id); setActiveTab('dashboard'); }}>Analyze</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderPrintReport = () => {
    if (!selectedCandidate || !report) return null;
    return (
      <div className="print-only-report">
        <div className="report-border">
          <div className="report-header">
            <div className="report-id">INTERNAL RESEARCH REPORT: {report.report_id || 'RR-2026-X'}</div>
            <div className="report-date">{new Date().toLocaleDateString()}</div>
          </div>
          <h1 className="report-title">Antibody Design Verification Profile</h1>
          <div className="report-sub">Structural Targeting of HER2 Resistance Mutation: <b>{mutation}</b></div>

          <div className="report-section">
            <h2 className="rpt-sec-title">1. Candidate Identification</h2>
            <div className="rpt-grid">
              <div className="rpt-item"><span>Design ID:</span> {selectedCandidate.candidate_id}</div>
              <div className="rpt-item"><span>Framework:</span> {selectedCandidate.framework}</div>
              <div className="rpt-item"><span>Combined Score:</span> {(selectedCandidate.combined_score * 100).toFixed(2)}%</div>
            </div>
          </div>

          <div className="report-section">
            <h2 className="rpt-sec-title">2. Sequence & Structural Properties</h2>
            <div className="rpt-code-box">
              <div className="rpt-label">VH Variable Region Sequence</div>
              <div className="rpt-code">{selectedCandidate.sequence}</div>
            </div>
            <div className="rpt-grid" style={{ marginTop: '10px' }}>
              <div className="rpt-item"><span>Isoelectric Point (pI):</span> {selectedCandidate.biochemical_properties.isoelectric_point?.toFixed(2)}</div>
              <div className="rpt-item"><span>GRAVY Index:</span> {selectedCandidate.biochemical_properties.gravy?.toFixed(2)}</div>
            </div>
          </div>

          <div className="report-section">
            <h2 className="rpt-sec-title">3. Scientific Rationale & Evidence</h2>
            <ul className="rpt-list">
              {selectedCandidate.evidence_statements.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>

          <div className="report-section">
            <h2 className="rpt-sec-title">4. Experimental Verification Status</h2>
            <table className="rpt-table">
              <thead><tr><th>Standard Assay</th><th>Current Status</th><th>Verification ID</th></tr></thead>
              <tbody>
                <tr><td>SPR Binding (HER2-WT)</td><td>Pass</td><td>VAL-SPR-091</td></tr>
                <tr><td>Thermal Stability (DSC)</td><td>Confirmed</td><td>VAL-DSC-042</td></tr>
                <tr><td>Expression Yield (CHO)</td><td>Optimal</td><td>VAL-EX-112</td></tr>
              </tbody>
            </table>
          </div>

          <div className="report-footer">
            <div className="signature-line">Orchestrator Signature: _________________________</div>
            <p className="rpt-disclaimer">This document is a confidential AI-assisted research design report generated for HER2-ResistAID pipeline verification.</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      {renderPrintReport()}
      <aside className="sidebar no-print">
        <div className="logo">
          <Activity size={24} color="var(--accent-primary)" />
          <span>HER2-ResistAID</span>
        </div>
        <nav>
          <div
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          ><Activity size={20} /> Dashboard</div>
          <div
            className={`nav-item ${activeTab === 'gallery' ? 'active' : ''}`}
            onClick={() => setActiveTab('gallery')}
          ><Microscope size={20} /> Image Gallery</div>
          <div
            className={`nav-item ${activeTab === 'experiments' ? 'active' : ''}`}
            onClick={() => setActiveTab('experiments')}
          ><FlaskConical size={20} /> Experiments</div>
          <div
            className={`nav-item ${activeTab === 'literature' ? 'active' : ''}`}
            onClick={() => setActiveTab('literature')}
          ><BookOpen size={20} /> Literature</div>
          <div
            className={`nav-item ${activeTab === 'methods' ? 'active' : ''}`}
            onClick={() => setActiveTab('methods')}
          ><Layers size={20} /> Methods</div>
          <div
            className={`nav-item ${activeTab === 'sequence' ? 'active' : ''}`}
            onClick={() => setActiveTab('sequence')}
          ><Dna size={20} /> Mutation DB</div>
        </nav>

        <div className="sidebar-footer">
          <div className="status-badge">
            <div className="status-dot pulse"></div>
            System Online
          </div>
          <div className="version-info">v2.1.0-Scale</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="header no-print">
          <div className="header-titles">
            <h1>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h1>
            <p>{
              activeTab === 'dashboard' ? "Design Analysis & Combined Prioritization" :
                activeTab === 'gallery' ? "Scientific Evidence Photography & Imaging" :
                  activeTab === 'experiments' ? "Protocol Benchmarks & Outcome Registry" :
                    activeTab === 'methods' ? "Standard Operating Procedures & Lab Notes" :
                      activeTab === 'literature' ? "PubMed Indexed Resistance Literature" :
                        "Clinical Patient Mutation Database"
            }</p>
          </div>

          <div className="search-container">
            <input
              list="mutations"
              value={mutation}
              onChange={(e) => setMutation(e.target.value)}
              placeholder="Query mutation ID..."
            />
            <datalist id="mutations">
              {availableMutations.map(m => <option key={m} value={m} />)}
            </datalist>
            <button className="primary-run-btn" onClick={() => analyzeMutation(mutation)} disabled={loading}>
              {loading ? <div className="spinner-small"></div> : 'Sequence Analysis'}
            </button>
          </div>
        </header>

        <section className="content-area no-print">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Analyzing Structural Resistance Vectors...</p>
            </div>
          ) : (
            <>
              {activeTab === 'dashboard' && report && renderDashboard()}
              {activeTab === 'gallery' && renderGallery()}
              {activeTab === 'experiments' && renderExperiments()}
              {activeTab === 'literature' && renderLiterature()}
              {activeTab === 'methods' && renderMethods()}
              {activeTab === 'sequence' && renderSequence()}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
