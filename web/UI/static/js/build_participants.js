(function () {
  var root = document.getElementById("participants-list");

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

  function loadParticipantsForEvent(eventID) {
    return requestJson("http://localhost:9992/api/participants/list/?attending_event=" + encodeURIComponent(eventID));
  }

  function createEventCard(item) {
    var event = item.event;
    var participants = item.participants || [];
    var card = createElement("article", "data-card has-actions", "");
    var actions = createElement("div", "card-actions", "");
    var seeButton = createElement("button", "card-action", "See all participants");
    var grid = createElement("div", "data-grid", "");

    seeButton.type = "button";
    card.dataset.eventId = event.event_id || "";
    actions.appendChild(seeButton);
    card.appendChild(actions);
    card.appendChild(createElement("h2", "", event.event_title || "Untitled event"));
    grid.appendChild(createPill("Place", event.event_place));
    grid.appendChild(createPill("Starts", formatDateTime(event.event_start_date, event.event_start_time)));
    grid.appendChild(createPill("Finishes", formatDateTime(event.event_finish_date, event.event_finish_time)));
    grid.appendChild(createPill("Registered participants", String(participants.length)));
    card.appendChild(grid);
    seeButton.addEventListener("click", function () {
      showParticipants(event.event_id);
    });
    return card;
  }

  function renderEvents(events) {
    clearElement(root);
    if (!Array.isArray(events) || events.length === 0) {
      root.appendChild(createElement("p", "muted", "No events found."));
      return;
    }
    Promise.all(events.map(function (event) {
      return loadParticipantsForEvent(event.event_id).then(function (participants) {
        return { event: event, participants: participants };
      }).catch(function () {
        return { event: event, participants: [] };
      });
    })).then(function (items) {
      clearElement(root);
      items.forEach(function (item) {
        root.appendChild(createEventCard(item));
      });
    });
  }

  function loadEvents() {
    return requestJson("http://localhost:9992/api/events/list/?target=all").then(renderEvents).catch(function () {
      clearElement(root);
      root.appendChild(createElement("p", "error-text", "Could not load events."));
    });
  }

  function createParticipantCard(participant) {
    var card = createElement("article", "data-card", "");
    var grid = createElement("div", "data-grid", "");
    var name = ((participant.first_name || "") + " " + (participant.middle_name || "") + " " + (participant.last_name || "")).replace(/\s+/g, " ").trim();

    card.dataset.participantId = participant.participant_id || "";
    card.appendChild(createElement("h2", "", name || "Participant"));
    grid.appendChild(createPill("First name", participant.first_name));
    grid.appendChild(createPill("Last name", participant.last_name));
    grid.appendChild(createPill("Middle name", participant.middle_name));
    grid.appendChild(createPill("Organization", participant.organization));
    card.appendChild(grid);
    return card;
  }

  function showParticipants(eventID) {
    return loadParticipantsForEvent(eventID).then(function (participants) {
      var toolbar = createElement("article", "data-card", "");
      var actions = createElement("div", "form-actions", "");
      var backButton = createElement("button", "small-action", "See events");

      backButton.type = "button";
      actions.appendChild(backButton);
      toolbar.appendChild(createElement("h2", "", "Participants"));
      toolbar.appendChild(actions);
      clearElement(root);
      root.appendChild(toolbar);

      if (!Array.isArray(participants) || participants.length === 0) {
        root.appendChild(createElement("p", "muted", "No participants found."));
      } else {
        participants.forEach(function (participant) {
          root.appendChild(createParticipantCard(participant));
        });
      }
      backButton.addEventListener("click", loadEvents);
    }).catch(function () {
      clearElement(root);
      root.appendChild(createElement("p", "error-text", "Could not load participants."));
    });
  }

  if (root) {
    loadEvents();
  }
}());
