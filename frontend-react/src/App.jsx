import { useEffect, useRef, useState } from "react";
import {
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  AnimatePresence,
  motion,
  useIsPresent,
  useReducedMotion,
} from "framer-motion";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  BadgeCheck,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  CircleHelp,
  Code2,
  FileText,
  FolderClock,
  GraduationCap,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  Plus,
  RotateCcw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  Users,
  WandSparkles,
  X,
} from "lucide-react";
import { criteria, defaultWeights, demoExamples } from "./demo";
import { readAnalysisSession, writeAnalysisSession } from "./sessionAnalysis";
import { analyzeDocuments, validateInputs } from "./api";
import { downloadReport } from "./exports";
import ScoreGauge from "./ScoreGauge";
import Brand from "./Brand";
import { useAuth } from "./auth/context/AuthContext";
import Settings from "./Settings";
import Architecture from "./Architecture";
import SavedAnalyses, { SaveAnalysis } from "./SavedAnalyses";
import { CritiquePanel, VerdictBadge } from "./Critique";

const emptyDoc = () => ({ mode: "file", file: null, text: "" });
const navItems = [
  { path: "/", label: "Vue d’ensemble", icon: LayoutDashboard },
  { path: "/analyse", label: "Nouvelle analyse", icon: Plus },
  { path: "/resultats", label: "Mes résultats", icon: AudioLines },
  { path: "/progression", label: "Plan de progression", icon: Target },
  { path: "/historique", label: "Bilans enregistrés", icon: FolderClock },
];
const icons = {
  hard_skills: Code2,
  experience: BriefcaseBusiness,
  education: GraduationCap,
  soft_skills: Users,
};
const number = (n) =>
  new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(n);

