import { authFetch } from "./auth/api";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Database,
  FolderClock,
  LoaderCircle,
  Save,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";
import "./history.css";

async function requestJSON(url, options = {}) {
  const response = await authFetch(url, options);
  if (response.status === 204) return null;
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error("Le serveur a renvoyé une réponse illisible.");
  }
  if (!response.ok)
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Impossible d’accéder à la base de données.",
    );
  return body;
}

export function SaveAnalysis({ result, isDemo, savedId, onSaved }) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = useRef(null);
  useEffect(() => {
    setTitle(
      `${isDemo ? "Démonstration" : "Mon bilan"} · ${new Date().toLocaleDateString("fr-FR")}`,
    );
    setError("");
    setBusy(false);
    return () => active.current?.abort();
  }, [result, isDemo]);
  async function save(event) {
    event.preventDefault();
    if (!title.trim() || busy) return;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setError("");
    try {
      const saved = await requestJSON("/api/analyses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim(), result, is_demo: isDemo }),
        signal: controller.signal,
      });
      if (!controller.signal.aborted) onSaved(saved.id);
    } catch (err) {
      if (!controller.signal.aborted)
        setError(
          err instanceof TypeError
            ? "La base est injoignable. Réessayez après reconnexion."
            : err.message,
        );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  return (
    <section className="glass-card save-analysis" aria-labelledby="save-title">
      <div className="section-title">
        <h2 id="save-title">
          <Database size={20} /> Garder une trace de votre progression
        </h2>
        <span className="subtle-badge">SQLite · sur cet ordinateur</span>
      </div>
      {savedId ? (
        <p className="saved-success" role="status">
          <Check size={18} /> Bilan enregistré.{" "}
          <Link to="/historique">
            Retrouver mes bilans <ArrowRight size={14} />
          </Link>
        </p>
      ) : (
        <>
          <p className="muted">
            Enregistrez ce bilan dans la base locale pour le retrouver après
            avoir fermé l’application. Il contient des extraits de vos
            documents. Les fichiers PDF/DOCX originaux ne sont pas conservés.
          </p>
          <form onSubmit={save} className="save-form">
            <label htmlFor="report-title">
              Nom du bilan
              <input
                id="report-title"
                value={title}
                maxLength={100}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={busy}
              />
            </label>
            <button
              className="button button-lime"
              disabled={busy || !title.trim()}
            >
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <Save size={17} />
              )}{" "}
              {busy ? "Enregistrement…" : "Enregistrer ce bilan"}
            </button>
          </form>
        </>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

export default function SavedAnalyses({ onOpen, onDeleted }) {
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState("");
  const action = useRef(null);
  const size = 12;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    requestJSON(`/api/analyses?limit=${size}&offset=${page * size}`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setData(value);
      })
      .catch((err) => {
        if (!controller.signal.aborted)
          setError(
            err instanceof TypeError
              ? "La base locale est injoignable. Vérifiez que le serveur fonctionne."
              : err.message,
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [page, revision]);
  useEffect(() => () => action.current?.abort(), []);
  async function act(item, remove = false) {
    const controller = new AbortController();
    action.current?.abort();
    action.current = controller;
    setBusy(item.id);
    setError("");
    try {
      const saved = await requestJSON(
        `/api/analyses/${encodeURIComponent(item.id)}`,
        { method: remove ? "DELETE" : "GET", signal: controller.signal },
      );
      if (controller.signal.aborted) return;
      if (remove) {
        onDeleted(item.id);
        setConfirm("");
        if (data.items.length === 1 && page > 0) setPage(page - 1);
        else setRevision((v) => v + 1);
      } else onOpen(saved);
    } catch (err) {
      if (!controller.signal.aborted)
        setError(
          err instanceof TypeError
            ? "La connexion a échoué. Réessayez."
            : err.message,
        );
    } finally {
      if (!controller.signal.aborted) setBusy("");
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">VOTRE PROGRESSION, DANS LE TEMPS</p>
          <h1>Des bilans à retrouver.</h1>
          <p className="heading-description">
            Seules les analyses que vous choisissez d’enregistrer sont
            conservées dans votre base locale.
          </p>
        </div>
        <span className="subtle-badge">
          <Database size={15} /> {data.total} bilan{data.total !== 1 ? "s" : ""}
        </span>
      </div>
      {error && (
        <div role="alert" className="history-error">
          <p>{error}</p>
          <button
            className="button button-ghost"
            onClick={() => setRevision((v) => v + 1)}
          >
            Réessayer
          </button>
        </div>
      )}
      {loading ? (
        <p className="history-loading" role="status">
          <LoaderCircle className="spin" size={20} /> Lecture de la base…
        </p>
      ) : !data.items.length && !error ? (
        <section className="glass-card history-empty">
          <FolderClock size={40} />
          <h2>Votre histoire commence ici.</h2>
          <p>
            Après une analyse, choisissez « Enregistrer ce bilan » pour le
            retrouver ici.
          </p>
          <Link className="button button-lime" to="/analyse">
            Créer une analyse <ArrowRight size={17} />
          </Link>
        </section>
      ) : (
        <div className="history-grid">
          {data.items.map((item) => (
            <article className="glass-card history-card" key={item.id}>
              <div className="history-card-top">
                <span className="subtle-badge">
                  {item.is_demo ? "Démonstration" : "Bilan enregistré"}
                </span>
                <strong>
                  {new Intl.NumberFormat("fr-FR", {
                    maximumFractionDigits: 1,
                  }).format(item.score)}
                  <small>/100</small>
                </strong>
              </div>
              <h2>{item.title}</h2>
              <time dateTime={item.created_at}>
                {new Date(item.created_at).toLocaleString("fr-FR", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </time>
              {confirm === item.id ? (
                <div className="delete-confirm">
                  <p>
                    Supprimer ce bilan enregistré ? Cette action est définitive.
                  </p>
                  <button
                    className="button button-ghost button-small"
                    disabled={!!busy}
                    onClick={() => setConfirm("")}
                  >
                    Conserver
                  </button>
                  <button
                    className="button button-danger button-small"
                    disabled={!!busy}
                    onClick={() => act(item, true)}
                  >
                    Confirmer la suppression
                  </button>
                </div>
              ) : (
                <div className="history-actions">
                  <button
                    className="button button-light button-small"
                    disabled={!!busy}
                    onClick={() => act(item)}
                  >
                    {busy === item.id ? (
                      <LoaderCircle className="spin" size={15} />
                    ) : (
                      <ArrowRight size={15} />
                    )}{" "}
                    Ouvrir le bilan
                  </button>
                  <button
                    className="icon-button"
                    aria-label={`Supprimer ${item.title}`}
                    disabled={!!busy}
                    onClick={() => setConfirm(item.id)}
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {data.total > size && (
        <div className="history-pagination">
          <button
            className="button button-ghost"
            disabled={page === 0 || loading || !!busy}
            onClick={() => setPage((v) => v - 1)}
          >
            <ArrowLeft size={16} /> Précédent
          </button>
          <span>
            Page {page + 1} / {Math.ceil(data.total / size)}
          </span>
          <button
            className="button button-ghost"
            disabled={(page + 1) * size >= data.total || loading || !!busy}
            onClick={() => setPage((v) => v + 1)}
          >
            Suivant <ArrowRight size={16} />
          </button>
        </div>
      )}
      <p className="history-privacy">
        Les bilans sont conservés sur cet ordinateur jusqu’à leur suppression.
        Ils ne sont pas chiffrés par l’application : protégez votre session et
        vos sauvegardes.
      </p>
    </>
  );
}
