(function () {
  var eventsList = document.getElementById("events-list");

  function clearElement(element) {
    while (element && element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function replaceDocument(html, nextUrl) {
    if (window.history && window.history.pushState) {
      window.history.pushState({}, "", nextUrl || window.location.href);
    }
    document.open();
    document.write(html);
    document.close();
  }

  function requestJson(url) {
    return fetch(url, { method: "GET", credentials: "same-origin" }).then(function (response) {
      if (response.status >= 300) {
        return response.text().then(function (html) {
          replaceDocument(html, url);
          throw new Error("Request failed");
        });
      }
      return response.json();
    });
  }

  function createElement(tagName, className, text) {
    var element = document.createElement(tagName);
    if (className) {
      element.className = className;
    }
    if (text) {
      element.textContent = text;
    }
    return element;
  }

  function sanitizeDescription(html) {
    var template = document.createElement("template");
    var allowedTags = {
      A: true,
      BR: true,
      DIV: true,
      EM: true,
      H2: true,
      IMG: true,
      LI: true,
      OL: true,
      P: true,
      SPAN: true,
      STRONG: true,
      UL: true
    };

    template.innerHTML = html || "";

    function clean(node) {
      Array.prototype.slice.call(node.children).forEach(function (child) {
        if (!allowedTags[child.tagName]) {
          child.replaceWith(document.createTextNode(child.textContent || ""));
          return;
        }

        Array.prototype.slice.call(child.attributes).forEach(function (attribute) {
          var name = attribute.name.toLowerCase();
          var value = attribute.value || "";
          var lowerValue = value.toLowerCase();
          var allowed = false;

          if (child.tagName === "IMG") {
            allowed = name === "src" && (value.indexOf("/static/icons/") === 0 || value.indexOf("http://localhost:9992/static/icons/") === 0) || name === "alt";
          } else if (child.tagName === "A") {
            allowed = name === "href" && lowerValue.indexOf("javascript:") !== 0 || name === "title";
          }

          if (!allowed) {
            child.removeAttribute(attribute.name);
          }
        });

        clean(child);
      });
    }

    clean(template.content);
    return template.innerHTML;
  }

  function splitDate(value) {
    if (typeof value === "string" && value.length >= 10) {
      return value.slice(0, 10);
    }
    var date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) {
      return "";
    }
    return date.toISOString().slice(0, 10);
  }

  function splitTime(value) {
    if (typeof value === "string" && value.indexOf("T") >= 0) {
      return value.slice(value.indexOf("T") + 1, value.indexOf("T") + 6);
    }
    var date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) {
      return "";
    }
    return date.toISOString().slice(11, 16);
  }

  function formatDateTime(dateValue, timeValue) {
    var date = splitDate(dateValue);
    var time = splitTime(timeValue);
    if (!date) {
      return "Not set";
    }
    return time ? date + " " + time : date;
  }

  function createPill(label, value) {
    var pill = createElement("div", "data-pill", "");
    pill.appendChild(createElement("strong", "", label));
    pill.appendChild(createElement("span", "", value || "Not set"));
    return pill;
  }

  function addEventData(card, event, includeRegistrationLink) {
    var grid = createElement("div", "data-grid", "");
    grid.appendChild(createPill("Place", event.event_place));
    grid.appendChild(createPill("Starts", formatDateTime(event.event_start_date, event.event_start_time)));
    grid.appendChild(createPill("Finishes", formatDateTime(event.event_finish_date, event.event_finish_time)));
    grid.appendChild(createPill("Announced", formatDateTime(event.announcement_date, event.announcement_time)));
    grid.appendChild(createPill("Registration closes", formatDateTime(event.registration_finish_date, event.registration_finish_time)));
    if (includeRegistrationLink) {
      grid.appendChild(createPill("Registration link", event.registration_link));
    }
    card.appendChild(grid);
  }

  function createButton(text) {
    var button = createElement("button", "card-action", text);
    button.type = "button";
    return button;
  }

  function createEventCard(event) {
    var card = createElement("article", "data-card has-actions", "");
    var actions = createElement("div", "card-actions", "");
    var showButton = createButton("See more");

    card.dataset.eventId = event.event_id || "";
    actions.appendChild(showButton);
    card.appendChild(actions);
    card.appendChild(createElement("h2", "", event.event_title || "Untitled event"));
    addEventData(card, event, false);
    showButton.addEventListener("click", function () {
      showEvent(event.event_id);
    });
    return card;
  }

  function renderEvents(events) {
    clearElement(eventsList);
    if (!Array.isArray(events) || events.length === 0) {
      eventsList.appendChild(createElement("p", "muted", "No events found."));
      return;
    }
    events.forEach(function (event) {
      eventsList.appendChild(createEventCard(event));
    });
  }

  function loadEvents() {
    return requestJson("http://localhost:9992/api/events/list/?target=all").then(renderEvents).catch(function () {
      clearElement(eventsList);
      eventsList.appendChild(createElement("p", "error-text", "Could not load events."));
    });
  }

  function showEvent(eventID) {
    return requestJson("http://localhost:9992/api/events/list/?event_id=" + encodeURIComponent(eventID)).then(function (events) {
      var event = Array.isArray(events) ? events[0] : events;
      var card = createElement("article", "data-card has-actions", "");
      var actions = createElement("div", "card-actions", "");
      var seeAll = createButton("See all");
      var description = createElement("div", "event-description", "");

      card.dataset.eventId = event.event_id || "";
      actions.appendChild(seeAll);
      card.appendChild(actions);
      card.appendChild(createElement("h2", "", event.event_title || "Untitled event"));
      addEventData(card, event, true);
      description.innerHTML = sanitizeDescription(event.event_description);
      card.appendChild(description);
      clearElement(eventsList);
      eventsList.appendChild(card);
      seeAll.addEventListener("click", loadEvents);
    });
  }

  if (eventsList) {
    loadEvents();
  }
}());
