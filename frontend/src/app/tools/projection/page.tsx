"use client";

import { useRef, useState } from "react";
import { Boxes, UploadCloud } from "lucide-react";

import { recordAnalysisCompleted } from "@/lib/analytics";

type ProjectedParcel = {
  parcel_id: string;
  coordinates: [number, number][];
};

type ProjectResponse = {
  source_crs: string;
  target_crs: string;
  parcels: ProjectedParcel[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const COMMON_CRS = [
  { value: "EPSG:4326", label: "EPSG:4326 — WGS84 (lat/lon)" },
  { value: "EPSG:3857", label: "EPSG:3857 — Web Mercator" },
  { value: "EPSG:2263", label: "EPSG:2263 — NY State Plane (ft)" },
  { value: "EPSG:27700", label: "EPSG:27700 — British National Grid" },
];

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
            [-122.4194, 37.7749],
            [-122.4184, 37.7749],
            [-122.4184, 37.7759],
            [-122.4194, 37.7759],
            [-122.4194, 37.7749],
          ],
        ],
      },
    },
  ],
};

export default function ProjectionPage() {
  const [geojsonText, setGeojsonText] = useState("");
  const [sourceCrs, setSourceCrs] = useState("EPSG:4326");
  const [targetCrs, setTargetCrs] = useState("EPSG:3857");
  const [results, setResults] = useState<ProjectResponse | null>(null);
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
    setSourceCrs("EPSG:4326");
    setTargetCrs("EPSG:3857");
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

    if (!sourceCrs.trim() || !targetCrs.trim()) {
      setError("Both a source and target CRS are required.");
      return;
    }

    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        source_crs: sourceCrs.trim(),
        target_crs: targetCrs.trim(),
      });
      const response = await fetch(`${API_URL}/project?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(featureCollection),
      });

      const body = await response.json();

      if (!response.ok) {
        setError(body.detail ?? "The projection tool rejected this request.");
        return;
      }

      setResults(body as ProjectResponse);
      recordAnalysisCompleted();
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
          <Boxes aria-hidden="true" className="size-5" />
        </span>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#17211F]">
            Coordinate projection
          </h1>
          <p className="text-sm text-[#17211F]/60">
            Reproject a GeoJSON FeatureCollection&apos;s coordinates from one
            coordinate reference system into another.
          </p>
        </div>
      </header>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-2xl border border-black/10 bg-white p-5 shadow-sm"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="source-crs"
              className="text-sm font-medium text-[#17211F]"
            >
              Source CRS
            </label>
            <input
              id="source-crs"
              list="crs-presets"
              value={sourceCrs}
              onChange={(event) => setSourceCrs(event.target.value)}
              placeholder="EPSG:4326"
              className="rounded-xl border border-black/10 bg-[#F6F6F1] px-3 py-2 text-sm text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="target-crs"
              className="text-sm font-medium text-[#17211F]"
            >
              Target CRS
            </label>
            <input
              id="target-crs"
              list="crs-presets"
              value={targetCrs}
              onChange={(event) => setTargetCrs(event.target.value)}
              placeholder="EPSG:3857"
              className="rounded-xl border border-black/10 bg-[#F6F6F1] px-3 py-2 text-sm text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
            />
          </div>
          <datalist id="crs-presets">
            {COMMON_CRS.map((crs) => (
              <option key={crs.value} value={crs.value}>
                {crs.label}
              </option>
            ))}
          </datalist>
        </div>

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
          className="h-56 w-full rounded-xl border border-black/10 bg-[#F6F6F1] p-3 font-mono text-xs leading-relaxed text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
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
            {isLoading ? "Reprojecting..." : "Reproject parcels"}
          </button>
        </div>
      </form>

      {results && (
        <section className="flex flex-col gap-4 rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-[#17211F]">
            {results.parcels.length} parcel
            {results.parcels.length === 1 ? "" : "s"} reprojected from{" "}
            <span className="font-mono">{results.source_crs}</span> to{" "}
            <span className="font-mono">{results.target_crs}</span>
          </h2>

          <div className="flex flex-col gap-3">
            {results.parcels.map((parcel) => (
              <div
                key={parcel.parcel_id}
                className="rounded-xl border border-black/10 bg-[#F6F6F1] p-3"
              >
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-[#17211F]/50">
                  {parcel.parcel_id}
                </p>
                <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-relaxed text-[#17211F]">
                  {JSON.stringify(parcel.coordinates)}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