export default function App() {
  const { utilisateur, deconnexion } = useAuth();
  const [restored] = useState(() => readAnalysisSession(utilisateur?.id));
  const [cv, setCV] = useState(emptyDoc);
  const [job, setJob] = useState(emptyDoc);
  const [weights, setWeights] = useState({ ...defaultWeights });
  const [llm, setLLM] = useState(true);
  const [result, setResult] = useState(restored?.result ?? null);
  const [savedId, setSavedId] = useState(restored?.savedId ?? null);
  const [sessionError, setSessionError] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(
    () => window.matchMedia("(max-width: 680px)").matches,
  );
  const [status, setStatus] = useState("checking");
  const [demo, setDemo] = useState(false);
  const [resultDemo, setResultDemo] = useState(restored?.resultDemo ?? false);
  const [demoIndex, setDemoIndex] = useState(-1);
  const [dirty, setDirty] = useState(false);
  const request = useRef(null);
  const revision = useRef(0);
  const sidebarRef = useRef(null);
  const menuButtonRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const mainRef = useRef(null);
  useEffect(() => {
    setSessionError(!writeAnalysisSession(utilisateur?.id, { result, savedId, resultDemo }));
  }, [utilisateur?.id, result, savedId, resultDemo]);
  useEffect(() => {
    mainRef.current?.focus({ preventScroll: true });
    if (mainRef.current) mainRef.current.scrollTop = 0;
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);
  useEffect(() => {
    const viewport = window.matchMedia("(max-width: 680px)");
    const updateViewport = (event) => {
      setIsMobileViewport(event.matches);
      if (!event.matches) setMobile(false);
    };
    viewport.addEventListener("change", updateViewport);
    return () => viewport.removeEventListener("change", updateViewport);
  }, []);
  useEffect(() => {
    if (!mobile || !isMobileViewport) return;
    const sidebar = sidebarRef.current;
    const focusable = () =>
      Array.from(
        sidebar.querySelectorAll(
          "a[href], button:not([disabled]), [tabindex='0']",
        ),
      );
    focusable()[0]?.focus();
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobile(false);
      }
      if (event.key === "Tab") {
        const elements = focusable();
        const first = elements[0];
        const last = elements[elements.length - 1];
        if (
          event.shiftKey &&
          (document.activeElement === first ||
            !sidebar.contains(document.activeElement))
        ) {
          event.preventDefault();
          last?.focus();
        } else if (
          !event.shiftKey &&
          (document.activeElement === last ||
            !sidebar.contains(document.activeElement))
        ) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      menuButtonRef.current?.focus();
    };
  }, [mobile, isMobileViewport]);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/health", { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((r) => setStatus(r.status === "ready" ? "ready" : "starting"))
      .catch(() => {
        if (!controller.signal.aborted) setStatus("offline");
      });
    return () => controller.abort();
  }, []);
  useEffect(() => () => request.current?.abort(), []);
  function markChanged() {
    revision.current += 1;
    setDirty(true);
  }
  const updateDoc = (setter) => (value) => {
    setter(value);
    markChanged();
    setDemo(false);
    setError("");
  };
  function loadDemo() {
    const next = (demoIndex + 1) % demoExamples.length;
    const example = demoExamples[next];
    setDemoIndex(next);
    setCV({ mode: "text", text: example.cv, file: null });
    setJob({ mode: "text", text: example.job, file: null });
    setDemo(true);
    markChanged();
    setError("");
    navigate("/analyse");
  }
  async function submit(event) {
    event?.preventDefault();
    const invalid = validateInputs(cv, job, weights);
    if (invalid) {
      setError(invalid);
      return;
    }
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const submittedRevision = revision.current;
    const submittedDemo = demo;
    const timeout = setTimeout(() => controller.abort("timeout"), 90000);
    setError("");
    setLoading(true);
    try {
      const output = await analyzeDocuments(
        cv,
        job,
        weights,
        llm,
        controller.signal,
      );
      if (request.current !== controller || controller.signal.aborted) return;
      setResult(output);
      setSavedId(null);
      setResultDemo(submittedDemo);
      setDirty(submittedRevision !== revision.current);
      setStatus("ready");
      navigate("/resultats");
    } catch (err) {
      if (request.current === controller)
        setError(
          controller.signal.aborted
            ? controller.signal.reason === "timeout"
              ? "Le délai de 90 secondes est dépassé. Réessayez ou désactivez la génération enrichie."
              : "Analyse annulée. Vous pouvez modifier vos documents et réessayer."
            : err instanceof TypeError
              ? "Le serveur est injoignable. Vérifiez que le backend est lancé."
              : err.message,
        );
    } finally {
      clearTimeout(timeout);
      if (request.current === controller) {
        setLoading(false);
        request.current = null;
      }
    }
  }
  const formProps = {
    cv,
    job,
    setCV: updateDoc(setCV),
    setJob: updateDoc(setJob),
    weights,
    llm,
    setLLM: (v) => {
      setLLM(v);
      markChanged();
    },
    loading,
    error,
    submit,
    cancel: () => {
      request.current?.abort();
      setLoading(false);
      setError(
        "Analyse annulée. Vous pouvez modifier vos documents et réessayer.",
      );
    },
    demo,
    demoIndex,
    loadDemo,
  };
  return (
    <div
      className={`app-frame ${location.pathname === "/" ? "overview-layout" : ""}`}
    >
      <a className="skip-link" href="#main">
        Aller au contenu
      </a>
      <aside
        id="app-sidebar"
        ref={sidebarRef}
        inert={isMobileViewport && !mobile}
        aria-hidden={isMobileViewport && !mobile ? true : undefined}
        className={`sidebar ${mobile ? "open" : ""}`}
      >
        <NavLink to="/" className="brand" onClick={() => setMobile(false)}>
          <Brand />
        </NavLink>
        <div className="workspace">
          <span className="workspace-avatar">TM</span>
          <div>
            <strong>{utilisateur?.nom || "Mon espace carrière"}</strong>
            <small>Analyses de candidatures</small>
          </div>
        </div>
        <p className="nav-caption">ESPACE DE TRAVAIL</p>
        <nav aria-label="Navigation principale">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              onClick={() => setMobile(false)}
            >
              {location.pathname === path && (
                <motion.span
                  className="nav-active-marker"
                  layoutId="active-navigation"
                  transition={{ type: "spring", stiffness: 420, damping: 36 }}
                />
              )}
              <Icon size={18} />
              <span>{label}</span>
              {path === "/resultats" && result && (
                <span className="nav-count">1</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-card">
            <div className="privacy-symbol">
              <ShieldCheck size={21} />
            </div>
            <strong>Votre parcours reste le vôtre.</strong>
            <p>Vous choisissez les bilans à conserver sur cet ordinateur.</p>
            <NavLink to="/methode">
              Notre méthode <ArrowUpRight size={14} />
            </NavLink>
          </div>
          <nav aria-label="Options">
            <NavLink to="/architecture" onClick={() => setMobile(false)}>
              <Code2 size={18} />
              Architecture du projet
            </NavLink>
            <NavLink to="/parametres" onClick={() => setMobile(false)}>
              <Settings2 size={18} />
              Paramètres
            </NavLink>
            <NavLink to="/methode" onClick={() => setMobile(false)}>
              <CircleHelp size={18} />
              Méthode & confidentialité
            </NavLink>
          </nav>
          <div className="sidebar-footer">
            <span className="team-avatar">G8</span>
            <div>
              <strong>Projet IA & Data Science</strong>
              <small>EMSI · 5AISDR · 2026—2027</small>
            </div>
          </div>
        </div>
      </aside>
      {mobile && (
        <button
          className="sidebar-backdrop"
          aria-label="Fermer le menu"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button menu-button"
              ref={menuButtonRef}
              aria-label={mobile ? "Fermer le menu" : "Ouvrir le menu"}
              aria-expanded={mobile}
              aria-controls="app-sidebar"
              onClick={() => setMobile(!mobile)}
            >
              {mobile ? <X size={20} /> : <Menu size={20} />}
            </button>
            <span className="breadcrumb">
              Espace carrière <ChevronRight size={13} />{" "}
              <strong>Talent Match</strong>
            </span>
          </div>
          <div className="topbar-right">
            <span className={`server-status ${status}`}>
              <i />
              {status === "ready"
                ? "Moteur prêt"
                : status === "checking"
                  ? "Connexion…"
                  : status === "starting"
                    ? "Modèle en chargement"
                    : "Moteur hors ligne"}
            </span>
            <button className="logout-button" onClick={deconnexion}>
              Se déconnecter
            </button>
          </div>
        </header>
        <main id="main" ref={mainRef} tabIndex={-1}>
          {result && dirty && (
            <div className="notice-banner" role="status">
              Les documents ou paramètres ont changé. Ce bilan correspond au
              dernier envoi ; relancez l’analyse pour le mettre à jour.
            </div>
          )}
          <div className="route-stage">
            <AnimatePresence initial={false} mode="sync">
              <AnimatedPage key={location.pathname}>
                <Routes location={location}>
                  <Route
                    path="/"
                    element={
                      <Overview
                        result={result}
                        loadDemo={loadDemo}
                        navigate={navigate}
                      />
                    }
                  />
                  <Route
                    path="/analyse"
                    element={
                      <>
                        <PageHeading
                          eyebrow="UNE CANDIDATURE, DE NOUVELLES PERSPECTIVES"
                          title="Faisons le point sur votre profil."
                          text="Un CV, une offre. Découvrez ce qui vous rapproche du poste et les étapes pour aller plus loin."
                        />
                        <AnalysisForm {...formProps} />
                      </>
                    }
                  />
                  <Route
                    path="/resultats"
                    element={
                      result ? (
                        <>
                          <Results
                            result={result}
                            demo={resultDemo}
                            navigate={navigate}
                          />
                          <SaveAnalysis
                            result={result}
                            isDemo={resultDemo}
                            savedId={savedId}
                            onSaved={setSavedId}
                          />
                          <p className="muted" role="status">
                            {sessionError
                              ? "Le navigateur ne peut pas conserver ce bilan dans la session. Enregistrez-le dans l’historique pour le retrouver."
                              : "Bilan conservé pendant la session de cet onglet, même après actualisation. Enregistrez-le pour le retrouver plus tard dans l’historique."}
                          </p>
                        </>
                      ) : (
                        <EmptyState
                          icon={AudioLines}
                          title="Votre premier bilan vous attend."
                          text="Importez un CV et une offre pour découvrir votre score, vos points forts et vos axes de progression."
                          action={() => navigate("/analyse")}
                          label="Créer mon analyse"
                          secondary={loadDemo}
                        />
                      )
                    }
                  />
                  <Route
                    path="/progression"
                    element={
                      result ? (
                        <Plan result={result} />
                      ) : (
                        <EmptyState
                          icon={Target}
                          title="Chaque objectif commence par un premier pas."
                          text="Votre feuille de route personnalisée apparaîtra ici après votre première analyse."
                          action={() => navigate("/analyse")}
                          label="Analyser mon profil"
                          secondary={loadDemo}
                        />
                      )
                    }
                  />
                  <Route
                    path="/parametres"
                    element={
                      <Settings
                        weights={weights}
                        setWeights={(v) => {
                          setWeights(v);
                          markChanged();
                        }}
                        llm={llm}
                        setLLM={(v) => {
                          setLLM(v);
                          markChanged();
                        }}
                      />
                    }
                  />
                  <Route
                    path="/historique"
                    element={
                      <SavedAnalyses
                        onOpen={(saved) => {
                          request.current?.abort();
                          request.current = null;
                          setLoading(false);
                          revision.current += 1;
                          setResult(saved.result);
                          setResultDemo(saved.is_demo);
                          setSavedId(saved.id);
                          setCV(emptyDoc());
                          setJob(emptyDoc());
                          setDemo(false);
                          setWeights(
                            Object.fromEntries(
                              Object.entries(saved.result.weights).map(
                                ([key, value]) => [
                                  key,
                                  Math.round(value * 100),
                                ],
                              ),
                            ),
                          );
                          setDirty(false);
                          setError("");
                          navigate("/resultats");
                        }}
                        onDeleted={(id) => {
                          if (savedId === id) setSavedId(null);
                        }}
                      />
                    }
                  />
                  <Route path="/methode" element={<Method />} />
                  <Route path="/architecture" element={<Architecture />} />
                  <Route
                    path="*"
                    element={
                      <EmptyState
                        icon={Search}
                        title="Cette page n’existe pas."
                        text="Revenons à votre espace carrière."
                        action={() => navigate("/")}
                        label="Retour à l’accueil"
                      />
                    }
                  />
                </Routes>
              </AnimatedPage>
            </AnimatePresence>
          </div>
        </main>
        <footer className="page-footer">
          <span>Conçu pour comprendre votre profil. Et préparer la suite.</span>
          <span>
            Talent Match · EMSI G8 <Sparkles size={12} />
          </span>
        </footer>
      </div>
    </div>
  );
}

function PageHeading({ eyebrow, title, text, action }) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {text && <p className="heading-description">{text}</p>}
      </div>
      {action}
    </div>
  );
}
function Reveal({ children, className = "", delay = 0 }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      {children}
    </motion.div>
  );
}

