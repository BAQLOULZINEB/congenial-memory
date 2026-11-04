export default function Brand() {
  return (
    <span className="brand-lockup">
      <svg
        viewBox="0 0 36 36"
        width="34"
        height="34"
        fill="none"
        aria-hidden="true"
      >
        <rect width="36" height="36" rx="10" fill="currentColor" />
        <path
          d="M8 12h13M14.5 12v14M21 25V15l5 6 4-6v10"
          stroke="#21192d"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        talent<span className="brand-light">match</span>
        <span className="brand-dot">.</span>
      </span>
    </span>
  );
}
