import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  BarChart3,
  BookOpenText,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  CloudSun,
  Download,
  ExternalLink,
  Factory,
  Gauge,
  Leaf,
  LoaderCircle,
  Map,
  MapPin,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  TableProperties,
  X,
} from "lucide-react";
import { api, downloadCsv } from "./services/api";
import { RegionCard } from "./components/RegionCard";
import type { ComparisonSummary, IntensityPeriod, RegionSnapshot } from "./types";
import { formatLocalTime, formatNumber, londonDateToUtc, todayInLondon } from "./utils/format";

const IntensityChart = lazy(() => import("./components/IntensityChart").then((module) => ({ default: module.IntensityChart })));
const GenerationMixChart = lazy(() => import("./components/ChartWidgets").then((module) => ({ default: module.GenerationMixChart })));
const RegionalComparisonChart = lazy(() => import("./components/ChartWidgets").then((module) => ({ default: module.RegionalComparisonChart })));

type Page = "overview" | "regions" | "history" | "compare" | "api";
const pageLabels: Record<Page, string> = {
  overview: "Overview",
  regions: "Regional explorer",
  history: "Historical data",
  compare: "Compare regions",
  api: "API reference",
};
const navItems: Array<{ id: Page; icon: typeof Activity }> = [
  { id: "overview", icon: Gauge },
  { id: "regions", icon: Map },
  { id: "history", icon: BarChart3 },
  { id: "compare", icon: TableProperties },
  { id: "api", icon: BookOpenText },
];

const toUtcIso = (date: Date) => date.toISOString().replace(".000Z", "Z");
const shiftDate = (value: string, days: number) => {
  const [year, month, day] = value.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, month - 1, day + days));
  return [shifted.getUTCFullYear(), String(shifted.getUTCMonth() + 1).padStart(2, "0"), String(shifted.getUTCDate()).padStart(2, "0")].join("-");
};

function classificationTone(value: string | null | undefined) {
  if (value === "very low" || value === "low") return "tone-green";
  if (value === "moderate") return "tone-amber";
  if (value === "high" || value === "very high") return "tone-red";
  return "tone-neutral";
}

function ClassificationPill({ value }: { value: string | null | undefined }) {
  return <span className={`classification-pill ${classificationTone(value)}`}>{value ?? "Unclassified"}</span>;
}

