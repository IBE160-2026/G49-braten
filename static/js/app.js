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
})();
