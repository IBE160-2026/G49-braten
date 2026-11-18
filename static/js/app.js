// The app's only script (AD-13): delegated listeners on `document`, nothing bound per element.
// Dialogs (AD-18): a dialog partial is swapped into the one #dialog slot and opened here.
// Menus use the native `popover` attribute; this file only places them at their trigger.
(function () {
  "use strict";

  var SLOT_ID = "dialog";
  var returnFocusTo = null;

  function slot() {
    return document.getElementById(SLOT_ID);
  }

  function isDialogRequest(detail) {
    var target = detail && detail.target;
    return !!target && target.id === SLOT_ID;
  }

  function closeOpenPopovers() {
    document.querySelectorAll("[popover]").forEach(function (el) {
      if (el.matches(":popover-open")) el.hidePopover();
    });
  }

  // ---- Dialogs ---------------------------------------------------------------

  document.addEventListener("htmx:beforeRequest", function (evt) {
    if (!isDialogRequest(evt.detail)) return;
    var elt = evt.detail.elt;
    // Opening (not resubmitting) a dialog: remember the trigger to give focus back on close.
    if (!elt.closest("dialog")) {
      var popover = elt.closest("[popover]");
      if (popover) {
        var id = popover.id;
        var visibleTrigger = Array.prototype.find.call(
          document.querySelectorAll('[popovertarget="' + id + '"]'),
          function (t) { return t.offsetParent !== null; }
        );
        returnFocusTo = visibleTrigger || elt;
        popover.hidePopover();
      } else {
        returnFocusTo = elt;
      }
    }
  });

  document.addEventListener("htmx:afterSwap", function (evt) {
    if (!isDialogRequest(evt.detail)) return;
    var dialog = slot().querySelector("dialog");
    if (dialog && !dialog.open) dialog.showModal();
  });

  // HX-Location (a valid dialog submit) swaps the whole <body>: give focus to the new page's
  // autofocus target, or else to #main (AD-18), never leave it on <body>.
  document.addEventListener("htmx:afterSettle", function (evt) {
    if (evt.detail.target !== document.body) return;
    returnFocusTo = null;
    var focusTarget = document.querySelector("[autofocus]") || document.getElementById("main");
    if (focusTarget) focusTarget.focus();
  });

  // `close` does not bubble, so listen in the capture phase.
  document.addEventListener("close", function (evt) {
    var dialog = evt.target;
    if (!(dialog instanceof HTMLDialogElement) || dialog.parentElement !== slot()) return;
    slot().replaceChildren();
    if (returnFocusTo && document.contains(returnFocusTo)) returnFocusTo.focus();
    returnFocusTo = null;
  }, true);

  // «Avbryt» and the close icon are links to the page behind, so they work without JavaScript.
  document.addEventListener("click", function (evt) {
    var closer = evt.target.closest("[data-dialog-close]");
    if (!closer) return;
    var dialog = closer.closest("dialog");
    if (!dialog || !dialog.open) return;
    evt.preventDefault();
    dialog.close();
  });

  // Never keep an open dialog or menu in htmx's history snapshot.
  document.addEventListener("htmx:beforeHistorySave", function () {
    var s = slot();
    if (s) s.replaceChildren();
    closeOpenPopovers();
  });

  // ---- Expected failures (AD-18): a fixed inline message where the action was ----

  function showFailure(evt, templateId) {
    var template = document.getElementById(templateId);
    if (!template) return;
    var elt = evt.detail.elt;
    var dialog = elt && elt.closest ? elt.closest("dialog") : null;
    var place = (dialog && dialog.querySelector(".dialog-messages")) || document.getElementById("page-messages");
    if (!place) return;
    place.replaceChildren(template.content.cloneNode(true));
  }

  document.addEventListener("htmx:sendError", function (evt) {
    showFailure(evt, "message-network-error");
  });
  document.addEventListener("htmx:responseError", function (evt) {
    showFailure(evt, "message-response-error");
  });

  // ---- Menus: place a popover at its visible trigger ---------------------------

  function placePopover(popover) {
    var triggers = document.querySelectorAll('[popovertarget="' + popover.id + '"]');
    var trigger = Array.prototype.find.call(triggers, function (t) { return t.offsetParent !== null; });
    if (!trigger) return;
    var rect = trigger.getBoundingClientRect();
    var gap = 6;
    var margin = 8;
    var width = popover.offsetWidth;
    var height = popover.offsetHeight;
    var vw = document.documentElement.clientWidth;
    var vh = window.innerHeight;
    var left = Math.min(Math.max(margin, rect.right - width), vw - width - margin);
    if (rect.left + width <= vw - margin && rect.left < vw / 2) left = Math.max(margin, rect.left);
    var below = rect.bottom + gap;
    var placeBelow = below + height <= vh - margin || rect.top < vh / 2;
    var top = Math.max(margin, placeBelow ? below : rect.top - gap - height);
    popover.style.inset = "auto";
    popover.style.margin = "0";
    popover.style.left = left + "px";
    popover.style.top = top + "px";
    // Keep every row reachable: the list scrolls inside the space left in the viewport.
    popover.style.maxHeight = (placeBelow ? vh - margin - top : rect.top - gap - top) + "px";
  }

  // `toggle` does not bubble, so listen in the capture phase.
  document.addEventListener("toggle", function (evt) {
    var popover = evt.target;
    if (!(popover instanceof HTMLElement) || !popover.hasAttribute("data-anchored")) return;
    if (evt.newState !== "open") return;
    placePopover(popover);
    if (popover.getAttribute("role") === "listbox") {
      var selected = popover.querySelector('[role="option"][aria-selected="true"]') || popover.querySelector('[role="option"]');
      if (selected) selected.focus();
    }
  }, true);

  // Mobile browsers fire resize when the address bar or keyboard moves; only a width change
  // can misplace a menu.
  var lastWidth = window.innerWidth;
  window.addEventListener("resize", function () {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    closeOpenPopovers();
  });

  // fag-switcher list (role=listbox): ↑ ↓ Home End move between the options.
  document.addEventListener("keydown", function (evt) {
    var listbox = evt.target.closest && evt.target.closest('[role="listbox"]');
    if (!listbox) return;
    var options = Array.prototype.slice.call(listbox.querySelectorAll('[role="option"]'));
    var index = options.indexOf(evt.target);
    var next = null;
    if (evt.key === "ArrowDown") next = options[Math.min(index + 1, options.length - 1)];
    else if (evt.key === "ArrowUp") next = options[Math.max(index - 1, 0)];
    else if (evt.key === "Home") next = options[0];
    else if (evt.key === "End") next = options[options.length - 1];
    if (!next) return;
    evt.preventDefault();
    next.focus();
  });

  // ---- P06 Quiz: keys 1–4 pick an option, Enter answers, Enter again moves on ------------

  function isTyping(el) {
    if (!el || !el.closest) return false;
    if (el.isContentEditable) return true;
    var tag = el.tagName;
    if (tag === "TEXTAREA" || tag === "SELECT") return true;
    return tag === "INPUT" && el.type !== "radio" && el.type !== "checkbox";
  }

  document.addEventListener("keydown", function (evt) {
    if (evt.altKey || evt.ctrlKey || evt.metaKey || evt.shiftKey) return;
    var target = evt.target;
    // 1–4 select an option of the one open option-group, unless the Student is typing.
    if (/^[1-4]$/.test(evt.key) && !isTyping(target)) {
      var group = document.querySelector(".option-group");
      if (!group) return;
      var radios = group.querySelectorAll('input[type="radio"]:not(:disabled)');
      var radio = radios[Number(evt.key) - 1];
      if (!radio) return;
      evt.preventDefault();
      radio.checked = true;
      radio.focus();
      return;
    }
    if (evt.key !== "Enter") return;
    // Enter on an option answers.
    if (target.matches && target.matches('.option-group input[type="radio"]')) {
      var form = target.form;
      if (!form) return;
      evt.preventDefault();
      if (form.requestSubmit) form.requestSubmit();
      else form.submit();
      return;
    }
    // Enter on the feedback heading moves on (never by itself: the Student presses it).
    if (target.matches && target.matches(".feedback-heading")) {
      var card = target.closest("#question-card");
      var next = card && card.querySelector("[data-next]");
      if (!next) return;
      evt.preventDefault();
      next.click();
    }
  });

  // After a swap into #question-card, focus the feedback heading (or the field to fix).
  document.addEventListener("htmx:afterSettle", function (evt) {
    var target = evt.detail && evt.detail.target;
    if (!target || target.id !== "question-card") return;
    var focusTarget = target.querySelector("[data-focus-on-swap]");
    if (focusTarget) focusTarget.focus();
  });

  // ---- P09 Repetisjon: Space or Enter flips the card, keys 1–4 rate it once flipped ----------
  // «Vis svaret» is a link to `?vis=svar`, so the flip works without JavaScript; here it flips in place.

  function reviewCard() {
    return document.querySelector("[data-review-card]");
  }

  function flipCard() {
    var card = reviewCard();
    if (!card || card.classList.contains("is-flipped")) return false;
    var box = document.getElementById("review-card");
    card.classList.add("is-flipped");
    box.querySelectorAll('[data-face="front"]').forEach(function (el) { el.hidden = true; });
    box.querySelectorAll('[data-face="back"]').forEach(function (el) { el.hidden = false; });
    var back = document.getElementById("review-back");
    if (back) back.focus();
    return true;
  }

  document.addEventListener("click", function (evt) {
    var flip = evt.target.closest && evt.target.closest("[data-flip]");
    if (!flip || !reviewCard()) return;
    if (flipCard()) evt.preventDefault();
  });

  document.addEventListener("keydown", function (evt) {
    if (evt.altKey || evt.ctrlKey || evt.metaKey || evt.shiftKey) return;
    var card = reviewCard();
    if (!card || isTyping(evt.target)) return;
    var target = evt.target;
    if (evt.key === " " || evt.key === "Enter") {
      if (card.classList.contains("is-flipped")) return;
      // Enter and Space keep their own meaning on other links and buttons («Avslutt»).
      var control = target.closest && target.closest("a, button, summary, [popover]");
      if (control && !control.hasAttribute("data-flip")) return;
      evt.preventDefault();
      flipCard();
      return;
    }
    if (/^[1-4]$/.test(evt.key)) {
      if (!card.classList.contains("is-flipped")) return;
      var button = document.querySelector('#review-card .rating-button[data-key="' + evt.key + '"]');
      if (!button || button.disabled || button.closest("fieldset:disabled")) return;
      evt.preventDefault();
      button.click();
    }
  });

  // After a rating swaps in the next card (or the end), focus its autofocus target (AD-18).
  document.addEventListener("htmx:afterSettle", function (evt) {
    var target = evt.detail && evt.detail.target;
    if (!target || target.id !== "review-card") return;
    var focusTarget = target.querySelector("[autofocus]");
    if (focusTarget) focusTarget.focus();
  });

  // ---- tema-tabs (P05): ← → Home End follow the neighbouring tab's link ----------
  // Each tab is a full-page GET link (AD-13), so the keys navigate; the flag below puts focus
  // back on the selected tab of the new page.

  var TAB_FOCUS_KEY = "studybuddy:tab-focus";

  document.addEventListener("keydown", function (evt) {
    if (evt.shiftKey || evt.altKey || evt.ctrlKey || evt.metaKey) return;
    var tab = evt.target.closest && evt.target.closest('[role="tab"]');
    var tablist = tab && tab.closest('[role="tablist"]');
    if (!tablist) return;
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    var index = tabs.indexOf(tab);
    var next = null;
    if (evt.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
    else if (evt.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
    else if (evt.key === "Home") next = tabs[0];
    else if (evt.key === "End") next = tabs[tabs.length - 1];
    if (!next) return;
    evt.preventDefault();
    next.focus();
    if (next.getAttribute("aria-selected") === "true") return;
    try {
      window.sessionStorage.setItem(TAB_FOCUS_KEY, next.id);
    } catch (e) { /* storage blocked: the page still loads, focus starts at the top */ }
    window.location.href = next.href;
  });

  // After a keyboard tab change, focus the newly selected tab (the script is deferred, so the
  // document is parsed by now).
  (function restoreTabFocus() {
    var id = null;
    try {
      id = window.sessionStorage.getItem(TAB_FOCUS_KEY);
      window.sessionStorage.removeItem(TAB_FOCUS_KEY);
    } catch (e) { return; }
    if (!id) return;
    var tab = document.getElementById(id);
    if (tab && tab.getAttribute("role") === "tab" && tab.getAttribute("aria-selected") === "true") tab.focus();
  })();

  // ---- result-summary (P07): a strip slot opens the question row it links to -----------------

  function openRowForHash() {
    var id = window.location.hash.slice(1);
    if (!id) return;
    var row = document.getElementById(id);
    if (row && row.tagName === "DETAILS" && row.classList.contains("result-row")) {
      row.open = true;
      var summary = row.querySelector("summary");
      if (summary) summary.focus();
    }
  }
  window.addEventListener("hashchange", openRowForHash);
  // The same slot twice fires no hashchange, so a click opens its row as well.
  document.addEventListener("click", function (evt) {
    var slot = evt.target.closest && evt.target.closest("a.result-slot");
    if (slot && slot.hash === window.location.hash) openRowForHash();
  });
  openRowForHash();

  // ---- D10 topic-picker: the footer counts the chosen tema and their Questions ----
  // The words live in the template (data-one, data-other with {t} and {q}); only numbers come from here.
  document.addEventListener("change", function (evt) {
    var picker = evt.target.closest && evt.target.closest("[data-topic-picker]");
    if (!picker) return;
    var foot = picker.querySelector("[data-topic-picker-count]");
    if (!foot) return;
    var topics = 0;
    var questions = 0;
    picker.querySelectorAll('input[type="checkbox"]').forEach(function (box) {
      if (!box.checked) return;
      topics += 1;
      questions += parseInt(box.getAttribute("data-questions"), 10) || 0;
    });
    var text = foot.getAttribute(topics === 1 ? "data-one" : "data-other") || "";
    foot.textContent = text.replace("{t}", topics).replace("{q}", questions);
  });
})();
