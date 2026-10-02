// Shared page behaviour: header, menu, arrival, social links, contact form. Settings live in js/config.js.
(function () {
  "use strict";
  var cfg = window.SITE_CONFIG || {};
  var social = cfg.social || {};
  var mail = cfg.emailjs || {};
  var RESEND_WAIT_MS = 60 * 1000;
  var SCROLLED_PX = 8;
  var STAGGER_MAX = 6;

  var year = document.getElementById("year");
  if (year) { year.textContent = String(new Date().getFullYear()); }

  // Header: the scroll-edge shade shows only while content is under the bar
  var header = document.querySelector(".site-header");
  if (header) {
    var edgeQueued = false;
    var updateEdge = function () {
      edgeQueued = false;
      header.classList.toggle("is-scrolled", window.scrollY > SCROLLED_PX);
    };
    window.addEventListener("scroll", function () {
      if (!edgeQueued) { edgeQueued = true; window.requestAnimationFrame(updateEdge); }
    }, { passive: true });
    updateEdge();
  }

  // Mobile menu: opens from its button; Escape, a link or a press outside closes it
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    var setMenu = function (open) {
      nav.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
    };
    toggle.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) { setMenu(false); }
    });
    document.addEventListener("pointerdown", function (event) {
      if (nav.classList.contains("open") && !nav.contains(event.target) && !toggle.contains(event.target)) { setMenu(false); }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("open")) { setMenu(false); toggle.focus(); }
    });
  }

  // Arrival: blocks that start below the fold settle in once. Anything already on screen is left alone.
  if ("IntersectionObserver" in window) {
    // Once settled, the arrival classes come off so the element's own press feedback is instant again
    var settle = function (event) {
      var el = event.currentTarget;
      if (event.target !== el || event.propertyName !== "opacity") { return; }
      el.classList.remove("reveal", "in");
      el.style.removeProperty("--i");
      el.removeEventListener("transitionend", settle);
    };
    var arrivals = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) { return; }
        entry.target.addEventListener("transitionend", settle);
        entry.target.classList.add("in");
        arrivals.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    var fold = window.innerHeight;
    document.querySelectorAll("main .section .wrap > *").forEach(function (block) {
      var items = block.children;
      var staggered = block.classList.contains("grid") && !block.classList.contains("rail") && items.length <= STAGGER_MAX * 2;
      Array.prototype.forEach.call(staggered ? items : [block], function (el, index) {
        if (el.getBoundingClientRect().top < fold) { return; }
        el.classList.add("reveal");
        if (staggered) { el.style.setProperty("--i", String(index % STAGGER_MAX)); }
        arrivals.observe(el);
      });
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

  function isInvalid(el) {
    var empty = !el.value || !el.value.trim();
    return (el.required && empty) || (!empty && el.validity && el.validity.typeMismatch);
  }

  function mark(el) {
    if (isInvalid(el)) { el.setAttribute("aria-invalid", "true"); } else { el.removeAttribute("aria-invalid"); }
  }

  // Inline feedback: a field is checked when you leave it, and cleared as soon as it is fixed
  form.addEventListener("focusout", function (event) {
    if (event.target.name && event.target.name !== "company") { mark(event.target); }
  });
  form.addEventListener("input", function (event) {
    if (event.target.hasAttribute("aria-invalid")) { mark(event.target); }
  });

  function validate() {
    var bad = Array.prototype.filter.call(form.elements, isInvalid);
    Array.prototype.forEach.call(form.elements, function (el) { if (el.name) { mark(el); } });
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