function Overview({ result, loadDemo, navigate }) {
  return (
    <div className="overview-page">
      <PageHeading
        eyebrow="VOTRE ESPACE CARRIÈRE"
        title={
          <>
            Votre espace candidature<span className="accent-dot">.</span>
          </>
        }
        text="Comprendre votre profil. Préparer la suite."
        action={
          <span className="overview-date">
            <Sparkles size={15} />
            CV · offre · bilan
          </span>
        }
      />
      <div className="overview-tabs" aria-label="Raccourcis de votre parcours">
        <span className="overview-tab current">
          <LayoutDashboard size={15} />
          Vue d’ensemble
        </span>
        <button onClick={() => navigate("/analyse")}>
          <Plus size={15} />
          Analyser
        </button>
        <button onClick={() => navigate("/resultats")}>
          <AudioLines size={15} />
          Résultats
        </button>
        <button onClick={() => navigate("/progression")}>
          <Target size={15} />
          Progresser
        </button>
      </div>
      <div className="compact-bento">
        <Reveal className="compact-start purple" delay={0.02}>
          <div className="compact-card-top">
            <span>VOTRE CANDIDATURE</span>
            <FileText size={22} />
          </div>
          <h2>
            Un CV.
            <br />
            Une offre.
            <br />
            <em>Des possibilités.</em>
          </h2>
          <p>Faites le lien entre votre parcours et votre prochain poste.</p>
          <button
            className="button button-dark"
            onClick={() => navigate("/analyse")}
          >
            Nouvelle analyse <ArrowUpRight size={18} />
          </button>
          <span className="compact-footnote">PDF, DOCX ou texte</span>
        </Reveal>
        <Reveal className="compact-journey glass-card" delay={0.06}>
          <div className="compact-card-top">
            <span>COMMENT ÇA MARCHE</span>
            <Sparkles size={20} />
          </div>
          <h2>
            De l’intuition
            <br />à la clarté.
          </h2>
          <ol className="compact-flow">
            <li>
              <span className="flow-icon purple">
                <Upload size={17} />
              </span>
              <div>
                <strong>Importez</strong>
                <p>Votre CV et l’offre visée.</p>
              </div>
              <span className="flow-number">01</span>
            </li>
            <li>
              <span className="flow-icon orange">
                <AudioLines size={17} />
              </span>
              <div>
                <strong>Comprenez</strong>
                <p>Vos acquis et vos écarts.</p>
              </div>
              <span className="flow-number">02</span>
            </li>
            <li>
              <span className="flow-icon lime">
                <Target size={17} />
              </span>
              <div>
                <strong>Avancez</strong>
                <p>Un plan d’action concret.</p>
              </div>
              <span className="flow-number">03</span>
            </li>
          </ol>
        </Reveal>
        <Reveal className="compact-score lime" delay={0.1}>
          <div className="compact-card-top">
            <span>VOTRE ADÉQUATION</span>
            <Target size={22} />
          </div>
          <ScoreGauge score={result?.score} compact />
          <h2>
            {result
              ? "Votre dernier bilan."
              : "Votre profil mérite un regard neuf."}
          </h2>
          <p>
            {result
              ? "Les preuves derrière chaque résultat."
              : "Votre premier score apparaîtra ici après l’analyse."}
          </p>
          <button
            className="compact-link"
            onClick={() => navigate(result ? "/resultats" : "/analyse")}
          >
            {result ? "Ouvrir mon bilan" : "Découvrir mon adéquation"}
            <ArrowUpRight size={17} />
          </button>
        </Reveal>
        <Reveal className="compact-demo orange" delay={0.13}>
          <div className="demo-content">
            <div className="compact-card-top">
              <span>ENVIE DE VOIR AVANT D’ESSAYER ?</span>
            </div>
            <h2>
              Le premier pas,
              <br />
              sans partir de zéro.
            </h2>
            <p>
              Explorez une candidature de démonstration. De vrais calculs, des
              documents d’exemple.
            </p>
            <button className="button button-dark" onClick={loadDemo}>
              Essayer la démo <WandSparkles size={17} />
            </button>
          </div>
          <div className="demo-visual" aria-hidden="true">
            <div className="demo-sheet">
              <div className="demo-sheet-icon">
                <FileText size={24} />
              </div>
              <span>Profil Data Scientist</span>
              <i />
              <i />
              <i />
              <div>
                <b>Python</b>
                <b>SQL</b>
              </div>
            </div>
            <div className="demo-spark">
              <Sparkles size={23} />
            </div>
            <span className="demo-dot">✦</span>
          </div>
        </Reveal>
        <Reveal className="compact-method glass-card" delay={0.16}>
          <div className="compact-card-top">
            <span>SOUS LE CAPOT</span>
            <Code2 size={22} />
          </div>
          <h2>
            Les étapes
            <br />
            de votre analyse.
          </h2>
          <p>
            Découvrez comment React, FastAPI et les modèles NLP travaillent
            ensemble.
          </p>
          <button
            className="text-button"
            onClick={() => navigate("/architecture")}
          >
            Explorer l’architecture <ArrowUpRight size={16} />
          </button>
        </Reveal>
      </div>
      <div className="overview-bottom-note">
        <span>
          <ShieldCheck size={13} />
          Vos bilans sont enregistrés uniquement à votre demande.
        </span>
        <button onClick={() => navigate("/methode")}>
          Méthode & limites <ArrowUpRight size={13} />
        </button>
      </div>
    </div>
  );
}

