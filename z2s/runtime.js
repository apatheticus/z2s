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

  /* One catalogue entry. Its identifier is the element's id, so a link to
     FR-DOC-01 lands on the requirement itself rather than on the section
     containing four hundred of them. The priority is written twice on purpose:
     as a word a reader sees, and as an attribute a later pass filters on
     without reading the word (NFR-UX-03 — never colour alone). */
  function requirement(item) {
    var tags = list(item.tags);
    return '<article class="entry" id="' + esc(item.id) + '"' +
           (item.priority ? ' data-priority="' + esc(item.priority) + '"' : "") +
           ">" +
           "<h4>" +
           (item.priority ? '<span class="badge">' + esc(item.priority) + "</span> " : "") +
           /* The identifier is the link to the entry. A reader who wants to send
              somebody to one requirement out of four hundred copies the thing
              they were already going to quote (FR-SPC-06). */
           '<a class="ident" href="#' + esc(item.id) + '">' + esc(item.id) + "</a> " +
           rich(item.title) + "</h4>" +
           (item.text ? "<p>" + rich(item.text) + "</p>" : "") +
           (item.notes ? '<p class="note">' + rich(item.notes) + "</p>" : "") +
           (tags.length ? '<ul class="tags">' + join(tags, function (tag) {
             return "<li>" + rich(tag) + "</li>";
           }) + "</ul>" : "") +
           '<label class="tick"><input type="checkbox" data-review="' +
           esc(item.id) + '" /> <span>Reviewed</span></label>' +
           "</article>";
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

    /* A requirements catalogue: entries grouped under the area they belong to.
       Every fact a reader will want to sort or filter on — the area, the
       priority band, the tags — is in the markup as its own element, not folded
       into a sentence. Prose is not filterable, and a later pass that has to
       re-read sentences to find a priority is a pass that will get it wrong. */
    requirements: function (section) {
      var items = list(section.items);
      return '<div class="catalogue">' + join(section.areas, function (area) {
        var within = items.filter(function (item) { return item.area === area.key; });
        /* Open, always, on load. A document that hides its own content until
           the reader clicks has hidden its content (FR-SPC-10). */
        return '<details class="area" data-area="' + esc(area.key) + '" open>' +
               "<summary><h3>" + rich(area.name) +
               ' <span class="key">' + esc(area.key) + "</span></h3></summary>" +
               (area.description ? '<p class="area-note">' + rich(area.description) +
                "</p>" : "") +
               join(within, requirement) + "</details>";
      }) +
      /* Said in words, in the document, rather than left as an empty page the
         reader has to interpret (FR-SPC-05). */
      '<p class="no-match" role="status" hidden>Nothing in this catalogue matches ' +
      "the current filter.</p></div>";
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

  /* --------------------------------------------------------------- catalogue */

  /* Bands in the order a reader thinks about them rather than the order they
     happen to appear in. A band this list does not know still works; it is
     shown after the ones it does, because a vocabulary the runtime has never
     heard of is still the document's vocabulary (NFR-EVO-02). */
  var BANDS = ["Must", "Should", "Could", "Won't"];

  function catalogueItems(spec) {
    var items = [];
    list((spec || {}).sections).forEach(function (section) {
      if (section.type === "requirements") items = items.concat(list(section.items));
    });
    return items;
  }

  /* Everything a keyword is matched against, joined once per entry rather than
     once per keystroke: at five hundred entries the difference is the whole
     frame budget (NFR-PRF-03). */
  function searchable(item) {
    return [item.id, item.title, item.text, item.notes]
      .concat(list(item.tags))
      .filter(Boolean).join(" ").toLowerCase();
  }

  function bandsOf(items) {
    var seen = {}, extra = [];
    items.forEach(function (item) {
      var band = item.priority;
      if (!band || seen[band]) return;
      seen[band] = true;
      if (BANDS.indexOf(band) === -1) extra.push(band);
    });
    return BANDS.filter(function (band) { return seen[band]; }).concat(extra);
  }

  /* The controls for every catalogue in the document, in one bar. One filter,
     because FR-SPC-05 narrows the document rather than a section, and a second
     box that did the same thing would only raise the question of which one is
     in charge. Absent a catalogue there is nothing to control and no bar. */
  function renderToolbar(spec) {
    var items = catalogueItems(spec);
    if (!items.length) return "";
    var bands = bandsOf(items);
    return '<div class="toolbar" role="search">' +
      '<input type="search" data-filter class="find" autocomplete="off" ' +
      'placeholder="Filter entries" aria-label="Filter entries" />' +
      (bands.length ? '<div class="bands">' + join(bands, function (band) {
        return '<label class="band"><input type="checkbox" data-band="' + esc(band) +
               '" checked /> <span>' + esc(band) + "</span> " +
               '<span class="count" data-count="' + esc(band) + '">0</span></label>';
      }) + "</div>" : "") +
      '<div class="folds">' +
      '<button type="button" data-expand>Expand all</button>' +
      '<button type="button" data-collapse>Collapse all</button></div>' +
      "</div>";
  }

  function each(host, selector, render) {
    return Array.prototype.map.call(host.querySelectorAll(selector), render);
  }

  function ancestor(el, selector, records) {
    var found = el.closest ? el.closest(selector) : null;
    return found ? records[Number(found.getAttribute("data-index"))] : null;
  }

  /* Opens every fold between an element and the page. Used by the deep link and
     by the filter, so a result can never be reported as found and then left
     behind a container the reader has to guess at (FR-SPC-06). */
  function reveal(node) {
    while (node && node.tagName) {
      if (node.tagName === "DETAILS") node.open = true;
      if (node.hidden) node.hidden = false;
      node = node.parentNode;
    }
  }

  /* One predicate decides whether an entry is on the page. Both filters read it
     and a third would be one more clause, not one more pass. */
  function shows(entry, keyword, off) {
    return (!keyword || entry.text.indexOf(keyword) !== -1) && off[entry.band] !== true;
  }

  function applyCatalogue(spec, host) {
    var texts = {};
    catalogueItems(spec).forEach(function (item) { texts[item.id] = searchable(item); });

    var groups = each(host, ".catalogue .area", function (el, index) {
      el.setAttribute("data-index", String(index));
      return {el: el, live: 0};
    });
    var books = each(host, ".catalogue", function (el, index) {
      el.setAttribute("data-index", String(index));
      return {el: el, live: 0, empty: el.querySelector(".no-match")};
    });
    var entries = each(host, ".catalogue .entry", function (el) {
      return {el: el,
              /* From the specification where possible; from the rendered text
                 when a catalogue was built by something other than this
                 runtime, so the filter still works rather than matching
                 nothing. */
              text: texts[el.id] || (el.textContent || "").toLowerCase(),
              band: el.getAttribute("data-priority") || "",
              group: ancestor(el, ".area", groups),
              book: ancestor(el, ".catalogue", books)};
    });
    if (!entries.length) return null;

    var boxes = each(host, "[data-band]", function (el) { return el; });
    var keyword = "";
    var off = {};

    function refresh() {
      var counts = {};
      groups.forEach(function (group) { group.live = 0; });
      books.forEach(function (book) { book.live = 0; });

      entries.forEach(function (entry) {
        var hit = !keyword || entry.text.indexOf(keyword) !== -1;
        /* Counted against the keyword alone. Switching a band off must not
           zero its own count, or the reader loses the one number that would
           tell them what switching it back on would bring (M4-04). */
        if (hit) counts[entry.band] = (counts[entry.band] || 0) + 1;
        var shown = shows(entry, keyword, off);
        entry.el.hidden = !shown;
        if (!shown) return;
        if (entry.group) entry.group.live += 1;
        if (entry.book) entry.book.live += 1;
      });

      boxes.forEach(function (box) {
        var band = box.getAttribute("data-band");
        var count = box.parentNode.querySelector("[data-count]");
        if (count) count.textContent = String(counts[band] || 0);
      });
      groups.forEach(function (group) {
        group.el.hidden = group.live === 0;
        if (keyword && group.live) group.el.open = true;
      });
      books.forEach(function (book) {
        if (book.empty) book.empty.hidden = book.live !== 0;
      });
    }

    var search = host.querySelector("[data-filter]");
    if (search) {
      search.addEventListener("input", function () {
        keyword = search.value.trim().toLowerCase();
        refresh();
      });
    }
    boxes.forEach(function (box) {
      box.addEventListener("change", function () {
        off[box.getAttribute("data-band")] = !box.checked;
        refresh();
      });
    });
    fold(host, "[data-expand]", groups, true);
    fold(host, "[data-collapse]", groups, false);

    refresh();
    return {entries: entries, groups: groups, refresh: refresh};
  }

  function fold(host, selector, groups, open) {
    var button = host.querySelector(selector);
    if (!button) return null;
    button.addEventListener("click", function () {
      groups.forEach(function (group) { group.el.open = open; });
    });
    return button;
  }

  /* Following a link to an entry. The mark is left in place rather than faded
     out on a timer: a mark that removes itself is a mark a reader can miss, and
     under a reduced-motion preference a fade is not shown at all (NFR-UX-02).
     The next jump clears it, so only one entry is ever marked. */
  var MARK = "marked";

  function jump(host, hash) {
    var id = String(hash == null ? "" : hash).replace(/^#/, "");
    if (!id) return null;
    var owner = host.ownerDocument || (typeof document !== "undefined" ? document : null);
    var target = owner && owner.getElementById(id);
    if (!target) return null;
    each(host, "." + MARK, function (el) { el.classList.remove(MARK); });
    reveal(target);
    target.classList.add(MARK);
    if (target.scrollIntoView) target.scrollIntoView();
    return target;
  }

  function trackLinks(host) {
    var owner = host.ownerDocument;
    var view = owner && owner.defaultView;
    if (!view) return null;
    jump(host, view.location.hash);
    view.addEventListener("hashchange", function () { jump(host, view.location.hash); });
    return true;
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

  /* ------------------------------------------------------------ compatibility */

  /* The schema this runtime was written against. It is compared with a
     document's own version, never enforced: a document runtime renders what it
     can and says what it could not, rather than refusing (NFR-EVO-02,
     NFR-GEN-04). Refusing is the reading *tools'* job (NFR-EVO-01), because a
     tool that half-understands a document can write a wrong answer back, while
     a reader can simply see less.

     The compatibility rule lives here, beside the version, so that bumping one
     without considering the other is hard:

       older minor  — render everything; absent newer fields are optional
       newer minor  — render everything present; ignore fields not known here
       any major    — still render; a placeholder marks what cannot be shown */
  var SCHEMA_VERSION = "1.0";

  function compatible(documentVersion, runtimeVersion) {
    var mine = String(runtimeVersion || SCHEMA_VERSION).split(".");
    var theirs = String(documentVersion == null ? "" : documentVersion).split(".");
    if (theirs.length !== 2 || isNaN(Number(theirs[0])) || isNaN(Number(theirs[1]))) {
      return "unknown";
    }
    if (Number(theirs[0]) !== Number(mine[0])) {
      return Number(theirs[0]) < Number(mine[0]) ? "older-major" : "newer-major";
    }
    if (Number(theirs[1]) === Number(mine[1])) return "same";
    return Number(theirs[1]) < Number(mine[1]) ? "older-minor" : "newer-minor";
  }

  /* ------------------------------------------------------------------ review */

  /* A reviewer's ticks are that reviewer's private working state. They are kept
     in browser storage under a namespace built from the method and the
     document's own slug (NFR-GEN-07), so several documents from several
     projects can sit in one browser without overwriting each other, and they
     never enter the specification object — copying a document must not carry
     one reader's progress to the next (FR-SPC-08). */
  var REVIEW_PREFIX = "z2s:";

  function namespace(spec) {
    var envelope = (spec || {}).document || {};
    return REVIEW_PREFIX + (envelope.slug || "doc");
  }

  function readMarks(store, key) {
    try {
      var raw = store.getItem(key);
      var parsed = raw ? JSON.parse(raw) : null;
      /* Storage is shared with the reader's other tabs, extensions and past
         versions of this document. Anything unexpected in it is treated as no
         progress rather than as a reason to fail to render. */
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
      return parsed;
    } catch (error) {
      return {};
    }
  }

  function writeMarks(store, key, marks) {
    try {
      store.setItem(key, JSON.stringify(marks));
      return true;
    } catch (error) {
      /* Private browsing and a full quota both throw here. The document keeps
         working; only the memory of this session is lost. */
      return false;
    }
  }

  /* Everything a reviewer can tick, as one pool: a section, and every entry in
     every catalogue (FR-SPC-08). One pool means one progress figure, and a
     document with no catalogue keeps the review tracking it already had. */
  function reviewable(spec) {
    var ids = outline(spec).map(function (entry) { return entry.id; });
    catalogueItems(spec).forEach(function (item) {
      if (item.id) ids.push(item.id);
    });
    return ids;
  }

  function progress(ids, marks) {
    var reviewed = list(ids).filter(function (id) { return marks[id] === true; });
    return {reviewed: reviewed.length, total: list(ids).length};
  }

  function progressText(counted) {
    return counted.reviewed + " of " + counted.total + " reviewed";
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

  function renderContents(entries, tickable) {
    return "<h2>Contents</h2><ol>" + join(entries, function (entry) {
      return '<li><a href="#' + esc(entry.id) + '">' +
             '<span class="number">' + pad(entry.number) + "</span>" +
             "<span>" + esc(entry.title) + "</span></a></li>";
    }) + "</ol>" +
    /* Aggregate progress, announced when it changes so a reviewer working by
       keyboard hears the count without hunting for it (FR-SPC-08). */
    '<p class="progress" data-progress aria-live="polite">' +
    esc(progressText(progress(tickable, {}))) +
    "</p>" +
    /* Beside the figure it clears, rather than in the toolbar: the progress is
       what a reader is resetting, and a document with no catalogue has a
       progress figure but no toolbar (FR-SPC-08). */
    '<button type="button" class="reset" data-reset>Reset review</button>';
  }

  function renderSections(spec, entries) {
    var sections = list((spec || {}).sections);
    return join(entries, function (entry, index) {
      var section = sections[index];
      var render = renderers[section.type] || placeholder;
      return '<section class="section" id="' + esc(entry.id) + '">' +
             '<h2><span class="number">' + pad(entry.number) + "</span>" +
             esc(entry.title) + "</h2>" +
             '<label class="review"><input type="checkbox" data-review="' +
             esc(entry.id) + '" /> <span>Reviewed</span></label>' +
             (section.lede ? '<p class="lede">' + rich(section.lede) + "</p>" : "") +
             render(section) +
             "</section>";
    });
  }

  function renderDocument(spec) {
    spec = spec || {};
    var entries = outline(spec);
    return {
      toolbar: renderToolbar(spec),
      hero: renderHero(spec.document || {}),
      contents: renderContents(entries, reviewable(spec)),
      sections: renderSections(spec, entries)
    };
  }

  /* ------------------------------------------------------------------- mount */

  function mount(spec, host, store) {
    var parts = renderDocument(spec);
    host.innerHTML =
      parts.toolbar +
      '<header class="hero">' + parts.hero + "</header>" +
      '<nav class="contents" aria-label="Contents">' + parts.contents + "</nav>" +
      '<div class="body">' + parts.sections + "</div>";
    trackActive(host);
    applyCatalogue(spec, host);
    applyReview(spec, host, store === undefined ? localStore() : store);
    /* Last: a fragment has to be resolved against the page the filters have
       already settled, or the entry is revealed and then hidden again. */
    trackLinks(host);
    return host;
  }

  /* Browser storage, when there is any. Private browsing throws on the property
     itself in some engines, so even reaching for it is guarded. */
  function localStore() {
    try {
      return typeof localStorage === "undefined" ? null : localStorage;
    } catch (error) {
      return null;
    }
  }

  /* Restores this reader's ticks and keeps them; the specification object is
     never touched, which is what keeps a copied document free of one reader's
     progress (FR-SPC-08, NFR-GEN-07). */
  function applyReview(spec, host, store) {
    if (!store) return null;
    var key = namespace(spec);
    var marks = readMarks(store, key);
    var ids = reviewable(spec);
    var counter = host.querySelector("[data-progress]");

    function refresh() {
      if (counter) counter.textContent = progressText(progress(ids, marks));
    }

    var ticks = host.querySelectorAll("[data-review]");
    Array.prototype.forEach.call(ticks, function (box) {
      var id = box.getAttribute("data-review");
      box.checked = marks[id] === true;
      box.addEventListener("change", function () {
        if (box.checked) marks[id] = true;
        else delete marks[id];
        writeMarks(store, key, marks);
        refresh();
      });
    });

    /* Emptied in place rather than replaced: every listener above closes over
       this object, and a new one would leave them writing to the old. */
    var reset = host.querySelector("[data-reset]");
    if (reset) {
      reset.addEventListener("click", function () {
        Object.keys(marks).forEach(function (id) { delete marks[id]; });
        Array.prototype.forEach.call(ticks, function (box) { box.checked = false; });
        writeMarks(store, key, marks);
        refresh();
      });
    }

    refresh();
    return {key: key, marks: marks};
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
    mount: mount, trackActive: trackActive, boot: boot,
    schemaVersion: SCHEMA_VERSION, compatible: compatible,
    catalogue: {bands: BANDS, items: catalogueItems, searchable: searchable,
                bandsOf: bandsOf, toolbar: renderToolbar, shows: shows,
                apply: applyCatalogue, reveal: reveal, jump: jump,
                links: trackLinks, mark: MARK},
    review: {namespace: namespace, read: readMarks, write: writeMarks,
             reviewable: reviewable, progress: progress, text: progressText,
             apply: applyReview}
  };
}));
