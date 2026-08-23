import { useState } from 'react';
import { analyzeAssessment, getStatus, generateAnswers, getPreview, getDownloadUrl } from '../services/api';

const Home = () => {
  const [studentName, setStudentName] = useState('');
  const [regNumber, setRegNumber] = useState('');
  const [file, setFile] = useState<File | null>(null);
  
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [preview, setPreview] = useState<any>(null);

  const handleUpload = async () => {
    if (!studentName || !regNumber || !file) {
      alert("Please fill all fields");
      return;
    }
    
    try {
      setStatus('Uploading...');
      const response = await analyzeAssessment(studentName, regNumber, file);
      setAssessmentId(response.assessment_id);
      setStatus('Analyzing...');
      
      pollStatus(response.assessment_id);
    } catch (e: any) {
      alert(e.message || "Upload failed");
    }
  };
  
  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await getStatus(id);
        setStatus(res.status);
        setProgress(res.progress);
        
        if (res.progress === 50) {
          clearInterval(interval);
          const p = await getPreview(id);
          setPreview(p);
        } else if (res.progress === 100) {
          clearInterval(interval);
        } else if (res.status.includes('failed')) {
          clearInterval(interval);
        }
      } catch (e) {
        console.error(e);
        clearInterval(interval);
      }
    }, 2000);
  };

  const handleGenerate = async () => {
    if (!assessmentId) return;
    try {
      await generateAnswers(assessmentId);
      pollStatus(assessmentId);
    } catch (e: any) {
      alert(e.message || "Generation failed");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <div className="max-w-2xl w-full bg-white shadow-lg rounded-xl p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Assessment Generator</h1>
        <p className="text-gray-600 mb-8">Upload your assessment and let AI create a complete answer document.</p>
        
        {!assessmentId && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Student Name</label>
              <input type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" 
                value={studentName} onChange={e => setStudentName(e.target.value)} placeholder="Enter student name"/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Registration Number</label>
              <input type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" 
                value={regNumber} onChange={e => setRegNumber(e.target.value)} placeholder="Enter registration number"/>
            </div>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:bg-gray-50 transition"
                onClick={() => document.getElementById('fileUpload')?.click()}>
              <input type="file" id="fileUpload" className="hidden" accept=".pdf" onChange={e => setFile(e.target.files?.[0] || null)} />
              {file ? (
                <p className="text-blue-600 font-medium">{file.name}</p>
              ) : (
                <p className="text-gray-500">Drag assessment PDF here or <span className="text-blue-600">Choose PDF</span></p>
              )}
            </div>
            
            <button onClick={handleUpload} className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition">
              Analyze Assessment
            </button>
          </div>
        )}

        {assessmentId && (
          <div className="mt-8 space-y-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-blue-700">{status}</span>
                <span className="text-sm font-medium text-blue-700">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
            
            {preview && progress === 50 && (
              <div className="bg-gray-50 p-6 rounded-lg border">
                <h3 className="text-xl font-bold mb-4 text-gray-800">Assessment Summary</h3>
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-6">
                  <div><span className="font-semibold">Course:</span> {preview.course_name}</div>
                  <div><span className="font-semibold">Course Code:</span> {preview.course_code}</div>
                  <div><span className="font-semibold">Assessment:</span> {preview.assessment_type}</div>
                  <div><span className="font-semibold">Questions:</span> {preview.questions?.length}</div>
                  <div><span className="font-semibold">Total Marks:</span> {preview.total_marks}</div>
                </div>
                
                <button onClick={handleGenerate} className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg hover:bg-green-700 transition">
                  Generate Answers
                </button>
              </div>
            )}
            
            {progress === 100 && (
              <div className="text-center pt-4">
                <div className="text-green-500 text-5xl mb-4">✓</div>
                <h3 className="text-xl font-bold text-gray-800 mb-6">Generation Complete</h3>
                <a href={getDownloadUrl(assessmentId)} download className="inline-block w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition">
                  Download Final Assessment PDF
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
