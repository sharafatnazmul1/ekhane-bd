async function setLang(lang) {
  localStorage.setItem("lang", lang);

  const res = await fetch("/assets/lang/lang.json");
  const data = await res.json();
  const trans = data[lang];

  document.querySelectorAll("[data-t]").forEach(el => {
    const key = el.getAttribute("data-t");
    el.innerHTML = trans[key];
  });
}

window.onload = () => {
  const saved = localStorage.getItem("lang") || "en";
  setLang(saved);
};