function AnimatedPage({ children }) {
  const reduce = useReducedMotion();
  const present = useIsPresent();
  return (
    <motion.div
      className="route-view"
      aria-hidden={!present || undefined}
      inert={!present}
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduce ? { opacity: 0 } : { opacity: 0, y: -5 }}
      transition={{ duration: reduce ? 0 : 0.16, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

function DocumentInput({
  kind,
  title,
  subtitle,
  document,
  onChange,
  disabled,
}) {
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState("");
  const input = useRef(null);
  function choose(file) {
    if (!file) return;
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setFileError("Utilisez un fichier PDF ou DOCX.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setFileError("Le fichier dépasse 5 Mo.");
      return;
    }
    setFileError("");
    onChange({ ...document, file });
  }
  const Icon = kind === "cv" ? FileText : BriefcaseBusiness;
  return (
    <section className="document-card glass-card">
      <div className="document-heading">
        <span
          className={`document-icon ${kind === "cv" ? "purple" : "orange"}`}
        >
          <Icon size={22} />
        </span>
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="segmented" aria-label={`Source du ${kind}`}>
        <button
          type="button"
          aria-pressed={document.mode === "file"}
          className={document.mode === "file" ? "selected" : ""}
          onClick={() => onChange({ ...document, mode: "file" })}
          disabled={disabled}
        >
          <Upload size={14} />
          Importer un fichier
        </button>
        <button
          type="button"
          aria-pressed={document.mode === "text"}
          className={document.mode === "text" ? "selected" : ""}
          onClick={() => onChange({ ...document, mode: "text" })}
          disabled={disabled}
        >
          <FileText size={14} />
          Coller du texte
        </button>
      </div>
      {document.mode === "file" ? (
        <div
          className={`dropzone ${dragging ? "dragging" : ""} ${document.file ? "has-file" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (!disabled) choose(e.dataTransfer.files[0]);
          }}
        >
          <input
            ref={input}
            type="file"
            accept=".pdf,.docx"
            disabled={disabled}
            aria-label={`Importer ${kind === "cv" ? "le CV" : "l’offre"}`}
            onChange={(e) => {
              choose(e.target.files[0]);
              e.target.value = "";
            }}
          />
          {document.file ? (
            <>
              <span className="upload-illustration">
                <FileText size={30} />
              </span>
              <strong className="file-name">{document.file.name}</strong>
              <span>
                {number(document.file.size / 1024)} Ko · Prêt à analyser
              </span>
              <div className="file-actions">
                <button
                  type="button"
                  className="text-button"
                  disabled={disabled}
                  onClick={() => input.current.click()}
                >
                  Remplacer
                </button>
                <button
                  type="button"
                  className="text-button"
                  disabled={disabled}
                  onClick={() => onChange({ ...document, file: null })}
                >
                  <X size={14} />
                  Retirer
                </button>
              </div>
            </>
          ) : (
            <>
              <span className="upload-illustration">
                <Upload size={27} />
              </span>
              <strong>
                Glissez votre {kind === "cv" ? "CV" : "offre"} ici
              </strong>
              <span>ou choisissez un fichier sur votre appareil</span>
              <button
                type="button"
                className="button button-small button-light"
                disabled={disabled}
                onClick={() => input.current.click()}
              >
                Parcourir les fichiers <Plus size={15} />
              </button>
              <small>PDF, DOCX · 5 Mo maximum</small>
            </>
          )}
        </div>
      ) : (
        <div className="text-input-wrap">
          <label className="sr-only" htmlFor={`${kind}-text`}>
            Texte {kind === "cv" ? "du CV" : "de l’offre"}
          </label>
          <textarea
            id={`${kind}-text`}
            value={document.text}
            onChange={(e) => onChange({ ...document, text: e.target.value })}
            disabled={disabled}
            maxLength={30000}
            placeholder={
              kind === "cv"
                ? "Collez votre parcours, vos expériences, vos compétences et votre formation…"
                : "Collez la description du poste, les missions et les compétences recherchées…"
            }
          />
          <span className="char-count">
            {document.text.length.toLocaleString("fr-FR")} / 30 000 caractères ·
            30 minimum
          </span>
        </div>
      )}
      {fileError && (
        <p className="field-error" role="alert">
          {fileError}
        </p>
      )}
      <p className="document-hint">
        <ShieldCheck size={13} />
        {kind === "cv"
          ? "Import temporaire. Vous choisissez les bilans à enregistrer."
          : "Un texte précis donne une analyse plus pertinente."}
      </p>
    </section>
  );
}

function AnalysisForm({
  cv,
  job,
  setCV,
  setJob,
  weights,
  llm,
  setLLM,
  loading,
  error,
  submit,
  cancel,
  demo,
  demoIndex,
  loadDemo,
}) {
  const total = Object.values(weights).reduce((a, b) => a + Number(b), 0);
  return (
    <form onSubmit={submit}>
      <div className="analysis-toolbar">
        <span>
          <span className="mini-step active">1</span>Ajoutez vos documents{" "}
          <span className="toolbar-line" />
          <span className="mini-step">2</span>Découvrez votre bilan
        </span>
        <button
          className="text-button"
          type="button"
          onClick={loadDemo}
          disabled={loading}
        >
          <WandSparkles size={15} />
          {demo
            ? `${demoIndex + 1}/${demoExamples.length} · ${demoExamples[demoIndex].label} · Autre exemple`
            : "Utiliser un exemple"}
        </button>
      </div>
      <div className="document-grid">
        <DocumentInput
          kind="cv"
          title="Votre parcours"
          subtitle="Le point de départ de votre prochaine étape."
          document={cv}
          onChange={setCV}
          disabled={loading}
        />
        <DocumentInput
          kind="job"
          title="Votre objectif"
          subtitle="Le poste qui vous donne envie d’avancer."
          document={job}
          onChange={setJob}
          disabled={loading}
        />
      </div>
      <div className="analysis-bottom glass-card">
        <div className="llm-option">
          <label className="switch-label">
            <input
              type="checkbox"
              checked={llm}
              disabled={loading}
              onChange={(e) => setLLM(e.target.checked)}
            />
            <span className="switch-track" />
            <span>
              <strong>
                Bilan critique généré par IA{" "}
                <Sparkles size={14} />
              </strong>
              <small>
                Un modèle de langage juge votre CV comme un recruteur exigeant
                et réécrit vos phrases. Les sections du CV (hors coordonnées)
                sont transmises au service configuré. Désactivé : bilan
                critique local.
              </small>
            </span>
          </label>
        </div>
        <div className="analysis-submit">
          <span>
            <ShieldCheck size={14} />
            PDF textuels · 30 pages max. · Analyse locale
          </span>
          <div>
            {loading && (
              <button
                type="button"
                className="button button-ghost"
                onClick={cancel}
              >
                Annuler
              </button>
            )}
            <button
              className="button button-lime"
              type="submit"
              disabled={loading || total !== 100}
            >
              {loading ? (
                <>
                  <LoaderCircle className="spin" size={18} />
                  Analyse en cours…
                </>
              ) : (
                <>
                  Découvrir mon adéquation <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
        {total !== 100 && (
          <p role="alert" className="field-error">
            Vos pondérations totalisent {total} %. Ajustez-les à 100 % dans les
            paramètres.
          </p>
        )}
        {error && (
          <div className="error-banner" role="alert">
            <CircleHelp size={18} />
            {error}
          </div>
        )}
        {loading && (
          <p className="loading-note" role="status">
            Nous extrayons les compétences et comparons les preuves. La
            génération enrichie peut prendre plus de temps.
          </p>
        )}
      </div>
      <div className="weights-inline">
        Pondération actuelle :{" "}
        {criteria.map((c) => (
          <span key={c.key}>
            {c.short} <strong>{weights[c.key]} %</strong>
          </span>
        ))}
        <NavLink to="/parametres">
          Personnaliser <Settings2 size={13} />
        </NavLink>
      </div>
    </form>
  );
}

function EmptyState({ icon: Icon, title, text, action, label, secondary }) {
  return (
    <div className="empty-state glass-card">
      <span className="empty-icon">
        <Icon size={38} />
      </span>
      <p className="eyebrow">VOTRE ESPACE TALENT MATCH</p>
      <h1>{title}</h1>
      <p>{text}</p>
      <div>
        <button className="button button-lime" onClick={action}>
          {label}
          <ArrowRight size={17} />
        </button>
        {secondary && (
          <button className="text-button" onClick={secondary}>
            Essayer un exemple
          </button>
        )}
      </div>
    </div>
  );
}

function Results({ result, demo, navigate }) {
  const [filter, setFilter] = useState("Tous");
  const [tab, setTab] = useState("competences");
  const counts = Object.fromEntries(
    ["Couvert", "Partiel", "Absent"].map((s) => [
      s,
      result.gaps.filter((g) => g.status === s).length,
    ]),
  );
  return (
    <>
      <PageHeading
        eyebrow={
          demo
            ? "BILAN · CANDIDATURE DE DÉMONSTRATION"
            : "VOTRE PROFIL EN PERSPECTIVE"
        }
        title="Voici ce qui vous rapproche du poste."
        text="Un résultat à comprendre, des forces à valoriser et des pistes à explorer."
        action={
          <button
            className="button button-ghost"
            onClick={() => navigate("/analyse")}
          >
            <RotateCcw size={15} />
            Nouvelle analyse
          </button>
        }
      />
      <div className="result-top">
        <section className="result-score lime">
          <div className="card-label">
            <span>ADÉQUATION GLOBALE</span>
            <Target size={21} />
          </div>
          <ScoreGauge score={result.score} />
          <p>
            Une lecture de votre CV,
            <br />
            pas une mesure de votre potentiel.
          </p>
        </section>
        <section className="result-summary glass-card">
          <span className="subtle-badge">
            <Sparkles size={13} />
            Votre synthèse
          </span>
          <h2>Vos acquis. Vos prochaines possibilités.</h2>
          <VerdictBadge verdict={result.recommendations.verdict} />
          <p>{result.recommendations.summary}</p>
          <div className="match-counts">
            <span>
              <i className="dot covered" />
              {counts.Couvert} couvertes
            </span>
            <span>
              <i className="dot partial" />
              {counts.Partiel} partielles
            </span>
            <span>
              <i className="dot absent" />
              {counts.Absent} absentes
            </span>
          </div>
          <small>
            Calculé en {number(result.timings_ms.total / 1000)} s · Conseils{" "}
            {result.recommendations.source === "llm"
              ? "générés par modèle de langage, vérifiés contre le CV"
              : "locaux structurés"}
          </small>
        </section>
      </div>
      <div className="criteria-grid">
        {criteria.map((c) => {
          const Icon = icons[c.key];
          const component = result.components[c.key];
          return (
            <section key={c.key} className={`criterion-card ${c.color}`}>
              <div>
                <Icon size={19} />
                <span>{c.short}</span>
              </div>
              <strong>
                {component.score === null ? "—" : number(component.score)}
                <small>{component.score !== null ? "%" : ""}</small>
              </strong>
              {component.score !== null && (
                <div
                  className="criterion-meter"
                  role="meter"
                  aria-label={c.label}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={component.score}
                >
                  <i style={{ width: `${component.score}%` }} />
                </div>
              )}
              <span>
                {component.score === null
                  ? "Non exigé par l’offre"
                  : c.key === "experience" && result.cv.experience_years == null
                    ? "Durée non reconnue · à vérifier"
                  : `Poids effectif : ${number(result.effective_weights[c.key] * 100)} %`}
              </span>
            </section>
          );
        })}
      </div>
      <section className="glass-card results-detail">
        <div className="section-title">
          <div className="tabs" aria-label="Détail de l’analyse">
            {[
              ["competences", "Matrice des compétences"],
              ["preuves", "Preuves & méthode"],
            ].map(([id, label]) => (
              <button
                key={id}
                aria-pressed={tab === id}
                className={tab === id ? "selected" : ""}
                onClick={() => setTab(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <span className="subtle-badge">{result.gaps.length} compétences</span>
        </div>
        {tab === "competences" ? (
          <>
            <div className="filter-bar">
              {["Tous", "Couvert", "Partiel", "Absent"].map((s) => (
                <button
                  key={s}
                  aria-pressed={filter === s}
                  className={filter === s ? "selected" : ""}
                  onClick={() => setFilter(s)}
                >
                  {s}
                  <span>{s === "Tous" ? result.gaps.length : counts[s]}</span>
                </button>
              ))}
            </div>
            <div className="table-scroll">
              <table className="gap-table">
                <thead>
                  <tr>
                    <th>Compétence</th>
                    <th>Correspondance</th>
                    <th>Exigence</th>
                    <th>Preuve dans votre CV</th>
                  </tr>
                </thead>
                <tbody>
                  {result.gaps
                    .filter((g) => filter === "Tous" || g.status === filter)
                    .map((g) => (
                      <tr key={g.skill}>
                        <td>
                          <strong>{g.skill}</strong>
                          <small>
                            {g.category === "hard_skills"
                              ? "Technique"
                              : "Transversale"}
                          </small>
                        </td>
                        <td>
                          <span
                            className={`status-badge ${g.status === "Couvert" ? "covered" : g.status === "Partiel" ? "partial" : "absent"}`}
                          >
                            <i />
                            {g.status}
                          </span>
                        </td>
                        <td>{g.required ? "Requis" : "Souhaitable"}</td>
                        <td>{g.evidence}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              {!result.gaps.some(
                (g) => filter === "Tous" || g.status === filter,
              ) && (
                <p className="table-empty">
                  Aucune compétence dans cette catégorie.
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="evidence-content">
            {result.warnings.map((w) => (
              <p className="method-notice" key={w}>
                <CircleHelp size={16} />
                {w}
              </p>
            ))}
            {criteria.map((c) => (
              <p key={c.key}>
                <strong>{c.label} — </strong>
                {result.components[c.key].explanation}
              </p>
            ))}
            <p className="muted">Modèle : {result.embedding_model}</p>
            <div className="document-grid">
              {[
                ["CV", result.cv],
                ["Offre", result.job],
              ].map(([title, profile]) => (
                <div key={title}>
                  <h3>Sections extraites · {title}</h3>
                  {Object.entries(profile.sections).map(([name, text]) => (
                    <details key={name}>
                      <summary>{name}</summary>
                      <pre>{text}</pre>
                    </details>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
      <div className="result-bottom">
        <div className="next-step glass-card">
          <span className="document-icon purple">
            <Target size={22} />
          </span>
          <div>
            <h3>Et maintenant, on avance ?</h3>
            <p>Transformez vos écarts en un plan de progression.</p>
          </div>
          <button
            className="button button-light"
            onClick={() => navigate("/progression")}
          >
            Mon plan d’action
            <ArrowRight size={16} />
          </button>
        </div>
        <Exports result={result} />
      </div>
    </>
  );
}

function Exports({ result }) {
  return (
    <section className="export-card glass-card">
      <div>
        <h3>Emportez votre bilan.</h3>
        <p>Le rapport HTML s’imprime aussi en PDF.</p>
      </div>
      <div className="export-buttons">
        {[
          ["html", "Rapport"],
          ["csv", "CSV"],
          ["json", "JSON"],
        ].map(([type, label]) => (
          <button
            className="button button-ghost button-small"
            key={type}
            onClick={() => downloadReport(result, type)}
          >
            <ArrowDownToLine size={14} />
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}

function Plan({ result }) {
  const r = result.recommendations;
  return (
    <>
      <PageHeading
        eyebrow="DE LA COMPRÉHENSION À L’ACTION"
        title="Votre prochaine version commence ici."
        text="Des pistes concrètes, à votre rythme. Choisissez une priorité et faites le premier pas."
      />
      <CritiquePanel recommendations={r} />
      <div className="plan-summary">
        <section className="glass-card">
          <h2>
            <BadgeCheck size={20} />
            Vos points d’appui
          </h2>
          {r.strengths.length ? (
            r.strengths.map((s, i) => (
              <p key={i}>
                <Check size={16} />
                {s}
              </p>
            ))
          ) : (
            <p>
              Ajoutez des preuves concrètes de vos compétences pour mieux
              valoriser votre profil.
            </p>
          )}
        </section>
        <section className="glass-card">
          <h2>
            <Target size={20} />
            Vos priorités
          </h2>
          {r.priorities.length ? (
            r.priorities.map((s, i) => (
              <p key={i}>
                <ArrowUpRight size={16} />
                {s}
              </p>
            ))
          ) : (
            <p>
              Les compétences reconnues sont couvertes. Approfondissez vos
              exemples et préparez votre entretien.
            </p>
          )}
        </section>
      </div>
      <div className="section-title plan-title">
        <h2>Une compétence. Un projet. Un pas en avant.</h2>
        <span className="subtle-badge">{r.actions.length} pistes</span>
      </div>
      <div className="action-grid">
        {r.actions.map((a, i) => (
          <section key={i} className="action-card glass-card">
            <div className="action-heading">
              <span className={`action-number ${criteria[i % 4].color}`}>
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3>{a.skill}</h3>
              <ArrowUpRight size={17} />
            </div>
            <p>{a.project}</p>
            <div className="action-goal">
              <span>VOTRE OBJECTIF</span>
              <p>{a.success_criterion}</p>
            </div>
            {/^https:\/\//i.test(a.resource) ? (
              <a
                className="text-button"
                href={a.resource}
                target="_blank"
                rel="noopener noreferrer"
              >
                Explorer la ressource officielle
                <ArrowUpRight size={15} />
              </a>
            ) : (
              <p className="muted">{a.resource}</p>
            )}
          </section>
        ))}
      </div>
      <section className="glass-card rewrites">
        <h2>
          <WandSparkles size={21} />
          Mieux raconter vos acquis.
        </h2>
        <p className="muted">
          Des suggestions à adapter à votre expérience réelle, sans inventer de
          résultats.
        </p>
        {r.rewrites.map((v, i) => (
          <div className="rewrite" key={i}>
            <div>
              <span>VOTRE EXTRAIT</span>
              <p>{v.original}</p>
            </div>
            <ArrowRight size={18} />
            <div>
              <span>PISTE DE REFORMULATION</span>
              <p>{v.suggestion}</p>
              {v.keywords?.length > 0 && (
                <p className="rewrite-keywords">
                  {v.keywords.map((k) => (
                    <span key={k} className="subtle-badge">
                      {k}
                    </span>
                  ))}
                </p>
              )}
              {v.rationale && <small className="muted">{v.rationale}</small>}
            </div>
          </div>
        ))}
        {!r.rewrites.length && (
          <p>
            Ajoutez des exemples concrets de vos réalisations pour obtenir des
            suggestions de reformulation.
          </p>
        )}
      </section>
      <Exports result={result} />
    </>
  );
}

function Method() {
  return (
    <>
      <PageHeading
        eyebrow="TRANSPARENT, DU DÉBUT À LA FIN"
        title="Un score. Des preuves. Votre jugement."
        text="L’analyse vous aide à comprendre une candidature. Elle ne décide jamais à votre place."
      />
      <div className="method-grid">
        {[
          {
            icon: FileText,
            color: "purple",
            title: "01 · Extraire",
            text: "Lecture des PDF et DOCX, nettoyage du texte et reconnaissance des sections. Le dictionnaire bilingue spaCy normalise les compétences, diplômes et durées explicites.",
          },
          {
            icon: AudioLines,
            color: "lime",
            title: "02 · Comparer",
            text: "Les embeddings MiniLM et la similarité cosinus identifient les liens entre compétences. Une parenté reste partielle : elle ne prouve pas une maîtrise.",
          },
          {
            icon: Target,
            color: "orange",
            title: "03 · Guider",
            text: "Vos forces et lacunes deviennent des pistes de reformulation, des projets pratiques et des ressources. Les conseils enrichis par LLM sont facultatifs.",
          },
        ].map(({ icon: Icon, color, title, text }) => (
          <section className="glass-card" key={title}>
            <span className={`document-icon ${color}`}>
              <Icon size={23} />
            </span>
            <h2>{title}</h2>
            <p>{text}</p>
          </section>
        ))}
      </div>
      <section className="glass-card method-details">
        <h2>Comment le score est-il calculé ?</h2>
        <p>
          Par défaut : 50 % de compétences techniques, 25 % d’expérience, 15 %
          de formation et 10 % de compétences transversales.
        </p>
        <ul>
          <li>
            Compétence explicitement reconnue : 100 points. Compétence connexe :
            50 × similarité cosinus. Aucune preuve : 0 point.
          </li>
          <li>
            Une compétence souhaitable compte moitié moins qu’un prérequis
            obligatoire.
          </li>
          <li>
            Les critères non exigés dans l’offre sont exclus et les poids
            restants renormalisés.
          </li>
          <li>
            L’expérience utilise les durées déclarées, sans additionner des
            périodes ambiguës. La formation compare les niveaux, pas
            l’équivalence des spécialités.
          </li>
        </ul>
        <h2>Les limites à connaître</h2>
        <p>
          Les PDF scannés nécessitent un OCR préalable. Le dictionnaire n’est
          pas exhaustif ; certaines compétences ou négations complexes peuvent
          être mal reconnues. MiniLM est principalement anglophone, complété ici
          par des alias français. Les seuils sont heuristiques et demandent une
          validation sur un corpus annoté.
        </p>
        <h2>Vos données restent vos données</h2>
        <p>
          Les fichiers originaux peuvent être utilisés temporairement pendant
          l’import puis sont fermés. Le dernier bilan est conservé dans la session
          de cet onglet et effacé à la déconnexion. Les bilans enregistrés volontairement restent dans la base
          SQLite locale jusqu’à leur suppression et contiennent des extraits
          personnels. Les exports JSON contiennent les sections extraites :
          protégez-les comme vos documents personnels. Si vous activez les
          conseils enrichis, les preuves sont envoyées au service de génération
          configuré.
        </p>
        <div className="method-notice">
          <ShieldCheck size={20} />
          <span>
            Le score n’est ni une probabilité d’embauche, ni un classement
            objectif des personnes. Vérifiez les preuves et gardez une
            appréciation humaine.
          </span>
        </div>
      </section>
    </>
  );
}
