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

  /* ---------------------------------------------------------- trace links */

  /* The kinds of upward reference, in the order a reader thinks about them
     rather than alphabetically. A kind this list has never heard of is still
     the document's vocabulary, so it is shown after the ones it knows rather
     than dropped (NFR-EVO-02) — the same rule the priority bands follow. */
  var TRACE_KINDS = ["cap", "goal", "fr", "nfr", "adr", "us", "uc", "bc", "tg"];

  /* An area code: the second segment of FR-DOC-01. A numeric second segment
     (ADR-04) means the kind itself is the namespace. */
  var AREA = /^[A-Z]{2,4}$/;

  /* Which document owns an identifier (M7-01). The area code where there is
     one, so an addendum may own FR-NEW while the original keeps FR-DOC. The
     rule is spelled the same way in the coverage engine; a link and a collision
     report that disagreed about ownership would send a reader to the wrong
     file and report nothing wrong. */
  function owner(id) {
    var parts = String(id == null ? "" : id).split("-");
    return (parts.length > 1 && AREA.test(parts[1]))
      ? parts[0] + "-" + parts[1] : parts[0];
  }

  /* Every identifier this document defines, so a trace to one of them stays on
     the page. Read from the specification rather than from the DOM: the answer
     has to be the same before the document is inserted as after, and a renderer
     that asks the page about markup it has not written yet gets "no". */
  function identifiers(node, out) {
    out = out || {};
    if (node && typeof node === "object") {
      if (typeof node.id === "string") out[node.id] = true;
      Object.keys(node).forEach(function (key) { identifiers(node[key], out); });
    }
    return out;
  }

  /* Where a trace goes (FR-TRC-07). This document always wins, so a reference
     inside the document that defines it stays local. Anything else is routed by
     namespace to the file that owns it. An identifier this set cannot place
     gets no link at all: a chip that goes nowhere is honest, and one that opens
     the wrong document is not. */
  function route(id, own, links) {
    if (own && own[id]) return "#" + id;
    var file = links ? links[owner(id)] : null;
    return (file && safeHref(file)) ? file + "#" + id : null;
  }

  function traceIds(traces) {
    if (!traces || typeof traces !== "object") return [];
    var known = TRACE_KINDS.filter(function (kind) { return traces[kind]; });
    var rest = Object.keys(traces).filter(function (kind) {
      return TRACE_KINDS.indexOf(kind) === -1;
    }).sort();
    var out = [];
    known.concat(rest).forEach(function (kind) {
      list(traces[kind]).forEach(function (id) {
        if (typeof id === "string" && id) out.push(id);
      });
    });
    return out;
  }

  function traceChips(traces, own, links) {
    var ids = traceIds(traces);
    if (!ids.length) return "";
    return '<p class="chips"><span class="chips-label">Traces</span>' +
           join(ids, function (id) {
             var href = route(id, own, links);
             return href ? '<a class="chip" href="' + esc(href) + '">' + esc(id) + "</a>"
                         : '<span class="chip">' + esc(id) + "</span>";
           }) + "</p>";
  }

  /* The document currently being rendered: what it defines and where its
     siblings live. A renderer takes a section and nothing else, deliberately —
     so the one fact that is a property of the whole document rather than of any
     section is held here and set once, at the start of a render. */
  var CONTEXT = {own: {}, links: {}, statuses: {}, statusOrder: [], autonomy: {}};

  /* A closed set's own labels, from the legend the document carries. The
     enumerations are the document's, not this file's — a value this runtime has
     never heard of still renders, as itself (NFR-EVO-02). Kept as one map per
     set rather than one map overall, because "auto" is an autonomy class and a
     criterion kind at the same time and means a different word in each. */
  function labels(legend, name) {
    var out = {};
    list((legend || {})[name]).forEach(function (value) {
      if (value && value.id) out[value.id] = value.label || value.id;
    });
    return out;
  }

  function traces(item) {
    return traceChips(item.traces, CONTEXT.own, CONTEXT.links);
  }

  /* One catalogue entry. Its identifier is the element's id, so a link to
     FR-DOC-01 lands on the requirement itself rather than on the section
     containing four hundred of them. The priority is written twice on purpose:
     as a word a reader sees, and as an attribute a later pass filters on
     without reading the word (NFR-UX-03 — never colour alone). */
  /* The three clauses of one scenario, and its own identifier as its own element
     id. A scenario is what an automated test is named after (FR-TRC-09), so a
     failing test has to be followable back to the exact triple it defends —
     which means the triple has to be linkable, not merely printed. */
  function scenario(one) {
    var clauses = [["Given", one.given], ["When", one.when], ["Then", one.then]];
    return '<li class="scenario" id="' + esc(one.id) + '">' +
           "<h5>" +
           '<a class="ident" href="#' + esc(one.id) + '">' + esc(one.id) + "</a> " +
           rich(one.title) + "</h5><dl>" +
           join(clauses, function (clause) {
             return clause[1] ? "<dt>" + clause[0] + "</dt><dd>" + rich(clause[1]) +
                                "</dd>" : "";
           }) + "</dl></li>";
  }

  /* Open, like every other fold in a catalogue: a document defaults to showing
     what it contains rather than to hiding it (FR-SPC-10). The count is in the
     summary so a reader who does collapse it still knows what is in there. */
  function scenarios(item) {
    var within = list(item.scenarios);
    if (!within.length) return "";
    return '<details class="scenarios" open><summary>Scenarios (' +
           within.length + ")</summary><ol>" + join(within, scenario) +
           "</ol></details>";
  }

  /* An actor-centred flow, folded inside its entry the way scenarios are. The
     four facts are a description list rather than a sentence: a reader looking
     for who performs this is looking for one word, and prose makes them read a
     paragraph to find it. */
  function flow(item) {
    var facts = [["Actor", item.actor], ["Goal", item.goal],
                 ["Trigger", item.trigger]].filter(function (pair) {
      return pair[1];
    });
    var paths = [["Preconditions", item.pre, "ul"], ["Main flow", item.main, "ol"],
                 ["Alternates", item.alt, "ul"], ["Exceptions", item.exc, "ul"]]
      .filter(function (part) { return list(part[1]).length; });
    if (!facts.length && !paths.length && !item.post) return "";

    return '<details class="flow" open><summary>Flow (' +
           list(item.main).length + " steps)</summary>" +
           (facts.length ? '<dl class="facts">' + join(facts, function (pair) {
             return "<dt>" + esc(pair[0]) + "</dt><dd>" + rich(pair[1]) + "</dd>";
           }) + "</dl>" : "") +
           join(paths, function (part) {
             return "<h5>" + esc(part[0]) + "</h5><" + part[2] + ">" +
                    join(part[1], function (step) {
                      return "<li>" + rich(step) + "</li>";
                    }) + "</" + part[2] + ">";
           }) +
           (item.post ? '<p class="post"><strong>Ends with:</strong> ' +
                        rich(item.post) + "</p>" : "") +
           "</details>";
  }

  /* Why a decision was taken, folded inside its entry exactly as a flow is. All
     four parts or none: the context and the decision are what was chosen, and
     the alternatives and consequences are the only things that let a later
     reader judge whether the reasoning still holds (M6-01). A decision showing
     its conclusion and hiding its argument is a decision that gets re-argued. */
  function reasoning(item) {
    var facts = [["Context", item.context], ["Decision", item.decision]]
      .filter(function (pair) { return pair[1]; });
    var paths = [["Alternatives", item.alternatives],
                 ["Consequences", item.consequences]]
      .filter(function (part) { return list(part[1]).length; });
    if (!facts.length && !paths.length) return "";

    return '<details class="reasoning" open><summary>The reasoning (' +
           (facts.length + paths.length) + " parts)</summary>" +
           (facts.length ? '<dl class="facts">' + join(facts, function (pair) {
             return "<dt>" + esc(pair[0]) + "</dt><dd>" + rich(pair[1]) + "</dd>";
           }) + "</dl>" : "") +
           join(paths, function (part) {
             return "<h5>" + esc(part[0]) + "</h5><ul>" +
                    join(part[1], function (line) {
                      return "<li>" + rich(line) + "</li>";
                    }) + "</ul>";
           }) +
           "</details>";
  }

  /* The three parts of a test-first task, folded inside it exactly as the
     reasoning of a decision is (ADR-06). Red first, always: the order is the
     argument. A task that showed the change before the failing test would read
     as work somebody decided to do and then justified. */
  var TDD = [["Red", "red"], ["Green", "green"], ["Refactor", "refactor"]];

  /* The priority band that records a decision NOT to build (FR-TRC-06). Spelled
     here as well as in `z2s/trace.py`, deliberately and for the same reason the
     routing rule is spelled twice: this file is read by a browser with nothing
     else loaded, and a document that had to import its own vocabulary from a
     Python module would not render at all. */
  var EXCLUDED = "Won't";

  function tdd(item) {
    var stated = item.tdd || {};
    var parts = TDD.filter(function (pair) { return stated[pair[1]]; });
    if (!parts.length) return "";
    return '<details class="tdd" open><summary>Test first (' + parts.length +
           " steps)</summary>" +
           '<dl class="facts">' + join(parts, function (pair) {
             return "<dt>" + esc(pair[0]) + "</dt><dd>" + rich(stated[pair[1]]) +
                    "</dd>";
           }) + "</dl></details>";
  }

  /* What decides that a task is finished. The boxes are the plan's own record
     and nobody's reading position (M8-02): they are disabled, because a control
     a reader can operate is a control a reader expects to mean something, and
     the only thing that writes here is the status command. Each criterion is
     its own element with its own identifier, so one can be linked to, ticked and
     reported on by name (FR-PLN-05). */
  function criteria(item) {
    var all = list(item.criteria);
    if (!all.length) return "";
    var done = all.filter(function (one) { return one.done; }).length;
    return '<details class="criteria" open><summary>Done when (' + done + " of " +
           all.length + ")</summary><ul>" +
           join(all, function (one) {
             return '<li class="criterion" id="' + esc(one.id) + '"' +
                    (one.done ? ' data-done="true"' : "") +
                    (one.kind ? ' data-kind="' + esc(one.kind) + '"' : "") + ">" +
                    '<input type="checkbox" disabled' + (one.done ? " checked" : "") +
                    ' aria-labelledby="' + esc(one.id) + '-text" /> ' +
                    '<span id="' + esc(one.id) + '-text">' + rich(one.text) + "</span>" +
                    (one.kind === "human-review"
                      ? ' <span class="badge review">Human review</span>' : "") +
                    "</li>";
           }) + "</ul></details>";
  }

  /* The facts a reader schedules on: whether a machine may attempt this, which
     layer it touches, what it waits for, and how big somebody guessed it is.
     Written as their own elements rather than folded into the summary, because
     a later pass that has to re-read a sentence to find the autonomy class is a
     pass that will get it wrong. */
  function scheduling(item) {
    var facts = [["Autonomy", CONTEXT.autonomy[item.autonomy] || item.autonomy],
                 ["Layer", item.layer],
                 ["Effort", item.effort],
                 ["Waits for", list(item.dependsOn).join(", ")]]
      .filter(function (pair) { return pair[1]; });
    if (!facts.length) return "";
    return '<dl class="scheduling">' + join(facts, function (pair) {
      return "<dt>" + esc(pair[0]) + "</dt><dd>" + rich(pair[1]) + "</dd>";
    }) + "</dl>";
  }

  /* What this entry needs proved beyond what the document already states for
     every entry, and what it is exempt from. A waiver is shown with its reason
     attached, because an exemption whose reason is somewhere else is an
     exemption nobody checks. */
  function alsoVerify(item) {
    var extra = list(item.verify);
    var waived = list(item.waives);
    /* A rule this unit of work was excused, shown beside the exemptions a story
       carries and for the same reason: an exception granted at generation time
       and then left out of the document is an exception nobody reviews again
       (M9-P1-T3). The validator reports it on every run; this is where the
       reader meets it. */
    var excused = list(item.exceptions);
    if (!extra.length && !waived.length && !excused.length) return "";
    return '<div class="also">' +
           (extra.length ? "<h5>Also verify</h5><ul>" + join(extra, function (line) {
             return "<li>" + rich(line) + "</li>";
           }) + "</ul>" : "") +
           (waived.length ? "<h5>Exempt from</h5><ul>" +
            join(waived, function (one) {
              return "<li>" + rich(one.assertion) +
                     ' <span class="why">' + rich(one.reason) + "</span></li>";
            }) + "</ul>" : "") +
           (excused.length ? "<h5>Excused from</h5><ul>" +
            join(excused, function (one) {
              return '<li class="excused">' + esc(one.rule) +
                     ' <span class="why">' + rich(one.reason) + "</span></li>";
            }) + "</ul>" : "") +
           "</div>";
  }

  /* A later decision that changed this requirement, shown against it and marked
     as an amendment rather than woven into the original wording (FR-AMD-04,
     NFR-EVO-05). Distinct on purpose: a reader has to be able to tell what the
     requirement said when it was agreed from what was decided about it after,
     because tests and traces were written against the first. */
  function amendments(item) {
    var found = list(item.amendments);
    if (!found.length) return "";
    return '<div class="amended"><h5>Amended since</h5><ul>' +
           join(found, function (one) {
             return '<li><span class="when">' + esc(one.date) + "</span> " +
                    rich(one.text) + "</li>";
           }) + "</ul></div>";
  }

  /* One folded set of instructions, in the exact markup the prompts SECTION
     renders. Same element, same class names, same button — so the stylesheet
     already reaches it and `applyPrompts` already wires it, wherever on the
     page it is put (M14-03). Shut by default, and the only closed fold in this
     runtime: a page of instructions above the thing they are about buries the
     thing they are about, and the copy button is what a reader actually wants
     from a block they are never going to read on screen. */
  function promptFold(id, title, body) {
    return '<details class="prompt" id="' + esc(id) + '">' +
           "<summary>" + rich(title) + "</summary>" +
           '<button type="button" class="copy" data-copy>Copy</button>' +
           "<pre><code>" + esc(body) + "</code></pre></details>";
  }

  /* The instructions for one unit, on that unit's own card. An operator who has
     found the task they want should not have to go back to the top of the
     document to pick up what to do about it (FR-EXE-15). */
  function unitPrompt(id, title, body) {
    return body ? '<div class="prompts">' + promptFold("prompt-" + id, title, body) +
                  "</div>" : "";
  }

  function requirement(item) {
    var tags = list(item.tags);
    var layers = list(item.testLayers);
    return '<article class="entry" id="' + esc(item.id) + '"' +
           (item.priority ? ' data-priority="' + esc(item.priority) + '"' : "") +
           /* A retired entry is marked in the markup as well as in the words,
              because "Retired" read as a badge and "Retired" read as prose are
              the same sentence to a reader and different things to a filter
              (M7-P2-T4). */
           (item.retired ? ' data-retired="true"' : "") +
           /* A deliberate exclusion is not absent scope, it is a decision
              (FR-GEN-09, ADR-17) — so it stays in the catalogue and is marked
              as what it is. Marked in the markup as well as in the band, for
              the same reason a retired entry is: a reader skimming for what
              gets built should not have to read the priority of every entry.
              `Won't` is spelled here and in `trace.py`, deliberately, the same
              way the routing rule is: the reader of a set does not depend on
              the writer of one. */
           (item.priority === EXCLUDED ? ' data-excluded="true"' : "") +
           ">" +
           "<h4>" +
           (item.retired ? '<span class="badge retired">Retired</span> ' : "") +
           (item.priority ? '<span class="badge">' + esc(item.priority) + "</span> " : "") +
           /* A decision carries a standing rather than a priority band, and the
              two never appear on the same entry — so they share the slot the
              reader already looks in for "how much does this bind me". */
           (item.status ? '<span class="badge standing" data-status="' +
            esc(item.status) + '">' +
            esc(CONTEXT.statuses[item.status] || item.status) + "</span> " : "") +
           /* The identifier is the link to the entry. A reader who wants to send
              somebody to one requirement out of four hundred copies the thing
              they were already going to quote (FR-SPC-06). */
           '<a class="ident" href="#' + esc(item.id) + '">' + esc(item.id) + "</a> " +
           rich(item.title) + "</h4>" +
           /* First inside the card, before the description: what a reader came
              to this entry to take away. */
           unitPrompt(item.id, "Instructions for " + item.id, item.prompt) +
           (item.text ? "<p>" + rich(item.text) + "</p>" : "") +
           /* Why it went, beside what it was. A retired entry with no reason
              beside it is an entry somebody re-proposes next quarter (ADR-03). */
           (item.retired ? '<p class="retired-reason"><strong>Retired:</strong> ' +
            rich(item.retired) + "</p>" : "") +
           /* How a number is arrived at, beside the number. A target whose
              measurement lives somewhere else is a target two people can both
              claim to have met (M6-P1-T3-C2). */
           (item.measured ? '<p class="measured"><strong>Measured by:</strong> ' +
            rich(item.measured) + "</p>" : "") +
           /* An exclusion's note IS its reason, and it is labelled as one. An
              unlabelled note under a `Won't` entry reads as a remark about
              scope somebody might build; labelled, it is the argument, which is
              the thing that stops the decision being re-argued next quarter. */
           (item.notes ? '<p class="' +
            (item.priority === EXCLUDED ? "excluded-reason" : "note") + '">' +
            (item.priority === EXCLUDED ?
             "<strong>Not building this, because:</strong> " : "") +
            rich(item.notes) + "</p>" : "") +
           amendments(item) +
           (tags.length ? '<ul class="tags">' + join(tags, function (tag) {
             return "<li>" + rich(tag) + "</li>";
           }) + "</ul>" : "") +
           /* Which layers actually have to pass before this is done. Written as
              its own list rather than mixed in with the tags, because a reader
              filtering on a tag is filtering on subject matter and a reader
              reading these is reading a verification obligation. */
           (layers.length ? '<ul class="layers">' + join(layers, function (layer) {
             return "<li>" + esc(layer) + "</li>";
           }) + "</ul>" : "") +
           /* What this entry serves, as links a reader can follow upward to the
              thing that justifies it (FR-TRC-03, US-TRC-02). */
           scheduling(item) +
           traces(item) +
           flow(item) +
           reasoning(item) +
           tdd(item) +
           criteria(item) +
           alsoVerify(item) +
           scenarios(item) +
           '<label class="tick"><input type="checkbox" data-review="' +
           esc(item.id) + '" /> <span>Reviewed</span></label>' +
           "</article>";
  }

  /* ----------------------------------------------------------------- rollup */

  /* Progress, worked out here every time the document is opened and stored
     nowhere (FR-STA-04, NFR-DAT-05). A figure written into the specification
     would be right at the moment it was written and wrong from the next status
     change onward, and the reader has no way to tell which they are looking at.

     Deliberately NOT the same thing as the review progress further down: that
     one counts what this reader has read, this one counts what the build has
     finished. Same word, different question, so different names throughout —
     `rollup` and `data-rollup` here, `progress` and `data-progress` there. */
  function statusCounts(items) {
    var counts = {}, total = 0;
    list(items).forEach(function (item) {
      if (!item.status) return;
      counts[item.status] = (counts[item.status] || 0) + 1;
      total += 1;
    });
    return {counts: counts, total: total};
  }

  /* Every human-review criterion nobody has signed off yet, each one still
     knowing which unit it belongs to (FR-STA-08). */
  function outstanding(items) {
    var found = [];
    list(items).forEach(function (item) {
      list(item.criteria).forEach(function (one) {
        if (one.kind === "human-review" && !one.done) {
          found.push({id: one.id, unit: item.id, title: item.title, text: one.text});
        }
      });
    });
    return found;
  }

  function rollupText(figures) {
    var order = CONTEXT.statusOrder.length ? CONTEXT.statusOrder
                                           : Object.keys(figures.counts);
    var said = order.filter(function (state) { return figures.counts[state]; })
      .map(function (state) {
        return figures.counts[state] + " " +
               (CONTEXT.statuses[state] || state).toLowerCase();
      });
    return figures.total + (figures.total === 1 ? " task · " : " tasks · ") +
           (said.join(" · ") || "nothing recorded");
  }

  function rollup(items, name) {
    var figures = statusCounts(items);
    if (!figures.total) return "";
    var done = figures.counts.passing || 0;
    var share = Math.round((done / figures.total) * 100);
    return '<p class="rollup" data-rollup="' + esc(name) + '">' +
           '<span class="bar"><span class="fill" style="width: ' + share +
           '%"></span></span> <span class="figures">' + esc(rollupText(figures)) +
           "</span></p>";
  }

  /* The queue a reviewer clears before a milestone closes, in one place rather
     than one fold at a time (FR-STA-08, M10-P3-T2). Absent outstanding items
     there is no queue and no heading saying there is nothing in it. */
  function queue(items) {
    var waiting = outstanding(items);
    if (!waiting.length) return "";
    return '<details class="queue" data-queue open><summary>Human review ' +
           "outstanding (" + waiting.length + ")</summary><ul>" +
           join(waiting, function (one) {
             return '<li><a href="#' + esc(one.id) + '">' + esc(one.id) +
                    "</a> " + rich(one.text) +
                    ' <span class="unit">' + esc(one.unit) + "</span></li>";
           }) + "</ul></details>";
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
               (item.kicker ? '<p class="kicker">' + rich(item.kicker) + "</p>" : "") +
               (item.title ? "<h3>" + rich(item.title) + "</h3>" : "") +
               (item.body ? "<p>" + rich(item.body) + "</p>" : "") +
               /* Some cards carry a paragraph and some carry a handful of
                  points. Both are the card's content; a list forced into a
                  paragraph is a list a reader has to take apart again. */
               (list(item.items).length ? "<ul>" + join(item.items, function (line) {
                 return "<li>" + rich(line) + "</li>";
               }) + "</ul>" : "") +
               traces(item) +
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
      /* A catalogue that declares no areas is not an error and not empty: some
         things are numbered flat because they cross every area by definition —
         a use case is UC-01 and belongs to nothing (M5-05). Its entries render
         straight into the catalogue, and every filter, deep link and review
         tick keeps working, because all of those are keyed on the entry. */
      /* Derived, on every render: what this catalogue adds up to, and what is
         still waiting on a person. Both are empty strings for a catalogue of
         requirements or decisions, which carry no status and need no queue. */
      var head = rollup(items, section.id) + queue(items);
      if (!list(section.areas).length) {
        return head + '<div class="catalogue">' + join(items, requirement) +
               '<p class="no-match" role="status" hidden>Nothing in this catalogue ' +
               "matches the current filter.</p></div>";
      }
      return head + '<div class="catalogue">' + join(section.areas, function (area) {
        var within = items.filter(function (item) { return item.area === area.key; });
        /* Open, always, on load. A document that hides its own content until
           the reader clicks has hidden its content (FR-SPC-10). */
        return '<details class="area" data-area="' + esc(area.key) + '" open>' +
               "<summary><h3>" + rich(area.name) +
               ' <span class="key">' + esc(area.key) + "</span></h3></summary>" +
               (area.description ? '<p class="area-note">' + rich(area.description) +
                "</p>" : "") +
               unitPrompt(area.key, "Instructions for " + area.key, area.prompt) +
               rollup(within, area.key) +
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

    /* The dependency ordering, as the thing it actually is: rounds. Each wave is
       numbered and its members are listed as links, so a reader who wants to
       know what can start now reads one row rather than a graph (FR-PLN-09). */
    waves: function (section) {
      /* A milestone's own document, where the section names one. A wave member
         is a place to go and start work, so the link goes there rather than to
         a row further down the page the reader is already on. */
      var files = section.files || {};
      return '<ol class="waves">' + join(section.waves, function (wave, index) {
        return '<li class="wave"><h3>Wave ' + (index + 1) + "</h3><ul>" +
               join(wave, function (unit) {
                 var href = files[unit];
                 return "<li>" +
                        (href && safeHref(href)
                          ? '<a href="' + esc(href) + '">' + esc(unit) + "</a>"
                          : '<span class="unit">' + esc(unit) + "</span>") +
                        "</li>";
               }) + "</ul></li>";
      }) + "</ol>";
    },

    /* The instructions a worker is handed, quoted rather than rendered: every
       character between the markers is the prompt, so an asterisk in it is an
       asterisk and not emphasis. Folded, because a page of instructions above
       the plan buries the plan; the copy button is what a reader actually wants
       from a block they are never going to read on screen. */
    prompts: function (section) {
      return '<div class="prompts">' + join(section.items, function (item) {
        return promptFold(item.id, item.title, item.body);
      }) + "</div>";
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
  var BANDS = ["Must", "Should", "Could", EXCLUDED];

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
    var words = [item.id, item.title, item.text, item.notes, item.role,
                 item.actor, item.goal, item.trigger, item.post,
                 /* A decision is found by what it decided and a target by how
                    it is measured, both of which are inside the entry rather
                    than in its title. */
                 item.status, item.context, item.decision, item.measured,
                 item.retired]
      .concat(list(item.tags))
      .concat(list(item.testLayers))
      .concat(list(item.verify))
      .concat(list(item.alternatives)).concat(list(item.consequences))
      /* Every step of a flow, for the same reason a scenario's clauses are
         folded in below: a reader searching for the behaviour has to find the
         entry that specifies it, wherever inside the entry it is written. */
      .concat(list(item.pre)).concat(list(item.main))
      .concat(list(item.alt)).concat(list(item.exc))
      /* An identifier this entry traces to is a thing a reader searches for by
         name: "what does FR-DOC-02 get me" is answered by the entries that
         claim to serve it, and those are exactly these. */
      .concat(traceIds(item.traces))
      /* How a task is scheduled is exactly what a reader filters a plan by:
         "what can run unattended", "what touches the schema", "what waits for
         M7". None of those words are in a task's title. */
      .concat([item.autonomy, item.layer, item.effort])
      .concat(list(item.dependsOn));
    TDD.forEach(function (pair) {
      words = words.concat([(item.tdd || {})[pair[1]]]);
    });
    /* A criterion is inside its task, so a keyword that appears only in what
       proves the work still has to bring the task back — the same rule a
       scenario's clauses follow below. */
    list(item.criteria).forEach(function (one) {
      words = words.concat([one.id, one.text, one.kind]);
    });
    list(item.waives).forEach(function (one) {
      words = words.concat([one.assertion, one.reason]);
    });
    /* "What have we excused, and why" is a question a reader asks of the whole
       plan at once, and the keyword box is how they ask it. */
    list(item.exceptions).forEach(function (one) {
      words = words.concat([one.rule, one.reason]);
    });
    /* "What changed after we agreed it" is asked of the catalogue, not of one
       entry, so an amendment's words and its date both have to be findable. */
    list(item.amendments).forEach(function (one) {
      words = words.concat([one.date, one.text]);
    });
    /* A scenario is inside its entry, so a keyword that only appears in a
       Given/When/Then still has to bring the entry back. Otherwise a reader
       searching for the behaviour finds nothing and concludes it is unspecified,
       when it is spelled out three lines further down. */
    list(item.scenarios).forEach(function (one) {
      words = words.concat([one.id, one.title, one.given, one.when, one.then]);
    });
    return words.filter(Boolean).join(" ").toLowerCase();
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
             esc(entry.title) +
             /* What the section holds, counted by whoever generated it. A reader
                deciding whether to open a catalogue wants the size before they
                scroll it, and a generator that has already counted should not
                make them count again. */
             (section.badge ? '<span class="tally">' + esc(section.badge) +
                              "</span>" : "") +
             "</h2>" +
             '<label class="review"><input type="checkbox" data-review="' +
             esc(entry.id) + '" /> <span>Reviewed</span></label>' +
             (section.lede ? '<p class="lede">' + rich(section.lede) + "</p>" : "") +
             render(section) +
             "</section>";
    });
  }

  function renderDocument(spec) {
    spec = spec || {};
    /* Before any section is rendered: a trace chip needs to know what this
       document defines and which file owns everything else. */
    CONTEXT = {own: identifiers(spec), links: spec.links || {},
               statuses: labels(spec.legend, "statuses"),
               /* The order the document's own legend states, so a rollup reads
                  in the order the reader was taught the vocabulary. */
               statusOrder: list((spec.legend || {}).statuses).map(function (one) {
                 return one.id;
               }),
               autonomy: labels(spec.legend, "autonomy")};
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
    applyPrompts(host);
    applyReview(spec, host, store === undefined ? localStore() : store);
    /* Last: a fragment has to be resolved against the page the filters have
       already settled, or the entry is revealed and then hidden again. */
    trackLinks(host);
    return host;
  }

  /* Hands the prompt beside the button to the clipboard, and says so in the
     button itself rather than in a message somewhere else on the page — the
     reader is looking at the button they just pressed. The label is restored on
     the next press rather than by a timer, because a timer that fires while the
     reader is elsewhere reports nothing to nobody, and a control that quietly
     un-says what it said is a control a reader stops believing.

     Guarded end to end: a document opened from a file has no clipboard
     permission in some engines, and a copy button that throws would take the
     rest of the page's behaviour down with it. */
  function applyPrompts(host) {
    var buttons = host.querySelectorAll("[data-copy]");
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener("click", function () {
        var block = button.parentNode ? button.parentNode.querySelector("pre") : null;
        var text = block ? block.textContent : "";
        var done = function (word) { button.textContent = word; };
        try {
          var clipboard = typeof navigator === "undefined" ? null : navigator.clipboard;
          if (!clipboard) return done("Select and copy");
          clipboard.writeText(text).then(function () {
            done("Copied");
          }, function () {
            done("Select and copy");
          });
        } catch (error) {
          done("Select and copy");
        }
      });
    });
    return buttons.length;
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
    trace: {kinds: TRACE_KINDS, namespace: owner, identifiers: identifiers,
            route: route, ids: traceIds, chips: traceChips},
    schemaVersion: SCHEMA_VERSION, compatible: compatible,
    catalogue: {bands: BANDS, items: catalogueItems, searchable: searchable,
                bandsOf: bandsOf, toolbar: renderToolbar, shows: shows,
                apply: applyCatalogue, reveal: reveal, jump: jump,
                links: trackLinks, mark: MARK},
    plan: {tdd: tdd, criteria: criteria, scheduling: scheduling,
           labels: labels, prompts: applyPrompts},
    rollup: {counts: statusCounts, text: rollupText, render: rollup,
             outstanding: outstanding, queue: queue},
    review: {namespace: namespace, read: readMarks, write: writeMarks,
             reviewable: reviewable, progress: progress, text: progressText,
             apply: applyReview}
  };
}));
