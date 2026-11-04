export function validateInputs(cv, job, weights) {
  if (Object.values(weights).reduce((a, b) => a + Number(b), 0) !== 100)
    return "La somme des pondérations doit être égale à 100 %.";
  for (const [name, doc] of [
    ["CV", cv],
    ["offre", job],
  ]) {
    if (doc.mode === "file") {
      if (!doc.file) return `Ajoutez un fichier pour votre ${name}.`;
      if (!/\.(pdf|docx)$/i.test(doc.file.name))
        return "Utilisez un document PDF ou DOCX.";
      if (doc.file.size > 5 * 1024 * 1024)
        return "Chaque fichier doit être inférieur à 5 Mo.";
    } else if (doc.text.trim().length < 30 || doc.text.trim().length > 30000)
      return `Le texte de votre ${name} doit contenir entre 30 et 30 000 caractères.`;
  }
  return null;
}
export async function analyzeDocuments(cv, job, weights, useLLM, signal) {
  const data = new FormData();
  for (const [name, doc] of [
    ["cv", cv],
    ["job", job],
  ]) {
    if (doc.mode === "file") data.append(name + "_file", doc.file);
    else data.append(name + "_text", doc.text);
  }
  data.append(
    "weights",
    JSON.stringify(
      Object.fromEntries(Object.entries(weights).map(([k, v]) => [k, v / 100])),
    ),
  );
  data.append("use_llm", String(useLLM));
  const response = await fetch("/api/analyze/files", {
    method: "POST",
    body: data,
    signal,
  });
  let json;
  try {
    json = await response.json();
  } catch {
    throw new Error(
      "Le serveur a renvoyé une réponse illisible. Vérifiez que le backend est disponible.",
    );
  }
  if (!response.ok)
    throw new Error(
      typeof json.detail === "string"
        ? json.detail
        : "Les documents ne sont pas valides. Vérifiez leur contenu.",
    );
  return json;
}