function App() {
  const [page, setPage] = useState<Page>("overview");
  const [navOpen, setNavOpen] = useState(false);
  const [current, setCurrent] = useState<IntensityPeriod | null>(null);
  const [forecast, setForecast] = useState<IntensityPeriod[]>([]);
  const [history, setHistory] = useState<IntensityPeriod[]>([]);
  const [regions, setRegions] = useState<RegionSnapshot[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState(18);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [retrievedAt, setRetrievedAt] = useState<string | null>(null);

  const loadOverview = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setLoadError(null);
    const now = new Date();
    const requests = await Promise.all([
      api.current().then((value) => ({ ok: true as const, value }), (error: unknown) => ({ ok: false as const, error })),
      api.forecast(24).then((value) => ({ ok: true as const, value }), (error: unknown) => ({ ok: false as const, error })),
      api.regions().then((value) => ({ ok: true as const, value }), (error: unknown) => ({ ok: false as const, error })),
      api.history(toUtcIso(new Date(now.getTime() - 24 * 60 * 60 * 1000)), toUtcIso(now))
        .then((value) => ({ ok: true as const, value }), (error: unknown) => ({ ok: false as const, error })),
    ]);
    let successes = 0;
    const errors: string[] = [];
    const recordError = (error: unknown) => errors.push(error instanceof Error ? error.message : "A data request failed.");
    const [currentResult, forecastResult, regionResult, historyResult] = requests;
    if (currentResult.ok) {
      successes += 1;
      setCurrent(currentResult.value.data[0] ?? null);
      setRetrievedAt(currentResult.value.metadata?.retrieved_at ?? null);
    } else recordError(currentResult.error);
    if (forecastResult.ok) {
      successes += 1;
      setForecast(forecastResult.value.data);
      setRetrievedAt(forecastResult.value.metadata?.retrieved_at ?? null);
    } else recordError(forecastResult.error);
    if (regionResult.ok) {
      successes += 1;
      setRegions(regionResult.value.data);
      setRetrievedAt(regionResult.value.metadata?.retrieved_at ?? null);
    } else recordError(regionResult.error);
    if (historyResult.ok) {
      successes += 1;
      setHistory(historyResult.value.data);
      setRetrievedAt(historyResult.value.metadata?.retrieved_at ?? null);
    } else recordError(historyResult.error);
    if (successes === 0) setLoadError(errors[0] ?? "Data could not be loaded.");
    else if (errors.length) setLoadError(`${errors.length} data view${errors.length === 1 ? "" : "s"} could not be refreshed. Some information may be missing.`);
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  const selectedRegion = useMemo(() => regions.find((region) => region.id === selectedRegionId) ?? null, [regions, selectedRegionId]);
  const nationalRegion = regions.find((region) => region.id === 18) ?? null;
  const nextForecast = forecast.find((period) => Date.parse(period.from) >= Date.now() - 60_000 && period.forecast != null) ?? forecast.find((period) => period.forecast != null) ?? null;

  const openRegion = (regionId: number) => {
    setSelectedRegionId(regionId);
    setPage("regions");
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${navOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><Leaf size={19} strokeWidth={2.3} /></div>
          <div><strong>Carbon intelligence</strong><span>GREAT BRITAIN · LIVE DATA</span></div>
          <button aria-label="Close navigation" className="mobile-close" onClick={() => setNavOpen(false)}><X size={19} /></button>
        </div>
        <div className="nav-section-label">WORKSPACE</div>
        <nav className="primary-nav" aria-label="Main navigation">
          {navItems.map(({ id, icon: Icon }) => (
            <button key={id} className={`nav-item ${page === id ? "nav-active" : ""}`} onClick={() => { setPage(id); setNavOpen(false); }}>
              <Icon size={18} strokeWidth={1.9} /><span>{pageLabels[id]}</span>{page === id && <span className="nav-active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="coverage-card">
            <div className="coverage-icon"><ShieldCheck size={16} /></div>
            <div><strong>Verified source</strong><span>NESO Carbon Intensity API</span></div>
            <Check size={15} className="coverage-check" />
          </div>
          <p className="coverage-note">Independent data platform. Coverage includes England, Scotland and Wales. Northern Ireland is not covered.</p>
          <div className="sidebar-footer">UK CARBON INTELLIGENCE <span>v0.1</span></div>
        </div>
      </aside>
      {navOpen && <button className="mobile-scrim" aria-label="Close navigation overlay" onClick={() => setNavOpen(false)} />}

      <main className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu" aria-label="Open navigation" onClick={() => setNavOpen(true)}><Menu size={20} /></button>
            <div className="breadcrumbs"><span>Data platform</span><span className="crumb-divider">/</span><strong>{pageLabels[page]}</strong></div>
          </div>
          <div className="topbar-right">
            <div className="live-indicator"><span />LIVE FEED</div>
            <span className="topbar-separator" />
            <span className="updated-label">Updated {retrievedAt ? formatLocalTime(retrievedAt, { hour: "2-digit", minute: "2-digit" }) : "—"}</span>
            <button className="refresh-button" onClick={() => void loadOverview(true)} disabled={refreshing} aria-label="Refresh data">
              <RefreshCw size={15} className={refreshing ? "spin" : ""} /><span>Refresh</span>
            </button>
          </div>
        </header>

        <div className="content-wrap">
          {loadError && <div className={`notice ${current || regions.length ? "notice-warn" : "notice-error"}`} role="alert"><CircleHelp size={17} /><span>{loadError}</span>{!current && <button onClick={() => void loadOverview(true)}>Retry</button>}</div>}
          {loading && !current && !regions.length ? <LoadingState /> : (
            <>
              {page === "overview" && <OverviewPage current={current} forecast={forecast} history={history} regions={regions} nextForecast={nextForecast} onRegion={openRegion} />}
              {page === "regions" && <RegionsPage regions={regions} selected={selectedRegion} gb={nationalRegion} selectedId={selectedRegionId} onSelect={setSelectedRegionId} />}
              {page === "history" && <HistoryPage regions={regions} />}
              {page === "compare" && <ComparePage regions={regions} />}
              {page === "api" && <ApiPage />}
            </>
          )}
          <footer className="page-footer">
            <span>Data source: <a href="https://carbonintensity.org.uk/" target="_blank" rel="noreferrer">National Energy System Operator (NESO)</a></span>
            <span>Independent project · Data licensed under CC BY 4.0 · Times shown in Europe/London</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function LoadingState() {
  return <div className="loading-state" role="status"><LoaderCircle className="spin" size={24} /><span>Connecting to the carbon intensity feed…</span></div>;
}

function PageHeading({ eyebrow, title, detail, action }: { eyebrow: string; title: string; detail: string; action?: ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{detail}</p></div>{action}</div>;
}

function OverviewPage({ current, forecast, history, regions, nextForecast, onRegion }: {
  current: IntensityPeriod | null;
  forecast: IntensityPeriod[];
  history: IntensityPeriod[];
  regions: RegionSnapshot[];
  nextForecast: IntensityPeriod | null;
  onRegion: (id: number) => void;
}) {
  const mainValue = current?.actual ?? current?.forecast ?? null;
  const currentKind = current?.actual != null ? "Estimated actual" : current?.forecast != null ? "Current-period forecast" : "No current value";
  const index = current?.actual != null ? current.actual_classification : current?.forecast_classification;
  const lastActual = [...history].reverse().find((item) => item.actual != null && item.from !== current?.from);
  const delta = current?.actual != null && lastActual?.actual != null ? current.actual - lastActual.actual : null;
  const gbMix = regions.find((region) => region.id === 18)?.current?.generation_mix ?? [];
  const lowRegions = regions.filter((item) => item.current && ["very low", "low"].includes(item.current.forecast_classification ?? "")).length;

  return (
    <>
      <PageHeading eyebrow="SYSTEM OVERVIEW · GREAT BRITAIN" title="Electricity, in context." detail="A live view of the carbon intensity behind the grid—updated every settlement period." action={<span className="scope-chip"><MapPin size={14} />Great Britain</span>} />
      <section className="hero-grid">
        <article className="hero-card">
          <div className="hero-card-top"><div><div className="card-eyebrow"><span className="pulse-dot" />CURRENT GB INTENSITY</div><p className="hero-caption">Carbon dioxide equivalent per unit of electricity</p></div><div className="hero-icon"><Activity size={20} /></div></div>
          <div className="hero-measure"><strong>{formatNumber(mainValue)}</strong><span>gCO₂<small>/kWh</small></span></div>
          <div className="hero-bottom"><div><ClassificationPill value={index} /><span className="hero-kind">{currentKind}{delta != null ? ` · ${delta > 0 ? "+" : ""}${formatNumber(delta)} vs prior actual` : ""}</span></div><span className="hero-period"><Clock3 size={13} />{current ? `${formatLocalTime(current.from)} – ${formatLocalTime(current.to, { hour: "2-digit", minute: "2-digit" })}` : "Waiting for data"}</span></div>
          <div className="hero-sparkline"><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /><div /></div>
        </article>
        <article className="summary-card">
          <div className="summary-card-heading"><div className="summary-icon"><CloudSun size={18} /></div><div><div className="card-eyebrow">UP NEXT</div><span className="small-muted">Next half-hour period</span></div></div>
          {nextForecast ? <><div className="summary-value">{formatNumber(nextForecast.forecast)} <span>gCO₂/kWh</span></div><div className="summary-class"><ClassificationPill value={nextForecast.forecast_classification} /><span>{formatLocalTime(nextForecast.from)}</span></div><div className="summary-divider" /><div className="summary-foot"><span>Forecast value</span><span>NESO · 30 min</span></div></> : <EmptyInline label="No forecast returned." />}
        </article>
        <article className="summary-card summary-clean-card">
          <div className="summary-card-heading"><div className="summary-icon clean-icon"><Leaf size={18} /></div><div><div className="card-eyebrow">REGIONAL SNAPSHOT</div><span className="small-muted">Current regional forecasts</span></div></div>
          <div className="summary-value">{regions.length ? `${lowRegions} / ${regions.filter((item) => item.available).length}` : "—"}<span>regions currently low or very low</span></div>
          <div className="mini-region-bars">{regions.filter((r) => r.type === "dno").slice(0, 14).map((region) => <div key={region.id} title={`${region.name}: ${region.current?.forecast ?? "no data"} gCO₂/kWh`} style={{ height: `${Math.max(18, Math.min(100, (region.current?.forecast ?? 0) / 3.5))}%` }} className={region.current && region.current.forecast_classification && ["low", "very low"].includes(region.current.forecast_classification) ? "bar-clean" : "bar-carbon"} />)}</div>
          <div className="summary-foot"><span>14 DNO regions</span><button className="text-link" onClick={() => onRegion(18)}>Explore regions <ArrowRight size={13} /></button></div>
        </article>
      </section>

      <section className="panel chart-panel">
        <div className="panel-heading"><div><div className="section-title">Grid intensity over time</div><p>Actual estimates and forecasts are shown separately. Half-hour settlement periods.</p></div><div className="period-note"><span className="chart-legend-dot actual-dot" />Estimated actual <span className="chart-legend-dot forecast-dot" />Forecast</div></div>
        <Suspense fallback={<ChartFallback height={310} />}>
          <IntensityChart data={[...history, ...forecast.filter((item) => Date.parse(item.from) > Date.now())]} height={310} showLegend={false} />
        </Suspense>
        <div className="chart-axis-foot"><span>Past 24 hours</span><span>Next 24 hours</span></div>
      </section>

      <section className="bottom-grid">
        <div className="panel region-panel">
          <div className="panel-heading"><div><div className="section-title">Regional outlook</div><p>Provider-reported forecasts by grid region</p></div><button className="icon-text-button" onClick={() => onRegion(18)}>View all <ArrowRight size={14} /></button></div>
          <div className="region-card-grid">{regions.filter((region) => region.type === "dno").slice(0, 6).map((region) => <RegionCard key={region.id} region={region} onSelect={onRegion} />)}</div>
        </div>
        <div className="panel mix-panel">
          <div className="panel-heading"><div><div className="section-title">GB generation mix</div><p>Provider-reported share by fuel type</p></div><div className="mix-badge"><Factory size={14} />NESO</div></div>
          {gbMix.length ? <Suspense fallback={<ChartFallback height={160} />}><GenerationMixChart data={gbMix} periodStart={regions.find((item) => item.id === 18)?.current?.from} /></Suspense> : <EmptyInline label="Generation mix is not currently available." />}
          <div className="mix-note"><CircleHelp size={13} />Share of estimated regional consumption mix; not generation volume.</div>
        </div>
      </section>
      <div className="methodology-strip"><div className="methodology-mark"><ShieldCheck size={18} /></div><div><strong>Understand the numbers</strong><span>Intensity is reported in gCO₂/kWh. The actual value is an estimate; regional values represent grid regions, not individual properties.</span></div><a href="https://carbon-intensity.github.io/api-definitions/" target="_blank" rel="noreferrer">Source methodology <ExternalLink size={13} /></a></div>
    </>
  );
}

function RegionsPage({ regions, selected, gb, selectedId, onSelect }: {
  regions: RegionSnapshot[];
  selected: RegionSnapshot | null;
  gb: RegionSnapshot | null;
  selectedId: number;
  onSelect: (id: number) => void;
}) {
  const [series, setSeries] = useState<IntensityPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [postcode, setPostcode] = useState("");
  const [postcodeResult, setPostcodeResult] = useState<IntensityPeriod[] | null>(null);
  const [postcodeError, setPostcodeError] = useState<string | null>(null);
  const [postcodeLoading, setPostcodeLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    const end = new Date();
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
    setLoading(true);
    setError(null);
    api.regionHistory(selectedId, toUtcIso(start), toUtcIso(end))
      .then((result) => { if (alive) setSeries(result.data); })
      .catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : "Regional history could not be loaded."); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [selectedId]);

  const selectedValue = selected?.current?.forecast;
  const gbValue = gb?.current?.forecast;
  const difference = selectedValue != null && gbValue != null ? selectedValue - gbValue : null;
  const dnoRegions = regions.filter((region) => region.type === "dno");
  const countryRegions = regions.filter((region) => region.type === "country");

  const lookupPostcode = async (event: FormEvent) => {
    event.preventDefault();
    setPostcodeLoading(true);
    setPostcodeError(null);
    setPostcodeResult(null);
    try {
      const result = await api.postcode(postcode);
      setPostcodeResult(result.data);
      if (!result.data.length) setPostcodeError("The provider returned no regional periods for this postcode.");
    } catch (reason) {
      setPostcodeError(reason instanceof Error ? reason.message : "Postcode lookup failed.");
    } finally {
      setPostcodeLoading(false);
    }
  };

  return (
    <>
      <PageHeading eyebrow="GEOGRAPHIC EXPLORER" title="The grid, region by region." detail="Compare provider-reported intensity across Great Britain's distribution regions and country aggregates." />
      <section className="region-explorer-grid">
        <div className="panel region-selector-panel">
          <div className="panel-heading"><div><div className="section-title">Choose a region</div><p>14 DNO areas and 3 country aggregates</p></div><span className="selection-count">{regions.filter((r) => r.available).length} online</span></div>
          <div className="region-card-grid region-full-grid">{dnoRegions.map((region) => <RegionCard key={region.id} region={region} onSelect={onSelect} />)}</div>
          <div className="aggregate-heading"><span>COUNTRY AGGREGATES</span></div>
          <div className="region-card-grid region-country-grid">{countryRegions.map((region) => <RegionCard key={region.id} region={region} onSelect={onSelect} />)}{gb && <RegionCard region={gb} onSelect={onSelect} />}</div>
        </div>
        <div className="region-detail-column">
          <div className="panel region-detail-panel">
            <label className="field-label" htmlFor="region-select">SELECTED AREA</label>
            <div className="select-wrap"><select id="region-select" value={selectedId} onChange={(event) => onSelect(Number(event.target.value))}>{regions.map((region) => <option key={region.id} value={region.id}>{region.name}{region.available ? "" : " · no data"}</option>)}</select><ChevronDown size={16} /></div>
            {selected ? <><div className="region-big-value">{formatNumber(selected.current?.forecast)}<small>gCO₂/kWh</small></div><div className="region-detail-meta"><ClassificationPill value={selected.current?.forecast_classification} /><span>{selected.current ? `Forecast · ${formatLocalTime(selected.current.from)}` : "Current data unavailable"}</span></div><div className="region-vs-gb"><div><span>GB provider value</span><strong>{formatNumber(gbValue)} <small>gCO₂/kWh</small></strong></div><div className={difference != null && difference <= 0 ? "diff-good" : "diff-high"}><span>Difference to GB</span><strong>{difference == null ? "—" : `${difference > 0 ? "+" : ""}${formatNumber(difference)}`} <small>gCO₂/kWh</small></strong></div></div></> : <EmptyInline label="Choose a region to inspect its latest forecast." />}
          </div>
          <div className="panel region-history-panel"><div className="panel-heading"><div><div className="section-title">Regional trend</div><p>Recent forecast periods · last 24 hours</p></div></div>{loading ? <LoadingInline /> : error ? <ErrorInline message={error} /> : <Suspense fallback={<ChartFallback height={228} />}><IntensityChart data={series} height={228} showLegend={false} /></Suspense>}</div>
        </div>
      </section>
      <section className="panel postcode-panel"><div><div className="postcode-icon"><Search size={18} /></div><div className="section-title">Find a region by postcode</div><p>Enter a UK postcode. The provider resolves it to a regional estimate, not a property-level reading.</p></div><form onSubmit={(event) => void lookupPostcode(event)} className="postcode-form"><label className="sr-only" htmlFor="postcode">Postcode</label><input id="postcode" value={postcode} onChange={(event) => setPostcode(event.target.value)} placeholder="e.g. EH1 1YZ" autoComplete="postal-code" required /><button className="primary-button" type="submit" disabled={postcodeLoading}>{postcodeLoading ? <LoaderCircle size={15} className="spin" /> : <Search size={15} />}Find region</button></form>
        {postcodeError && <p className="inline-error" role="alert">{postcodeError}</p>}
        {postcodeResult?.[0] && <div className="postcode-result"><div className="postcode-result-icon"><MapPin size={17} /></div><div><span>Resolved area · {postcodeResult[0].region_name}</span><strong>{formatNumber(postcodeResult[0].forecast)} <small>gCO₂/kWh forecast</small></strong></div><ClassificationPill value={postcodeResult[0].forecast_classification} /><span className="postcode-note">Regional estimate only</span></div>}
      </section>
      <div className="methodology-strip"><div className="methodology-mark"><CircleHelp size={18} /></div><div><strong>How regional comparisons work</strong><span>GB and country aggregates come directly from NESO. They are never calculated as an unweighted average of the DNO regions.</span></div></div>
    </>
  );
}

function HistoryPage({ regions }: { regions: RegionSnapshot[] }) {
  const today = todayInLondon();
  const [startDate, setStartDate] = useState(shiftDate(today, -6));
  const [endDate, setEndDate] = useState(today);
  const [regionId, setRegionId] = useState(18);
  const [data, setData] = useState<IntensityPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const fetchHistory = async (event?: FormEvent) => {
    event?.preventDefault();
    setError(null);
    setSubmitted(true);
    const start = londonDateToUtc(startDate);
    const end = londonDateToUtc(shiftDate(endDate, 1));
    if (!startDate || !endDate || Date.parse(startDate) > Date.parse(endDate)) {
      setError("Choose a start date that is on or before the end date.");
      return;
    }
    if (end.getTime() - start.getTime() > 14 * 24 * 60 * 60 * 1000) {
      setError("Choose a range of 14 days or less, matching the NESO national history limit.");
      return;
    }
    setLoading(true);
    try {
      const result = await api.history(toUtcIso(start), toUtcIso(end), regionId === 18 ? undefined : regionId);
      setData(result.data);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Historical data could not be loaded.");
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void fetchHistory(); /* initial last-seven-day request */ }, []);

  return (
    <>
      <PageHeading eyebrow="HISTORICAL EXPLORER" title="Read the pattern, not just the moment." detail="Explore half-hour observations, keep forecasts separate from estimated actuals, and export the records." />
      <form className="panel filter-panel" onSubmit={(event) => void fetchHistory(event)}>
        <div className="filter-title"><div className="filter-icon"><Clock3 size={17} /></div><div><strong>Choose a period</strong><span>Time range is selected in London local dates</span></div></div>
        <div className="filter-controls"><label><span>START DATE</span><input type="date" value={startDate} max={endDate || today} onChange={(event) => setStartDate(event.target.value)} /></label><label><span>END DATE</span><input type="date" value={endDate} min={startDate} max={today} onChange={(event) => setEndDate(event.target.value)} /></label><label className="region-filter"><span>REGION</span><select value={regionId} onChange={(event) => setRegionId(Number(event.target.value))}>{regions.map((region) => <option value={region.id} key={region.id}>{region.name}</option>)}</select></label><button className="primary-button" type="submit" disabled={loading}>{loading ? <LoaderCircle size={15} className="spin" /> : <Search size={15} />}Load data</button></div>
      </form>
      {error && <div className="notice notice-error" role="alert"><CircleHelp size={16} />{error}</div>}
      <section className="panel history-results-panel">
        <div className="panel-heading"><div><div className="section-title">{regions.find((region) => region.id === regionId)?.name ?? "Selected region"} intensity</div><p>gCO₂/kWh · half-hour periods · timestamps returned in UTC, displayed in London time</p></div><button type="button" className="secondary-button" onClick={() => downloadCsv(data, `carbon-intensity-region-${regionId}.csv`)} disabled={!data.length}><Download size={15} />Export CSV</button></div>
        {loading ? <div className="loading-slab"><LoaderCircle size={20} className="spin" />Fetching provider observations…</div> : <Suspense fallback={<ChartFallback height={350} />}><IntensityChart data={data} height={350} /></Suspense>}
        {submitted && !loading && !data.length && !error && <div className="empty-result">No records were returned for this period.</div>}
        <div className="history-summary"><SummaryChip label="Records" value={String(data.length)} /><SummaryChip label="Actual intervals" value={String(data.filter((item) => item.actual != null).length)} /><SummaryChip label="Forecast intervals" value={String(data.filter((item) => item.forecast != null).length)} /><div className="history-legend"><span><i className="legend-line solid-line" />Estimated actual</span><span><i className="legend-line dashed-line" />Forecast</span></div></div>
      </section>
      <div className="range-limit-note"><ShieldCheck size={16} /><span>History queries are capped at 14 days per request to match NESO's documented national range limit. Missing intervals remain missing; the chart does not fill gaps.</span></div>
    </>
  );
}

function SummaryChip({ label, value }: { label: string; value: string }) {
  return <div className="summary-chip"><span>{label}</span><strong>{value}</strong></div>;
}

function ComparePage({ regions }: { regions: RegionSnapshot[] }) {
  const [selectedIds, setSelectedIds] = useState<number[]>([3, 8, 16, 18]);
  const [comparison, setComparison] = useState<ComparisonSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(shiftDate(todayInLondon(), -1));
  const [endDate, setEndDate] = useState(todayInLondon());

  const compare = async (event?: FormEvent) => {
    event?.preventDefault();
    if (selectedIds.length < 2 || selectedIds.length > 6) {
      setError("Select between two and six regions.");
      return;
    }
    setLoading(true);
    setError(null);
    const start = londonDateToUtc(startDate);
    const end = londonDateToUtc(shiftDate(endDate, 1));
    if (end.getTime() - start.getTime() > 14 * 24 * 60 * 60 * 1000) {
      setError("Choose a comparison period of 14 days or less.");
      setLoading(false);
      return;
    }
    try {
      const result = await api.regionalComparison(selectedIds, toUtcIso(start), toUtcIso(end));
      setComparison(result.data);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Comparison could not be loaded.");
      setComparison([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { void compare(); /* initial comparison */ }, []);

  const toggleRegion = (id: number) => {
    setSelectedIds((previous) => previous.includes(id) ? previous.filter((item) => item !== id) : [...previous, id].slice(-6));
  };
  return (
    <>
      <PageHeading eyebrow="REGIONAL COMPARISON" title="Put places side by side." detail="Compare the provider's regional forecast series. National and country aggregates remain provider-reported values." />
      <form className="panel compare-controls" onSubmit={(event) => void compare(event)}>
        <div className="compare-controls-heading"><div><div className="section-title">Select regions</div><p>Choose 2 to 6 · aggregates are sourced directly from NESO</p></div><div className="selected-count">{selectedIds.length}<span>/ 6</span></div></div>
        <div className="compare-region-options">{regions.map((region) => <label key={region.id} className={`compare-region-option ${selectedIds.includes(region.id) ? "option-selected" : ""}`}><input type="checkbox" checked={selectedIds.includes(region.id)} onChange={() => toggleRegion(region.id)} /><span className="custom-check"><Check size={12} /></span><span>{region.name}</span><small>{region.type === "dno" ? "DNO" : region.type === "country" ? "Country" : "GB"}</small></label>)}</div>
        <div className="compare-bottom-controls"><label><span>FROM</span><input type="date" value={startDate} max={endDate} onChange={(event) => setStartDate(event.target.value)} /></label><label><span>TO</span><input type="date" value={endDate} min={startDate} max={todayInLondon()} onChange={(event) => setEndDate(event.target.value)} /></label><button className="primary-button" type="submit" disabled={loading}>{loading ? <LoaderCircle size={15} className="spin" /> : <BarChart3 size={15} />}Compare selected</button></div>
      </form>
      {error && <div className="notice notice-error" role="alert"><CircleHelp size={16} />{error}</div>}
      <section className="panel comparison-panel"><div className="panel-heading"><div><div className="section-title">Forecast range by region</div><p>Average, minimum and maximum of available provider forecast periods for the selected range.</p></div><div className="comparison-method"><ShieldCheck size={14} />Provider series</div></div>
        {loading ? <div className="loading-slab"><LoaderCircle size={20} className="spin" />Calculating regional summaries…</div> : comparison.length ? <><Suspense fallback={<ChartFallback height={250} />}><RegionalComparisonChart data={comparison} /></Suspense><div className="comparison-table-wrap"><table className="data-table"><thead><tr><th>REGION</th><th>CURRENT FORECAST</th><th>PERIOD AVERAGE</th><th>MIN / MAX</th><th>CHANGE IN RANGE</th></tr></thead><tbody>{comparison.map((item) => <tr key={item.region_id}><td><strong>{item.region_name}</strong><span className="table-sub">{item.count} available periods</span></td><td>{formatNumber(item.current_forecast)} <small>gCO₂/kWh</small></td><td>{formatNumber(item.average)} <small>gCO₂/kWh</small></td><td>{formatNumber(item.minimum)} / {formatNumber(item.maximum)}</td><td className={item.trend_change != null && item.trend_change < 0 ? "trend-down" : "trend-up"}>{item.trend_change == null ? "—" : `${item.trend_change > 0 ? "+" : ""}${formatNumber(item.trend_change)}`} <small>gCO₂/kWh</small></td></tr>)}</tbody></table></div><p className="method-note">The period change is last available forecast minus first available forecast. No unweighted regional or GB average is calculated.</p></> : <EmptyInline label="Select regions and compare to see their provider forecasts." />}
      </section>
      <div className="range-limit-note"><ArrowDownRight size={16} /><span>Regional statistics describe only provider observations returned for the selected range. A missing period does not mean zero intensity.</span></div>
    </>
  );
}

function ApiPage() {
  const endpoints = [
    ["GET", "/api/v1/carbon-intensity/current", "Latest GB interval with estimated actual, forecast and NESO index."],
    ["GET", "/api/v1/carbon-intensity/forecast?hours=24", "National forecast; use 24 or 48 hours."],
    ["GET", "/api/v1/carbon-intensity/history?start=…&end=…", "National time series; maximum 14 days per request."],
    ["GET", "/api/v1/regions", "Region catalogue and current regional forecasts."],
    ["GET", "/api/v1/regions/{id}/history", "Regional time series for a selected ID."],
    ["GET", "/api/v1/postcodes/{postcode}/carbon-intensity", "Resolves full or outward postcode to regional data."],
    ["GET", "/api/v1/statistics/summary", "Separate actual and forecast summary statistics."],
    ["GET", "/api/v1/statistics/regional-comparison", "Regional forecast range and trend comparison."],
    ["GET", "/api/v1/data-sources", "Provider, licence, attribution and geographic coverage."],
    ["GET", "/api/v1/collection/status", "Latest scheduled ingestion run."],
    ["GET", "/health · /ready · /api/v1/status", "Liveness, database readiness and application status."],
  ];
  return (
    <>
      <PageHeading eyebrow="DEVELOPER ACCESS" title="A clear API for grid signals." detail="The application API normalizes NESO source data while preserving geography, units, timestamps and forecast status." action={<a className="primary-button docs-link" href="/docs" target="_blank" rel="noreferrer"><BookOpenText size={15} />Open Swagger docs <ExternalLink size={13} /></a>} />
      <div className="api-top-cards"><div className="api-info-card"><div className="api-info-icon"><ShieldCheck size={18} /></div><div><span>BASE PATH</span><strong>/api/v1</strong><small>JSON · versioned REST</small></div></div><div className="api-info-card"><div className="api-info-icon"><Clock3 size={18} /></div><div><span>TIME HANDLING</span><strong>UTC in API</strong><small>Local display uses Europe/London</small></div></div><div className="api-info-card"><div className="api-info-icon"><MapPin size={18} /></div><div><span>GEOGRAPHIC SCOPE</span><strong>Great Britain</strong><small>England, Scotland and Wales</small></div></div></div>
      <section className="panel endpoint-panel"><div className="panel-heading"><div><div className="section-title">Endpoint reference</div><p>All responses include source and retrieval metadata where applicable.</p></div><a className="subtle-link" href="/openapi.json" target="_blank" rel="noreferrer">OpenAPI JSON <ExternalLink size={13} /></a></div><div className="endpoint-list">{endpoints.map(([method, path, description]) => <div className="endpoint-row" key={path}><span className="method-tag">{method}</span><code>{path}</code><span>{description}</span></div>)}</div></section>
      <section className="api-notes-grid"><div className="api-note"><div className="note-number">01</div><div><strong>Actual and forecast are distinct</strong><p>Actual means NESO's estimated actual value. Future intervals have forecast values and may not have actuals. Null is never displayed as zero.</p></div></div><div className="api-note"><div className="note-number">02</div><div><strong>Provider index is preserved</strong><p>Index labels come from NESO where supplied. A documented app-defined fallback is used only when no provider index is available.</p></div></div><div className="api-note"><div className="note-number">03</div><div><strong>Region is not property-level</strong><p>Postcode lookup returns the carbon intensity of its provider-mapped regional grid area, not a measurement for an address.</p></div></div><div className="api-note"><div className="note-number">04</div><div><strong>Rate limits apply</strong><p>The public NESO API is unauthenticated and rate-limited. Use the persisted collection service for scheduled analysis.</p></div></div></section>
      <div className="attribution-card"><div className="attribution-icon"><Leaf size={19} /></div><div><strong>Independent project · source attribution</strong><p>Data source: National Energy System Operator (NESO) Carbon Intensity API. Licensed under CC BY 4.0. This project is independent and is not endorsed by NESO.</p></div><a href="https://api.carbonintensity.org.uk/" target="_blank" rel="noreferrer" aria-label="Open NESO Carbon Intensity API"><ExternalLink size={16} /></a></div>
    </>
  );
}

function EmptyInline({ label }: { label: string }) {
  return <div className="empty-inline"><CircleHelp size={15} />{label}</div>;
}

function LoadingInline() {
  return <div className="loading-inline"><LoaderCircle size={16} className="spin" />Loading regional history…</div>;
}

function ErrorInline({ message }: { message: string }) {
  return <div className="inline-error" role="alert">{message}</div>;
}

function ChartFallback({ height }: { height: number }) {
  return <div className="chart-fallback" role="status" style={{ height }}>Preparing visualization…</div>;
}

export default App;
