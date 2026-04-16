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
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-xs">
        <thead className="bg-slate-50 text-slate-500">
          <tr>
            <th className="px-4 py-3 text-left font-medium">Score</th>
            <th className="px-4 py-3 text-left font-medium">NCT ID</th>
            <th className="px-4 py-3 text-left font-medium">Title</th>
          </tr>
        </thead>
        <tbody>
          {trials.map((t) => (
            <tr
              key={t.nct_id}
              className="border-t border-slate-200 align-top transition-colors hover:bg-slate-50/70"
            >
              <td className="px-4 py-3">
                <span className="inline-flex min-w-[3.5rem] items-center justify-center rounded-full bg-slate-100 px-2.5 py-1 text-[0.68rem] font-semibold tabular-nums text-slate-700">
                  {t.score.toFixed(0)}%
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-[0.7rem] text-slate-500">{t.nct_id}</td>
              <td className="px-4 py-3 text-slate-800">{t.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MatchResultTable;

