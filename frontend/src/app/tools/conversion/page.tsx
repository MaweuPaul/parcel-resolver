"use client";

import { useRef, useState } from "react";
import { ArrowLeftRight, UploadCloud } from "lucide-react";

import { recordAnalysisCompleted } from "@/lib/analytics";

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
            [10, 0],
            [20, 0],
            [20, 10],
            [10, 10],
            [10, 0],
          ],
        ],
      },
    },
  ],
};

export default function ConversionPage() {
  const [geojsonText, setGeojsonText] = useState("");
  const [crs, setCrs] = useState("");
  const [status, setStatus] = useState<string | null>(null);
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
    setStatus(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setStatus(null);

    let featureCollection: unknown;
    try {
      featureCollection = JSON.parse(geojsonText);
    } catch {
      setError("That isn't valid JSON. Check for a missing bracket or comma.");
      return;
    }

    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (crs.trim()) params.set("crs", crs.trim());
      const query = params.toString();

      const response = await fetch(`${API_URL}/convert${query ? `?${query}` : ""}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(featureCollection),
      });

      if (!response.ok) {
        const body = await response.json();
        setError(body.detail ?? "The conversion tool rejected this GeoJSON.");
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "parcels.zip";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      setStatus("parcels.zip downloaded — a zipped Shapefile (.shp/.shx/.dbf).");
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
          <ArrowLeftRight aria-hidden="true" className="size-5" />
        </span>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#17211F]">
            Format conversion
          </h1>
          <p className="text-sm text-[#17211F]/60">
            Paste or upload a GeoJSON FeatureCollection and download it as a
            zipped ESRI Shapefile.
          </p>
        </div>
      </header>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-2xl border border-black/10 bg-white p-5 shadow-sm"
      >
        <div className="flex flex-col gap-1.5 sm:max-w-xs">
          <label htmlFor="crs" className="text-sm font-medium text-[#17211F]">
            CRS for .prj <span className="font-normal text-[#17211F]/50">(optional)</span>
          </label>
          <input
            id="crs"
            value={crs}
            onChange={(event) => setCrs(event.target.value)}
            placeholder="EPSG:4326"
            className="rounded-xl border border-black/10 bg-[#F6F6F1] px-3 py-2 text-sm text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
          />
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
          className="h-64 w-full rounded-xl border border-black/10 bg-[#F6F6F1] p-3 font-mono text-xs leading-relaxed text-[#17211F] outline-none focus-visible:border-[#D3A62C] focus-visible:ring-2 focus-visible:ring-[#D3A62C]/40"
        />

        <div className="flex items-center justify-between">
          {error ? (
            <p className="text-sm text-red-600">{error}</p>
          ) : status ? (
            <p className="text-sm text-emerald-700">{status}</p>
          ) : (
            <span />
          )}
          <button
            type="submit"
            disabled={isLoading || geojsonText.trim().length === 0}
            className="rounded-xl bg-[#D3A62C] px-5 py-2.5 text-sm font-semibold text-[#17211F] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLoading ? "Converting..." : "Convert to Shapefile"}
          </button>
        </div>
      </form>
    </div>
  );
}
