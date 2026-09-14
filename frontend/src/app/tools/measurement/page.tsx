"use client";

import { useRef, useState } from "react";
import { Ruler, UploadCloud } from "lucide-react";

import { recordAnalysisCompleted } from "@/lib/analytics";

type ParcelMeasurement = {
  parcel_id: string;
  area: number;
  perimeter: number;
};

type MeasureResponse = {
  parcels: ParcelMeasurement[];
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
  ],
};

export default function MeasurementPage() {
  const [geojsonText, setGeojsonText] = useState("");
  const [results, setResults] = useState<ParcelMeasurement[] | null>(null);
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
      const response = await fetch(`${API_URL}/measure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(featureCollection),
      });

      const body = await response.json();

      if (!response.ok) {
        setError(body.detail ?? "The measurement tool rejected this GeoJSON.");
        return;
      }

      setResults((body as MeasureResponse).parcels);
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
          <Ruler aria-hidden="true" className="size-5" />
        </span>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#17211F]">
            Area and distance
          </h1>
          <p className="text-sm text-[#17211F]/60">
            Paste or upload a GeoJSON FeatureCollection to measure each
            parcel&apos;s area and boundary perimeter.
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
            {isLoading ? "Measuring..." : "Measure parcels"}
          </button>
        </div>
      </form>

      {results && (
        <section className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-[#17211F]">
            {results.length} parcel{results.length === 1 ? "" : "s"} measured
          </h2>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-black/10 text-xs uppercase tracking-wide text-[#17211F]/50">
                  <th className="py-2 pr-4 font-medium">Parcel</th>
                  <th className="py-2 pr-4 font-medium">Area</th>
                  <th className="py-2 pr-4 font-medium">Perimeter</th>
                </tr>
              </thead>
              <tbody>
                {results.map((parcel) => (
                  <tr
                    key={parcel.parcel_id}
                    className="border-b border-black/5 last:border-0"
                  >
                    <td className="py-2.5 pr-4 font-medium">{parcel.parcel_id}</td>
                    <td className="py-2.5 pr-4 text-[#17211F]/70">
                      {parcel.area.toLocaleString()}
                    </td>
                    <td className="py-2.5 pr-4 text-[#17211F]/70">
                      {parcel.perimeter.toLocaleString()}
                    </td>
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
