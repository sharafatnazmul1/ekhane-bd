async function setLang(lang) {
  localStorage.setItem("lang", lang);

  // Load JSON
  const res = await fetch("/assets/lang/lang.json");
  const data = await res.json();
  const trans = data[lang];

  // Translate elements with data-t attribute
  document.querySelectorAll("[data-t]").forEach(el => {
    const key = el.getAttribute("data-t");

    // Only replace if translation exists
    if (trans[key] && trans[key].trim() !== "") {
      el.innerHTML = trans[key];
    } 
    // else keep default text
  });
}

window.onload = () => {
  const saved = localStorage.getItem("lang") || "en";
  setLang(saved);
};
