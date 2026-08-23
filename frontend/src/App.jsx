import React, { useState, useEffect, useRef } from 'react';
import { 
  UploadCloud, 
  CheckCircle2, 
  Loader2, 
  FileText, 
  Code2, 
  GitGraph, 
  Download, 
  Layers, 
  Sparkles 
} from 'lucide-react';
import mermaid from 'mermaid';

mermaid.initialize({ startOnLoad: false, theme: 'neutral' });

function MermaidViewer({ chart, id }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (chart && containerRef.current) {
      mermaid.render(`mermaid-${id}-${Date.now()}`, chart)
        .then(({ svg }) => {
          if (containerRef.current) containerRef.current.innerHTML = svg;
        })
        .catch(() => {
          if (containerRef.current) {
            containerRef.current.innerHTML = `<pre class="text-xs text-red-400 font-mono">${chart}</pre>`;
          }
        });
    }
  }, [chart, id]);

  return <div ref={containerRef} className="p-4 bg-white text-slate-900 rounded-lg my-2 overflow-x-auto shadow-inner" />;
}

export default function App() {
  const [studentName, setStudentName] = useState('Alex Rivera');
  const [regNumber, setRegNumber] = useState('21BCE1092');
  const [file, setFile] = useState(null);
  
  const [status, setStatus] = useState('idle'); // idle | analyzing | analyzed | generating | ready
  const [assessment, setAssessment] = useState(null);
  const [results, setResults] = useState(null);
  const [downloading, setDownloading] = useState(false);

  const handleAnalyze = async () => {
    if (!file) return alert('Please select an assessment PDF.');
    setStatus('analyzing');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/analyze-assessment', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAssessment(data);
      setStatus('analyzed');
    } catch (err) {
      alert('Analysis Error: ' + err.message);
      setStatus('idle');
    }
  };

  const handleGenerate = async () => {
    setStatus('generating');
    const formData = new FormData();
    formData.append('student_name', studentName);
    formData.append('reg_number', regNumber);
    formData.append('assessment_schema_json', JSON.stringify(assessment));

    try {
      const res = await fetch('http://localhost:8000/api/generate-answers', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults(data);
      setStatus('ready');
    } catch (err) {
      alert('Generation Error: ' + err.message);
      setStatus('analyzed');
    }
  };

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const res = await fetch('http://localhost:8000/api/download-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(results),
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${assessment.course_code}_Solution_Report.pdf`;
      a.click();
    } catch {
      alert('PDF generation failed.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-16">
      <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg text-white">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Dynamic Assessment Engine</h1>
              <p className="text-xs text-slate-400">Autonomous Mark-Calibrated Intelligence</p>
            </div>
          </div>
          {status === 'ready' && (
            <button
              onClick={handleDownloadPDF}
              disabled={downloading}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition"
            >
              {downloading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Download className="w-4 h-4"/>}
              Download PDF Report
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 mt-8 space-y-8">
        {/* Upload & Setup */}
        <section className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-6 shadow-xl">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" /> Assessment Submission Setup
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-400 font-medium">Student Name</label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 font-medium">Registration Number</label>
              <input
                type="text"
                value={regNumber}
                onChange={(e) => setRegNumber(e.target.value)}
                className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 font-medium">Upload Assessment PDF</label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files[0])}
                className="mt-1 w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600/20 file:text-blue-400 hover:file:bg-blue-600/30 cursor-pointer"
              />
            </div>
          </div>

          <div className="mt-5 flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={status === 'analyzing' || !file}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-sm px-5 py-2 rounded-lg transition"
            >
              {status === 'analyzing' ? <Loader2 className="w-4 h-4 animate-spin"/> : <UploadCloud className="w-4 h-4"/>}
              Analyze Assessment
            </button>
          </div>
        </section>

        {/* Dynamic Analysis Matrix */}
        {assessment && (
          <section className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-6 shadow-xl space-y-6">
            <div className="flex flex-wrap items-center justify-between border-b border-slate-700/70 pb-4 gap-4">
              <div>
                <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                  Structure Extracted
                </span>
                <h3 className="text-xl font-bold text-white mt-1">
                  {assessment.course_name} ({assessment.course_code})
                </h3>
              </div>
              <div className="flex gap-4 text-xs">
                <div className="bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg text-center">
                  <span className="text-slate-400 block">Total Marks</span>
                  <span className="text-sm font-bold text-blue-400">{assessment.total_marks}</span>
                </div>
                <div className="bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg text-center">
                  <span className="text-slate-400 block">Questions</span>
                  <span className="text-sm font-bold text-purple-400">{assessment.total_questions}</span>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
                  <tr>
                    <th className="p-3">Q#</th>
                    <th className="p-3">Question Text</th>
                    <th className="p-3">Marks</th>
                    <th className="p-3">Taxonomy</th>
                    <th className="p-3">Depth Budget</th>
                    <th className="p-3 text-center">Diagram</th>
                    <th className="p-3 text-center">Code</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {assessment.questions.map((q, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="p-3 font-semibold text-white">{q.q_no}</td>
                      <td className="p-3 max-w-sm truncate text-slate-300">{q.question_text}</td>
                      <td className="p-3 font-bold text-amber-400">{q.marks}m</td>
                      <td className="p-3">
                        <span className="bg-purple-900/40 text-purple-300 border border-purple-800 px-1.5 py-0.5 rounded">
                          {q.taxonomy_level}
                        </span>
                      </td>
                      <td className="p-3 font-medium capitalize text-slate-200">{q.depth_budget}</td>
                      <td className="p-3 text-center">{q.requires_diagram ? <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto"/> : '—'}</td>
                      <td className="p-3 text-center">{q.requires_code ? <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto"/> : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {status !== 'ready' && (
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleGenerate}
                  disabled={status === 'generating'}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-sm px-6 py-2.5 rounded-lg transition"
                >
                  {status === 'generating' ? <Loader2 className="w-4 h-4 animate-spin"/> : <FileText className="w-4 h-4"/>}
                  Generate Calibrated Responses
                </button>
              </div>
            )}
          </section>
        )}

        {/* Generated Solutions */}
        {results && (
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Generated Solution Key</h3>
            {results.answers.map((ans, idx) => (
              <div key={idx} className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-6 space-y-4 shadow-lg">
                <div className="flex justify-between items-start border-b border-slate-700/60 pb-3">
                  <div>
                    <h4 className="text-base font-bold text-white flex items-center gap-2">
                      {ans.q_no}
                      <span className="text-xs font-normal text-amber-400 bg-amber-950/50 border border-amber-800 px-2 py-0.5 rounded">
                        {ans.marks} Marks
                      </span>
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">{ans.question_text}</p>
                  </div>
                  <div className="flex gap-2">
                    {ans.diagram_mermaid && (
                      <span className="flex items-center gap-1 text-[11px] bg-indigo-950/70 border border-indigo-800 text-indigo-300 px-2 py-0.5 rounded">
                        <GitGraph className="w-3 h-3"/> Diagram
                      </span>
                    )}
                    {ans.code_snippet && (
                      <span className="flex items-center gap-1 text-[11px] bg-blue-950/70 border border-blue-800 text-blue-300 px-2 py-0.5 rounded">
                        <Code2 className="w-3 h-3"/> Code
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                  {ans.answer_text}
                </div>

                {ans.diagram_mermaid && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold text-slate-400 mb-1">Architecture / Vector Flowchart:</p>
                    <MermaidViewer chart={ans.diagram_mermaid} id={idx} />
                  </div>
                )}

                {ans.code_snippet && (
                  <div className="mt-4 bg-slate-950 border border-slate-800 p-4 rounded-lg font-mono text-xs overflow-x-auto text-emerald-400">
                    <p className="text-slate-500 mb-2">// Verified Code Solution</p>
                    <pre>{ans.code_snippet}</pre>
                  </div>
                )}

                {ans.rubric_evidence?.length > 0 && (
                  <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[10px] text-slate-500 mr-1">Rubric Criteria:</span>
                    {ans.rubric_evidence.map((point, pIdx) => (
                      <span key={pIdx} className="text-[10px] bg-slate-900 border border-slate-700 text-slate-400 px-2 py-0.5 rounded">
                        ✓ {point}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
