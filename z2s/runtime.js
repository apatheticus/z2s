/* The document runtime.
 *
 * A published document contains its specification as data and nothing else. This
 * script reads that data at load time and builds the readable view from it, so a
 * fact cannot appear twice and disagree with itself (FR-SPC-02, ADR-02).
 *
 * Two rules shape everything below.
 *
 * Authored content is escaped before it is inserted, always, and only three
 * inline forms expand afterwards: bold, inline code and links (NFR-GEN-05,
 * NFR-DAT-07). Everything else an author types is text.
 *
 * A section type the runtime does not recognise renders a visible placeholder
 * and the rest of the document carries on (NFR-GEN-04, NFR-EVO-02). A newer
 * specification opened in an older document is a partial read, never a blank
 * page.
 *
 * Browser built-ins only — no library, at runtime or otherwise (NFR-ARC-03).
 */

(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.Z2S = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  /* ---------------------------------------------------------------- escaping */

  var ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"};

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return ESCAPES[c];
    });
  }

  /* Schemes a link may use. A link is authored prose, so the set is the small
     one a document actually needs; anything else renders as its text with the
     target dropped, rather than as a live javascript: or data: link. */
  var SAFE_SCHEMES = ["http:", "https:", "mailto:"];
  var HAS_SCHEME = /^[a-z][a-z0-9+.-]*:/i;

  function safeHref(href) {
    var scheme = HAS_SCHEME.exec(href);
    if (!scheme) return true;               /* relative, anchor, or path */
    return SAFE_SCHEMES.indexOf(scheme[0].toLowerCase()) !== -1;
  }

  /* The complete set of inline markup, in one table so the permitted forms are
     visible in a single place. Adding a form here is the only way to add one. */
  var INLINE = [
    {name: "link",
     pattern: /\[([^\]]+)\]\(([^)\s]+)\)/g,
     expand: function (whole, text, href) {
       return safeHref(href) ? '<a href="' + href + '">' + text + "</a>" : text;
     }},
    {name: "bold",
     pattern: /\*\*([^*]+)\*\*/g,
     expand: "<strong>$1</strong>"},
    {name: "code",
     pattern: /`([^`]+)`/g,
     expand: "<code>$1</code>"}
  ];

  /* Escape first, expand second. The other order lets an author close a tag from
     inside a bold marker. */
  function rich(value) {
    var out = esc(value);
    for (var i = 0; i < INLINE.length; i++) {
      out = out.replace(INLINE[i].pattern, INLINE[i].expand);
    }
    return out;
  }

  function list(value) {
    return Array.isArray(value) ? value : [];
  }

  function join(items, render) {
    return list(items).map(render).join("");
  }

  /* -------------------------------------------------------------- renderers */

  /* Every renderer takes the section and returns a string. No exceptions, so the
     registry needs no special cases and a new type is a single entry. */
  var renderers = {

    prose: function (section) {
      return join(section.body, function (paragraph) {
        return "<p>" + rich(paragraph) + "</p>";
      });
    },

    list: function (section) {
      var tag = section.ordered ? "ol" : "ul";
      return "<" + tag + ">" + join(section.items, function (item) {
        return "<li>" + rich(item) + "</li>";
      }) + "</" + tag + ">";
    },

    definitions: function (section) {
      return "<dl>" + join(section.items, function (item) {
        return "<dt>" + rich(item.term) + "</dt>" +
               "<dd>" + rich(item.definition) + "</dd>";
      }) + "</dl>";
    },

    table: function (section) {
      var head = join(section.columns, function (column) {
        return "<th scope=\"col\">" + rich(column) + "</th>";
      });
      var body = join(section.rows, function (row) {
        return "<tr>" + join(row, function (cell) {
          return "<td>" + rich(cell) + "</td>";
        }) + "</tr>";
      });
      return "<table>" + (head ? "<thead><tr>" + head + "</tr></thead>" : "") +
             "<tbody>" + body + "</tbody></table>";
    },

    cards: function (section) {
      return '<div class="cards">' + join(section.items, function (item) {
        return '<article class="card">' +
               (item.title ? "<h3>" + rich(item.title) + "</h3>" : "") +
               (item.body ? "<p>" + rich(item.body) + "</p>" : "") +
               "</article>";
      }) + "</div>";
    },

    statistics: function (section) {
      return '<dl class="stats">' + join(section.items, function (item) {
        return '<div class="stat"><dt>' + rich(item.label) + "</dt>" +
               "<dd>" + rich(item.value) + "</dd></div>";
      }) + "</dl>";
    },

    flow: function (section) {
      return '<ol class="flow">' + join(section.steps, function (step) {
        return '<li class="step">' +
               (step.title ? "<h3>" + rich(step.title) + "</h3>" : "") +
               (step.body ? "<p>" + rich(step.body) + "</p>" : "") +
               "</li>";
      }) + "</ol>";
    },

    /* Code is quoted material, not prose: escaped, never expanded. Two asterisks
       in a sample are two asterisks. */
    code: function (section) {
      var language = section.language ? ' data-language="' + esc(section.language) + '"' : "";
      return "<pre" + language + "><code>" + esc(section.body) + "</code></pre>";
    }
  };

  /* Not in the registry: this is what happens when the registry has no answer. */
  function placeholder(section) {
    return '<p class="placeholder" role="note">This document cannot display a ' +
           'section of type <code>' + esc(section.type || "(none)") + "</code>. " +
           "Its content is in the specification embedded in this file.</p>";
  }

  /* ---------------------------------------------------------------- ordering */

  /* One ordering pass. The sections and the contents list both read from it, so
     they cannot disagree about order or number. Numbers are computed from
     position and an authored number is ignored (NFR-GEN-06). */
  function outline(spec) {
    return list((spec || {}).sections).map(function (section, index) {
      return {
        id: section.id || "section-" + (index + 1),
        title: section.title || "",
        number: index + 1
      };
    });
  }

  function pad(number) {
    return number < 10 ? "0" + number : String(number);
  }

  /* ---------------------------------------------------------------- document */

  function renderHero(envelope) {
    var meta = [["Type", envelope.type], ["Version", envelope.version],
                ["Status", envelope.status], ["Date", envelope.date],
                ["Owner", envelope.owner]].filter(function (pair) {
      return pair[1];
    });
    return (envelope.kicker ? '<p class="kicker">' + esc(envelope.kicker) + "</p>" : "") +
           "<h1>" + esc(envelope.title) + "</h1>" +
           (envelope.summary ? '<p class="lead">' + rich(envelope.summary) + "</p>" : "") +
           (meta.length ? '<dl class="meta">' + join(meta, function (pair) {
             return "<div><dt>" + esc(pair[0]) + "</dt><dd>" + esc(pair[1]) + "</dd></div>";
           }) + "</dl>" : "");
  }

  function renderContents(entries) {
    return "<h2>Contents</h2><ol>" + join(entries, function (entry) {
      return '<li><a href="#' + esc(entry.id) + '">' +
             '<span class="number">' + pad(entry.number) + "</span>" +
             "<span>" + esc(entry.title) + "</span></a></li>";
    }) + "</ol>";
  }

  function renderSections(spec, entries) {
    var sections = list((spec || {}).sections);
    return join(entries, function (entry, index) {
      var section = sections[index];
      var render = renderers[section.type] || placeholder;
      return '<section class="section" id="' + esc(entry.id) + '">' +
             '<h2><span class="number">' + pad(entry.number) + "</span>" +
             esc(entry.title) + "</h2>" +
             (section.lede ? '<p class="lede">' + rich(section.lede) + "</p>" : "") +
             render(section) +
             "</section>";
    });
  }

  function renderDocument(spec) {
    spec = spec || {};
    var entries = outline(spec);
    return {
      hero: renderHero(spec.document || {}),
      contents: renderContents(entries),
      sections: renderSections(spec, entries)
    };
  }

  /* ------------------------------------------------------------------- mount */

  function mount(spec, host) {
    var parts = renderDocument(spec);
    host.innerHTML =
      '<header class="hero">' + parts.hero + "</header>" +
      '<nav class="contents" aria-label="Contents">' + parts.contents + "</nav>" +
      '<div class="body">' + parts.sections + "</div>";
    trackActive(host);
    return host;
  }

  /* Marks the contents entry for the section in view. Absent an
     IntersectionObserver the document is simply a document — nothing breaks. */
  function trackActive(host) {
    if (typeof IntersectionObserver !== "function") return null;
    var links = {};
    Array.prototype.forEach.call(host.querySelectorAll(".contents a"), function (link) {
      links[link.getAttribute("href").slice(1)] = link;
    });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        for (var id in links) links[id].classList.remove("active");
        var link = links[entry.target.id];
        if (link) link.classList.add("active");
      });
    }, {rootMargin: "-80px 0px -70% 0px", threshold: 0});
    Array.prototype.forEach.call(host.querySelectorAll(".section"), function (section) {
      observer.observe(section);
    });
    return observer;
  }

  /* The document finds its own data: the one embedded JSON block. No identifier
     is shared between the skeleton and this script. */
  function boot() {
    var block = document.querySelector('script[type="application/json"]');
    var host = document.getElementById("doc");
    if (!block || !host) return null;
    return mount(JSON.parse(block.textContent), host);
  }

  if (typeof document !== "undefined") boot();

  return {
    esc: esc, rich: rich, inline: INLINE,
    renderers: renderers, placeholder: placeholder,
    outline: outline, renderDocument: renderDocument,
    mount: mount, trackActive: trackActive, boot: boot
  };
}));
