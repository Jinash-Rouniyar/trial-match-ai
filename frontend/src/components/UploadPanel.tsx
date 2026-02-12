import React, { useState } from "react";
import { uploadPatient } from "../api/client";

interface Props {
  onUploaded?: () => void;
}

const UploadPanel: React.FC<Props> = ({ onUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please choose a JSON file first.");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const text = await file.text();
      const json = JSON.parse(text);
      await uploadPatient(json);
      if (onUploaded) onUploaded();
    } catch (e) {
      setError("Failed to upload or parse JSON file.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-medium text-slate-900">Upload patient JSON</h2>
          <p className="text-xs text-slate-600">
            Synthea-style JSON file. We’ll parse conditions, medications, and narrative.
          </p>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <input
          type="file"
          accept="application/json"
          onChange={handleFileChange}
          className="block w-full text-xs text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-black"
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60 disabled:hover:bg-white"
        >
          {loading ? "Uploading…" : "Upload"}
        </button>
      </div>
      {error && <p className="text-xs text-rose-500">{error}</p>}
    </section>
  );
};

export default UploadPanel;

