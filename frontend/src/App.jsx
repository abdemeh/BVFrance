import React, { useState, useEffect } from 'react';
import {
   Search, Users, Award, TrendingUp, ChevronRight, ShieldCheck, Zap,
   LayoutGrid, BarChart, Filter, Layers, Map as MapIcon, ArrowDown, Activity,
   Table as TableIcon, Layout
} from 'lucide-react';
import {
   PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
   BarChart as ReBarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
   LineChart, Line
} from 'recharts';
import './App.css';

const API_BASE = 'http://localhost:8000';
const COLORS = ['#5599ff', '#1f883b', '#db731f', '#5c3189', '#ef4444', '#ec4899', '#06b6d4', '#475569'];

function App() {
   const [activeTab, setActiveTab] = useState('NATIONAL');
   const [searchTerm, setSearchTerm] = useState('');
   const [suggestions, setSuggestions] = useState([]);
   const [stats, setStats] = useState(null);
   const [advStats, setAdvStats] = useState(null);
   const [communeData, setCommuneData] = useState(null);
   const [geoData, setGeoData] = useState(null);
   const [loading, setLoading] = useState(false);
   const [tour, setTour] = useState(0);

   const tabs = [
      { id: 'NATIONAL', label: 'National' },
      { id: 'REGION', label: 'Région' },
      { id: 'DEPARTEMENT', label: 'Département' },
      { id: 'COMMUNE', label: 'Commune' },
      { id: 'ADVANCED', label: 'Analyses' },
   ];

   const fetchData = async () => {
      if (activeTab === 'REGION' || activeTab === 'DEPARTEMENT' || activeTab === 'COMMUNE') {
         if (!geoData && !communeData) return;
      }

      setLoading(true);
      try {
         if (activeTab === 'NATIONAL') {
            const res = await fetch(`${API_BASE}/get/stats/global?tour=${tour}`);
            setStats(await res.json());
         } else if (activeTab === 'ADVANCED') {
            const t = tour === 0 ? 1 : tour;
            const res = await fetch(`${API_BASE}/get/stats/avancees?tour=${t}`);
            setAdvStats(await res.json());
         }
      } catch (e) { console.error(e); }
      setLoading(false);
   };

   useEffect(() => { fetchData(); }, [tour, activeTab]);

   const searchData = async (val) => {
      if (val.length < 2) { setSuggestions([]); return; }
      let level = activeTab === 'REGION' ? 'region' : activeTab === 'DEPARTEMENT' ? 'departement' : 'commune';
      try {
         const res = await fetch(`${API_BASE}/search/${level}?q=${val}`);
         setSuggestions(await res.json());
      } catch (e) { setSuggestions([]); }
   };

   useEffect(() => {
      const timer = setTimeout(() => searchData(searchTerm), 300);
      return () => clearTimeout(timer);
   }, [searchTerm]);

   const selectResult = async (item) => {
      setLoading(true); setSuggestions([]); setSearchTerm('');
      try {
         if (activeTab === 'REGION' || activeTab === 'DEPARTEMENT') {
            const res = await fetch(`${API_BASE}/get/stats/geo/${activeTab.toLowerCase()}/${item.id}?tour=0`);
            setGeoData(await res.json());
         } else {
            const res = await fetch(`${API_BASE}/get/resultats/commune/${item.id}?tour=1`);
            setCommuneData(await res.json());
            setActiveTab('COMMUNE');
         }
      } catch (e) { console.error(e); }
      setLoading(false);
   };

   const clearGeo = (newTab) => {
      setActiveTab(newTab);
      if (newTab !== 'COMMUNE') setCommuneData(null);
      if (newTab !== 'REGION' && newTab !== 'DEPARTEMENT' && newTab !== 'GEO') setGeoData(null);
   };

   const formatNum = (num, level) => {
      if (!num) return '0';
      if (level === 'NATIONAL') return (num / 1000000).toFixed(2) + 'M';
      if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
      return num.toLocaleString();
   };

   const hasData = (activeTab === 'NATIONAL' && stats) ||
      (activeTab === 'ADVANCED' && advStats) ||
      (activeTab === 'COMMUNE' && communeData) ||
      (['REGION', 'DEPARTEMENT', 'GEO'].includes(activeTab) && geoData);

   return (
      <div className="compact-app">
         <div className="header-wrapper">
            <div className="capsule-nav animate-pro">
               <div className="brand-capsule">
                  <div className="brand-dot"></div>
                  <span>BVFrance</span>
               </div>
               <div className="nav-buttons">
                  {tabs.map(tab => (
                     <button
                        key={tab.id}
                        className={activeTab === tab.id ? 'active' : ''}
                        onClick={() => clearGeo(tab.id)}
                     >
                        {tab.label}
                     </button>
                  ))}
               </div>
            </div>
         </div>

         <main className="dashboard-view">
            <div className="section-title animate-pro">
               <span className="title-tag">Résultats 2026</span>
               <h1>
                  {activeTab === 'NATIONAL' ? 'Tableau National' :
                     activeTab === 'ADVANCED' ? 'Analytics Pro' :
                        activeTab === 'COMMUNE' ? (communeData?.nom || 'Choisir Commune') :
                           (geoData?.label || (activeTab === 'REGION' ? 'Choisir Région' : 'Choisir Département'))}
               </h1>
            </div>

            {activeTab !== 'ADVANCED' && (
               <div className="controls-row animate-pro">
                  <div className="search-pill-modern">
                     <Search size={20} className="text-muted" />
                     <input
                        placeholder={`Rechercher ${activeTab.toLowerCase()}...`}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                     />
                     {suggestions.length > 0 && (
                        <div className="search-results-v4 glass">
                           {suggestions.map(s => (
                              <div key={s.id} className="res-item-v4" onClick={() => selectResult(s)}>
                                 <span>{s.nom}</span>
                                 {s.dep && <small>({s.dep})</small>}
                              </div>
                           ))}
                        </div>
                     )}
                  </div>

                  {activeTab === 'NATIONAL' && (
                     <div className="tour-pill-modern">
                        {[0, 1, 2].map(t => (
                           <button key={t} className={tour === t ? 'active' : ''} onClick={() => setTour(t)}>
                              {t === 0 ? 'Total' : `Tour ${t}`}
                           </button>
                        ))}
                     </div>
                  )}
               </div>
            )}

            {!hasData && !loading && activeTab !== 'ADVANCED' ? (
               <div className="empty-state animate-pro">
                  <h3>SÉLECTIONNER UN LIEU</h3>
                  <p>Utilisez la barre de recherche ci-dessus pour explorer les données électorales.</p>
               </div>
            ) : loading ? (
               <div className="empty-state"><h3>CHARGEMENT...</h3></div>
            ) : (
               <div className="dashboard-content animate-pro">

                  {['NATIONAL', 'REGION', 'DEPARTEMENT', 'GEO'].includes(activeTab) && (stats || geoData) && (
                     <div className="kpi-grid-modern">
                        <div className="card-white"><label>INSCRITS</label><div className="val">{formatNum(activeTab === 'NATIONAL' ? stats.metrics.total_inscrits : geoData.inscrits, activeTab)}</div></div>
                        <div className="card-white"><label>PARTICIPATION</label><div className="val">{(activeTab === 'NATIONAL' ? stats.metrics.avg_part : geoData.participation).toFixed(1)}%</div></div>
                        <div className="card-white"><label>VOTANTS</label><div className="val">{formatNum(activeTab === 'NATIONAL' ? stats.metrics.total_votants : (geoData.inscrits * geoData.participation / 100), activeTab)}</div></div>
                        <div className="card-white"><label>LEADER</label><div className="val" style={{ fontSize: '1.5rem' }}>{(activeTab === 'NATIONAL' ? stats.nuances[0]?.Nuance : geoData.nuances[0]?.Nuance) || 'N/A'}</div></div>
                     </div>
                  )}

                  {['NATIONAL', 'REGION', 'DEPARTEMENT', 'GEO'].includes(activeTab) && (stats || geoData) && (
                     <div className="chart-grid-modern">
                        <div className="viz-card-modern">
                           <h4><div className="dot-icon"></div> RÉPARTITION DES SIÈGES</h4>
                           <ResponsiveContainer width="100%" height={300}>
                              <PieChart>
                                 <Pie
                                    data={(activeTab === 'NATIONAL' ? stats.nuances : geoData.nuances).slice(0, 10)}
                                    dataKey="total_sieges" nameKey="Nuance" cx="50%" cy="50%" innerRadius={70} outerRadius={110} paddingAngle={4}
                                 >
                                    {(activeTab === 'NATIONAL' ? stats.nuances : geoData.nuances).map((_, index) => (
                                       <Cell key={index} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                 </Pie>
                                 <Tooltip contentStyle={{ borderRadius: '2rem', border: 'none', boxShadow: '0 10px 30px rgba(0,0,0,0.1)', padding: '1rem' }} />
                                 <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase' }} />
                              </PieChart>
                           </ResponsiveContainer>
                        </div>

                        <div className="viz-card-modern">
                           <h4><div className="dot-icon" style={{ background: '#db731f' }}></div> PARTS DE VOIX</h4>
                           <ResponsiveContainer width="100%" height={300}>
                              <ReBarChart data={(activeTab === 'NATIONAL' ? stats.nuances : geoData.nuances).slice(0, 8)}>
                                 <CartesianGrid strokeDasharray="5 5" vertical={false} stroke="#f1f5f9" />
                                 <XAxis dataKey="Nuance" fontSize={10} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontWeight: 700 }} />
                                 <YAxis axisLine={false} tickLine={false} fontSize={10} tick={{ fill: '#64748b', fontWeight: 700 }} />
                                 <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '1rem' }} />
                                 <Bar dataKey="total_voix" fill="#5599ff" radius={[10, 10, 0, 0]} />
                              </ReBarChart>
                           </ResponsiveContainer>
                        </div>
                     </div>
                  )}

                  {activeTab === 'COMMUNE' && communeData && (
                     <div className="commune-pro-view">
                        <div className="kpi-grid-modern">
                           <div className="card-white"><label>NOM COMMUNE</label><div className="val" style={{ fontSize: '1.5rem' }}>{communeData.nom}</div></div>
                           <div className="card-white"><label>INSCRITS</label><div className="val">{formatNum(communeData.inscrits, 'COMMUNE')}</div></div>
                           <div className="card-white"><label>PARTICIPATION</label><div className="val">{communeData.participation}%</div></div>
                           <div className="card-white"><label>DEPT</label><div className="val">{communeData.dep}</div></div>
                        </div>
                        <div className="commune-table-wrap mt-8">
                           <table className="modern-table-v4">
                              <thead><tr><th>CANDIDATURE</th><th className="r">VOIX</th><th className="r">% EXP</th><th className="r">SIÈGES</th></tr></thead>
                              <tbody>
                                 {communeData.lists.map((l, i) => (
                                    <tr key={i}>
                                       <td>
                                          <div className="l-name-bold">{l.Libelle || 'Liste sans nom'}</div>
                                          <div className="l-nuance-tag">{l.Nuance}</div>
                                       </td>
                                       <td className="r font-bold">{l.Voix.toLocaleString()}</td>
                                       <td className="r font-bold">{l.pct_exprimes}%</td>
                                       <td className="r"><strong style={{ fontSize: '1.25rem' }}>{l.Sieges}</strong></td>
                                    </tr>
                                 ))}
                              </tbody>
                           </table>
                        </div>
                     </div>
                  )}

                  {activeTab === 'ADVANCED' && advStats && (
                     <div className="advanced-pro-dashboard animate-slide-up">

                        <div className="tour-pill-modern mb-8" style={{ justifyContent: 'center' }}>
                           <button className={tour === 1 ? 'active' : ''} onClick={() => setTour(1)}>Tour 1</button>
                           <button className={tour === 2 ? 'active' : ''} onClick={() => setTour(2)}>Tour 2</button>
                        </div>

                        <div className="chart-grid-modern">
                           <div className="viz-card-modern">
                              <h4><Award size={18} /> SIÈGES & COMMUNES PAR NUANCE</h4>
                              <ResponsiveContainer width="100%" height={350}>
                                 <ReBarChart data={advStats.repartition.nuances_analytics.slice(0, 8)}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="Nuance" fontSize={10} axisLine={false} tickLine={false} />
                                    <YAxis axisLine={false} tickLine={false} />
                                    <Tooltip />
                                    <Legend />
                                    <Bar name="Sièges" dataKey="s" fill="#5599ff" radius={[4, 4, 0, 0]} />
                                    <Bar name="Communes" dataKey="nc" fill="#1f883b" radius={[4, 4, 0, 0]} />
                                 </ReBarChart>
                              </ResponsiveContainer>
                           </div>

                           <div className="viz-card-modern">
                              <h4><ShieldCheck size={18} /> MAJORITÉ VS OPPOSITION</h4>
                              <ResponsiveContainer width="100%" height={300}>
                                 <PieChart>
                                    <Pie
                                       data={advStats.repartition.majorite_vs_opposition}
                                       dataKey="total_sieges" nameKey="statut" cx="50%" cy="50%" innerRadius={70} outerRadius={100}
                                       paddingAngle={5}
                                    >
                                       <Cell fill="#5599ff" />
                                       <Cell fill="#db731f" />
                                    </Pie>
                                    <Tooltip />
                                    <Legend />
                                 </PieChart>
                              </ResponsiveContainer>
                           </div>
                        </div>

                        <div className="layout-grid-2-1 mt-8">
                           <div className="viz-card-modern">
                              <h4><Users size={18} /> PERCENTILES DES INSCRITS</h4>
                              <ResponsiveContainer width="100%" height={300}>
                                 <LineChart data={[
                                    { p: 'P25', v: advStats.descriptive.inscrits.p25 },
                                    { p: 'P50', v: advStats.descriptive.inscrits.med },
                                    { p: 'P75', v: advStats.descriptive.inscrits.p75 },
                                    { p: 'P90', v: advStats.descriptive.inscrits.p90 },
                                    { p: 'P99', v: advStats.descriptive.inscrits.p99 }
                                 ]}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="p" axisLine={false} tickLine={false} />
                                    <YAxis axisLine={false} tickLine={false} />
                                    <Tooltip />
                                    <Line type="monotone" dataKey="v" stroke="#5c3189" strokeWidth={5} dot={{ r: 8, fill: '#5c3189' }} />
                                 </LineChart>
                              </ResponsiveContainer>
                           </div>

                           <div className="viz-card-modern">
                              <h4><BarChart size={18} /> SIÈGES PAR COMMUNE</h4>
                              <div className="stats-list mt-6">
                                 <div className="s-row"><span>Moyenne</span> <strong>{advStats.descriptive.sieges_commune.mean}</strong></div>
                                 <div className="s-row"><span>Médiane</span> <strong>{advStats.descriptive.sieges_commune.med}</strong></div>
                                 <div className="s-row"><span>P25</span> <strong>{advStats.descriptive.sieges_commune.p25}</strong></div>
                                 <div className="s-row"><span>P75</span> <strong>{advStats.descriptive.sieges_commune.p75}</strong></div>
                                 <div className="s-row"><span>P99</span> <strong>{advStats.descriptive.sieges_commune.p99}</strong></div>
                              </div>
                           </div>
                        </div>
                     </div>
                  )}

               </div>
            )}
         </main>
      </div>
   );
}

export default App;

