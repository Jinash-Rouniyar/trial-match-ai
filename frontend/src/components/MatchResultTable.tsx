import React from "react";
import { TrialMatch } from "../api/client";

interface Props {
  trials: TrialMatch[];
}

const MatchResultTable: React.FC<Props> = ({ trials }) => {
  if (!trials || trials.length === 0) {
    return <p className="text-xs text-slate-400">No matching trials found for this run.</p>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-800/80 bg-surface">
      <table className="min-w-full text-xs">
        <thead className="bg-slate-900/60 text-slate-400">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Score</th>
            <th className="px-3 py-2 text-left font-medium">NCT ID</th>
            <th className="px-3 py-2 text-left font-medium">Title</th>
          </tr>
        </thead>
        <tbody>
          {trials.map((t) => (
            <tr key={t.nct_id} className="border-t border-slate-800/70">
              <td className="px-3 py-2 text-xs text-slate-100">{t.score.toFixed(0)}%</td>
              <td className="px-3 py-2 text-xs font-mono text-slate-300">{t.nct_id}</td>
              <td className="px-3 py-2 text-xs text-slate-100">{t.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MatchResultTable;

