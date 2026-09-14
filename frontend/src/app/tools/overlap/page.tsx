"use client";

import { useRef, useState } from "react";
import { ScanSearch, UploadCloud } from "lucide-react";

type OverlapResult = {
  parcel_a: string;
  parcel_b: string;
  overlap_area: number;
  overlap_percentage: number;
  severity: "none" | "tolerance" | "dispute" | string;
};

type ResolveResponse = {
  overlaps: OverlapResult[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const SAMPLE_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { parcelid: "P001" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10],
            [0, 0],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: { parcelid: "P002" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [8, 8],
            [18, 8],
            [18, 18],
            [8, 18],
            [8, 8],
          ],
        ],
      },
    },
  ],
};

const severityStyles: Record<string, string> = {
  dispute: "bg-red-100 text-red-700",
  tolerance: "bg-amber-100 text-amber-800",
  none: "bg-emerald-100 text-emerald-700",
};

export default function OverlapPage() {
  const [geojsonText, setGeojsonText] = useState("");
  const [results, setResults] = useState<OverlapResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setGeojsonText(text);
    event.target.value = "";
  }

  function loadSample() {
    setGeojsonText(JSON.stringify(SAMPLE_FEATURE_COLLECTION, null, 2));
    setError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setResults(null);

    let featureCollection: unknown;
    try {
      featureCollection = JSON.parse(geojsonText);
    } catch {
      setError("That isn't valid JSON. Check for a missing bracket or comma.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(featureCollection),
      });

      const body = await response.json();

      if (!response.ok) {
        setError(body.detail ?? "The resolver rejected this GeoJSON.");
        return;
      }

      setResults((body as ResolveResponse).overlaps);
    } catch {
      setError(
        `Couldn't reach the resolver API at ${API_URL}. Is the backend running?`,
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header className="flex items-center gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#0A332E] text-[#D3A62C]">
          <ScanSearch aria-hidden="true" className="size-5" />
        </span>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#17211F]">
            Parcel overlap detection
          </h1>
          <p className="text-sm text-[#17211F]/60">
            Paste or upload a GeoJSON FeatureCollection to find overlapping
            parcel boundaries and their severity.
          </p>
        </div>
      </header>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-2xl border border-black/10 bg-white p-5 shadow-sm"
      >
        <div className="flex items-center justify-between gap-3">
          <label htmlFor="geojson" className="text-sm font-medium text-[#17211F]">
            GeoJSON FeatureCollection
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadSample}
              className="rounded-lg px-3 py-1.5 text-xs font-semibold text-[#0A332E] hover:bg-[#0A332E]/5"
            >
              Load sample
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 rounded-lg border border-black/10 px-3 py-1.5 text-xs font-semibold text-[#17211F] hover:bg-black/5"
            >
              <UploadCloud aria-hidden="true" className="size-3.5" />
              Upload file
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.geojson,application/json"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>

        <textarea
          id="geojson"
          value={geojsonText}
          onChange={(event) => setGeojsonText(event.target.value)}
          placeholder='{"type": "FeatureCollection", "features": [...]}'
          spellCheck={false}
          className="h-64 w-full rounded-xl border border-black/10 bg-[#F6F6F1] p-3 font-mono text-xs leading-relaxed text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
        />

        <div className="flex items-center justify-between">
          {error ? (
            <p className="text-sm text-red-600">{error}</p>
          ) : (
            <span />
          )}
          <button
            type="submit"
            disabled={isLoading || geojsonText.trim().length === 0}
            className="rounded-xl bg-[#D3A62C] px-5 py-2.5 text-sm font-semibold text-[#17211F] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLoading ? "Checking..." : "Check for overlaps"}
          </button>
        </div>
      </form>

      {results && (
        <section className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-[#17211F]">
            {results.length === 0
              ? "No overlaps found"
              : `${results.length} overlap${results.length === 1 ? "" : "s"} found`}
          </h2>

          {results.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-black/10 text-xs uppercase tracking-wide text-[#17211F]/50">
                    <th className="py-2 pr-4 font-medium">Parcel A</th>
                    <th className="py-2 pr-4 font-medium">Parcel B</th>
                    <th className="py-2 pr-4 font-medium">Overlap area</th>
                    <th className="py-2 pr-4 font-medium">Overlap %</th>
                    <th className="py-2 pr-4 font-medium">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((overlap) => (
                    <tr
                      key={`${overlap.parcel_a}-${overlap.parcel_b}`}
                      className="border-b border-black/5 last:border-0"
                    >
                      <td className="py-2.5 pr-4 font-medium">{overlap.parcel_a}</td>
                      <td className="py-2.5 pr-4 font-medium">{overlap.parcel_b}</td>
                      <td className="py-2.5 pr-4 text-[#17211F]/70">
                        {overlap.overlap_area.toLocaleString()}
                      </td>
                      <td className="py-2.5 pr-4 text-[#17211F]/70">
                        {overlap.overlap_percentage.toFixed(2)}%
                      </td>
                      <td className="py-2.5 pr-4">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                            severityStyles[overlap.severity] ??
                            "bg-zinc-100 text-zinc-700"
                          }`}
                        >
                          {overlap.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
