// Shared page behaviour: menu, footer year, social links, contact form. Settings live in js/config.js.
(function () {
  "use strict";
  var cfg = window.SITE_CONFIG || {};
  var social = cfg.social || {};
  var mail = cfg.emailjs || {};
  var RESEND_WAIT_MS = 60 * 1000;

  var year = document.getElementById("year");
  if (year) { year.textContent = String(new Date().getFullYear()); }

  // Mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Social links: channel cards say "Coming soon" until a URL is set; other social links are hidden
  document.querySelectorAll("[data-social]").forEach(function (link) {
    var url = social[link.getAttribute("data-social")];
    if (url) { link.href = url; return; }
    if (link.classList.contains("channel-card")) {
      link.classList.add("soon");
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
      var note = link.querySelector("small");
      if (note) { note.textContent = link.getAttribute("data-soon") || "Coming soon"; }
    } else {
      link.hidden = true;
    }
  });

  // Media: only one audio/video plays at a time
  document.addEventListener("play", function (event) {
    document.querySelectorAll("audio, video").forEach(function (m) { if (m !== event.target) { m.pause(); } });
  }, true);

  // Contact form -> EmailJS; if it can't send, a one-tap email link carries the full message
  var form = document.getElementById("contact-form");
  if (!form) { return; }
  var submit = form.querySelector("button[type=submit]");
  var label = submit.textContent;
  var status = form.querySelector(".form-status");
  var error = form.querySelector(".form-error");
  var ready = Boolean(window.emailjs && mail.publicKey && mail.serviceId && mail.templateId);
  if (ready) { window.emailjs.init({ publicKey: mail.publicKey }); }

  function value(name) {
    return (form.elements[name] && form.elements[name].value || "").trim();
  }

  function show(text, state, link) {
    status.textContent = text;
    status.className = "form-status " + state;
    if (link) { status.appendChild(link); }
  }

  function validate() {
    var bad = Array.prototype.filter.call(form.elements, function (el) {
      var empty = !el.value || !el.value.trim();
      return (el.required && empty) || (!empty && el.validity && el.validity.typeMismatch);
    });
    if (!bad.length) { error.hidden = true; return true; }
    error.textContent = (cfg.labels && cfg.labels.fix || "Please fill in or correct:") + " " +
      bad.map(function (el) { return el.closest("label").firstChild.textContent.trim(); }).join(", ");
    error.hidden = false;
    bad[0].focus();
    return false;
  }

  function text() {
    return ["New message via " + (cfg.siteName || document.title), "",
      "Topic: " + value("topic"), "Name: " + value("from_name"), "Email: " + value("from_email"),
      "Mobile: " + (value("from_mobile") || "Not provided"), "", value("message")].join("\n");
  }

  function emailLink(body) {
    if (!mail.toEmail) { return null; }
    var a = document.createElement("a");
    a.className = "btn btn-small btn-ghost";
    a.href = "mailto:" + mail.toEmail + "?subject=" + encodeURIComponent((cfg.siteName || "Website") + " message") +
      "&body=" + encodeURIComponent(body);
    a.textContent = (cfg.labels && cfg.labels.sendEmail) || "Send by email";
    return a;
  }

  function sentRecently() {
    try { return Date.now() - (Number(window.localStorage.getItem("site-sent")) || 0) < RESEND_WAIT_MS; }
    catch (e) { return false; }
  }

  function rememberSent() {
    try { window.localStorage.setItem("site-sent", String(Date.now())); } catch (e) { /* private mode */ }
  }

  var L = cfg.labels || {};
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!validate()) { return; }
    if (value("company")) { show(L.sent || "Thanks! Your message has been sent.", "ok"); return; }  // bot trap
    if (sentRecently()) { show(L.wait || "Already sent. Please wait a minute before sending another.", "err"); return; }
    var body = text();
    if (!ready) { show(L.manual || "Tap to send your message:", "ok", emailLink(body)); return; }
    submit.disabled = true;
    submit.textContent = L.sending || "Sending…";
    status.textContent = "";
    window.emailjs.send(mail.serviceId, mail.templateId, {
      from_name: value("from_name"),
      from_mobile: value("from_mobile") || "Not provided",
      from_email: value("from_email"),
      message: "[" + (cfg.siteName || "Website") + " · " + value("topic") + "]\n\n" + value("message"),
      to_email: mail.toEmail || ""
    }).then(function () {
      rememberSent();
      form.reset();
      show(L.sent || "Thanks! Your message has been sent.", "ok");
    }).catch(function () {
      show(L.failed || "Sorry, it could not be sent automatically. Please send it with one tap:", "err", emailLink(body));
    }).finally(function () {
      submit.disabled = false;
      submit.textContent = label;
    });
  });
})();
