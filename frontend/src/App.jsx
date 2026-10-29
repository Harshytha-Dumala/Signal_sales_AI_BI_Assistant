import { useEffect, useState } from 'react';
import { BarChart3, Send, Sparkles, Database, ShieldCheck, RotateCcw } from 'lucide-react';

const examples = [
  'What is the total revenue?',
  'Which product generated the highest revenue?',
  'What is the monthly revenue trend?',
  'Which region generated the highest sales?',
  'Compare revenue between January and February.'
];

function App() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/summary').then(r => {
      if (!r.ok) throw new Error('API unavailable');
      return r.json();
    }).then(setSummary).catch(() => setError('Backend is not running. Start the backend using the README instructions.'));
  }, []);

  async function ask(q = question) {
    if (!q.trim()) { setError('Enter a question first.'); return; }
    setLoading(true); setError(''); setResult(null); setQuestion(q);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ask', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Request failed.');
      setResult(data);
    } catch (e) { setError(e.message || 'Could not connect to backend.'); }
    finally { setLoading(false); }
  }

  function formatValue(value) {
    if (typeof value === 'number') return value.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    return value ?? '—';
  }

  return <main className="shell">
    <header className="topbar">
      <div className="brand-mark"><BarChart3 size={22}/></div>
      <div><div className="brand">Signal<span>Sales</span></div><div className="brand-sub">BUSINESS INTELLIGENCE ASSISTANT</div></div>
      <div className="status"><span className="dot"/> Local analytics</div>
    </header>

    <section className="hero">
      <div className="eyebrow"><Sparkles size={14}/> ASK YOUR SALES DATA</div>
      <h1>Turn questions into<br/><span>clear business answers.</span></h1>
      <p>Ask in plain English. Every answer is calculated from your sales database and shown with supporting figures.</p>
    </section>

    <section className="metrics">
      <div className="metric"><div className="metric-icon"><Database size={17}/></div><div><div className="metric-label">CSV records loaded</div><div className="metric-value">{summary ? summary.loaded_records : '—'}</div></div></div>
      <div className="metric"><div className="metric-icon"><ShieldCheck size={17}/></div><div><div className="metric-label">Completed records</div><div className="metric-value">{summary ? summary.completed_records : '—'}</div></div></div>
      <div className="metric"><div className="metric-icon"><RotateCcw size={17}/></div><div><div className="metric-label">Records excluded from revenue</div><div className="metric-value">{summary ? summary.records_excluded_from_revenue : '—'}</div></div></div>
    </section>

    <section className="workspace">
      <div className="question-panel">
        <div className="section-heading"><span className="step">01</span><div><h2>Ask a question</h2><p>Start with one of these supported analyses.</p></div></div>
        <div className="examples">{examples.map(ex => <button key={ex} className="example" onClick={() => { setQuestion(ex); ask(ex); }}>{ex}<span>↗</span></button>)}</div>
        <form onSubmit={e => { e.preventDefault(); ask(); }} className="ask-form">
          <textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder="e.g. Which region generated the highest sales?" rows="3" maxLength="500"/>
          <div className="input-footer"><span>{question.length}/500</span><button className="submit" disabled={loading}>{loading ? 'Analyzing…' : 'Ask assistant'} <Send size={15}/></button></div>
        </form>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="answer-panel">
        <div className="section-heading"><span className="step">02</span><div><h2>Answer</h2><p>Result and supporting data</p></div></div>
        {!result && <div className="empty"><div className="empty-icon"><Sparkles size={23}/></div><h3>Your answer will appear here</h3><p>Choose a question or type your own. The assistant uses predefined, read-only analytics rather than executing AI-generated SQL.</p></div>}
        {result && <div className="result">
          <div className="answer-label">ANSWER</div><p className="answer-text">{result.answer}</p>
          {result.value !== undefined && <div className="value-card"><span>Calculated value</span><strong>{formatValue(result.value)}</strong></div>}
          {Array.isArray(result.supporting_data) && result.supporting_data.length > 0 && <div className="table-wrap"><table><thead><tr>{Object.keys(result.supporting_data[0]).map(k => <th key={k}>{k.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{result.supporting_data.map((row,i) => <tr key={i}>{Object.values(row).map((v,j) => <td key={j}>{formatValue(v)}</td>)}</tr>)}</tbody></table></div>}
          {result.definition && <div className="definition"><ShieldCheck size={15}/><span>{result.definition}</span></div>}
          <div className="method">Interpretation: <strong>{result.interpretation_method}</strong></div>
          {result.suggestions && <div className="suggestions">{result.suggestions.map(s => <button key={s} onClick={() => {setQuestion(s); ask(s);}}>{s}</button>)}</div>}
        </div>}
      </div>
    </section>
    <footer><span>SignalSales · Mini AI BI Assistant</span><span>AI interprets · SQL calculates · You verify</span></footer>
  </main>;
}
export default App;
