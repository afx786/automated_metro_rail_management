import React, { useEffect, useState } from 'react';

export default function Dashboard() {
  const [trainsets, setTrainsets] = useState([]);
  const [sensors, setSensors] = useState({});
  const [plan, setPlan] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/trainsets/')
      .then(r => r.json())
      .then(data => {
        setTrainsets(data);
        data.forEach(t => {
          fetch(`http://localhost:8000/iot/trainsets/${t.code}`)
            .then(r => r.json())
            .then(sensorData => setSensors(prev => ({ ...prev, [t.code]: sensorData })))
            .catch(() => {});
        });
      })
      .catch(() => {});
  }, []);

  const refresh = async () => {
    await fetch('http://localhost:8000/trainsets/refresh/maximo', { method: 'POST' });
    const r = await fetch('http://localhost:8000/trainsets/');
    const updated = await r.json();
    setTrainsets(updated);
    updated.forEach(t => {
      fetch(`http://localhost:8000/iot/trainsets/${t.code}`)
        .then(r => r.json())
        .then(sensorData => setSensors(prev => ({ ...prev, [t.code]: sensorData })))
        .catch(() => {});
    });
  };

  const run = async () => {
    const res = await fetch('http://localhost:8000/plans/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    setPlan(data);
  };

  return (
    <div className="px-4 py-6 max-w-screen-xl mx-auto">
      <header className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-gray-900">
          KMRL Real Maximo Dashboard
        </h1>
      </header>

      <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8">
        <button
          onClick={refresh}
          className="w-full sm:w-auto px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded shadow transition"
        >
          Refresh from Maximo
        </button>
        <button
          onClick={run}
          className="w-full sm:w-auto px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded shadow transition"
        >
          Run Optimizer
        </button>
      </div>

      <section className="mb-12">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-800 mb-4">
          Trainsets ({trainsets.length})
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {trainsets.map(t => {
            const s = sensors[t.code] || {};
            return (
              <div
                key={t.code}
                className="bg-white rounded-lg shadow p-4 flex flex-col justify-between border border-gray-200"
              >
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900">{t.code}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    <span className="font-medium">Job Open:</span> {String(t.job_card_open)}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Mileage:</span> {t.mileage.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Needs Deep Clean:</span> {String(t.needs_deep_clean)}
                  </p>
                </div>

                
                <div className="mt-4 border-t pt-3">
                  <h4 className="text-sm sm:text-base font-medium text-gray-800 mb-2">
                    Sensor Data
                  </h4>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Brake Temp:</span>{' '}
                    {s.brake_temp != null ? `${s.brake_temp.toFixed(1)}°C` : '—'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">HVAC:</span> {s.hvac_status ?? '—'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Signal:</span>{' '}
                    {s.signal_comm_ok == null ? '—' : s.signal_comm_ok ? '✔️' : '✘'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {plan && (
        <section className="mb-6">
          <h3 className="text-xl sm:text-2xl font-semibold text-gray-800 mb-4">
            Plan (Revenue)
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white rounded-lg shadow">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Trainset</th>
                  <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {plan.revenue.map(p => (
                  <tr key={p.trainset} className="border-t">
                    <td className="px-4 py-2 text-sm text-gray-800">{p.trainset}</td>
                    <td className="px-4 py-2 text-sm text-gray-800">{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
