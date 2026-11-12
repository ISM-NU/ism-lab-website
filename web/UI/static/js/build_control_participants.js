(function () {
  var root = document.getElementById("participants-list");
  var modal = document.getElementById("participant-modal");
  var form = document.getElementById("participant-form");
  var modalTitle = document.getElementById("participant-modal-title");
  var toast = document.getElementById("toast");
  var currentEventID = "";
  var editingParticipantID = "";
  var toastTimer = null;

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

  function showToast(message) {
    if (!toast) {
      return;
    }
    window.clearTimeout(toastTimer);
    toast.textContent = message || "Transaction Successful";
    toast.classList.add("visible");
    toastTimer = window.setTimeout(function () {
      toast.classList.remove("visible");
    }, 3200);
  }

  function requestJson(url, options) {
    return fetch(url, options || { method: "GET", credentials: "same-origin" }).then(function (response) {
      if (response.status >= 300) {
        return response.text().then(function (html) {
          replaceDocument(html, url);
          throw new Error("Request failed");
        });
      }
      return response.text().then(function (body) {
        return body ? JSON.parse(body) : {};
      });
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

  function createButton(text, className) {
    var button = createElement("button", "card-action " + (className || ""), text);
    button.type = "button";
    return button;
  }

  function loadParticipantsForEvent(eventID) {
    return requestJson("http://localhost:9992/api/participants/list/?attending_event=" + encodeURIComponent(eventID), {
      method: "GET",
      credentials: "same-origin"
    });
  }

  function createEventCard(item) {
    var event = item.event;
    var participants = item.participants || [];
    var card = createElement("article", "data-card has-actions", "");
    var actions = createElement("div", "card-actions", "");
    var seeButton = createButton("See all participants", "");
    var grid = createElement("div", "data-grid", "");

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
    currentEventID = "";
    return requestJson("http://localhost:9992/api/events/list/?target=all", {
      method: "GET",
      credentials: "same-origin"
    }).then(renderEvents).catch(function () {
      clearElement(root);
      root.appendChild(createElement("p", "error-text", "Could not load events."));
    });
  }

  function createParticipantCard(participant) {
    var card = createElement("article", "data-card has-actions", "");
    var actions = createElement("div", "card-actions", "");
    var updateButton = createButton("Update", "");
    var deleteButton = createButton("Delete", "danger");
    var grid = createElement("div", "data-grid", "");
    var name = ((participant.first_name || "") + " " + (participant.middle_name || "") + " " + (participant.last_name || "")).replace(/\s+/g, " ").trim();

    card.dataset.participantId = participant.participant_id || "";
    actions.appendChild(updateButton);
    actions.appendChild(deleteButton);
    card.appendChild(actions);
    card.appendChild(createElement("h2", "", name || "Participant"));
    grid.appendChild(createPill("First name", participant.first_name));
    grid.appendChild(createPill("Last name", participant.last_name));
    grid.appendChild(createPill("Middle name", participant.middle_name));
    grid.appendChild(createPill("Organization", participant.organization));
    card.appendChild(grid);

    updateButton.addEventListener("click", function () {
      openParticipantForm(participant);
    });
    deleteButton.addEventListener("click", function () {
      deleteParticipant(participant.participant_id);
    });

    return card;
  }

  function showParticipants(eventID) {
    currentEventID = eventID;
    return loadParticipantsForEvent(eventID).then(function (participants) {
      var toolbar = createElement("article", "data-card", "");
      var actions = createElement("div", "form-actions", "");
      var backButton = createElement("button", "small-action", "See events");
      var createButton = createElement("button", "small-action primary-tool", "Create participant");

      backButton.type = "button";
      createButton.type = "button";
      actions.appendChild(backButton);
      actions.appendChild(createButton);
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
      createButton.addEventListener("click", function () {
        openParticipantForm({ attending_event: currentEventID });
      });
    }).catch(function () {
      clearElement(root);
      root.appendChild(createElement("p", "error-text", "Could not load participants."));
    });
  }

  function openParticipantForm(participant) {
    editingParticipantID = participant && participant.participant_id ? participant.participant_id : "";
    modalTitle.textContent = editingParticipantID ? "Update participant" : "Create participant";
    form.reset();
    form.elements.first_name.value = participant.first_name || "";
    form.elements.last_name.value = participant.last_name || "";
    form.elements.middle_name.value = participant.middle_name || "";
    form.elements.organization.value = participant.organization || "";
    form.elements.attending_event.value = participant.attending_event || currentEventID || "";
    modal.classList.remove("hidden");
  }

  function closeParticipantForm() {
    modal.classList.add("hidden");
    editingParticipantID = "";
  }

  function participantPayload() {
    return {
      first_name: form.elements.first_name.value.trim(),
      last_name: form.elements.last_name.value.trim(),
      middle_name: form.elements.middle_name.value.trim(),
      organization: form.elements.organization.value.trim(),
      attending_event: form.elements.attending_event.value.trim()
    };
  }

  function submitParticipant(event) {
    var url = "http://localhost:9992/api/participants/create/";
    var method = "POST";
    event.preventDefault();
    if (editingParticipantID) {
      url = "http://localhost:9992/api/participants/update/?participant_id=" + encodeURIComponent(editingParticipantID);
      method = "PUT";
    }
    requestJson(url, {
      method: method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(participantPayload())
    }).then(function () {
      showToast("Transaction Successful");
      closeParticipantForm();
      showParticipants(currentEventID || form.elements.attending_event.value.trim());
    }).catch(function () {
      showToast("Could not save participant");
    });
  }

  function deleteParticipant(participantID) {
    requestJson("http://localhost:9992/api/participants/erase/?participant_id=" + encodeURIComponent(participantID), {
      method: "DELETE",
      credentials: "same-origin"
    }).then(function () {
      showToast("Transaction Successful");
      showParticipants(currentEventID);
    }).catch(function () {
      showToast("Could not delete participant");
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-close-modal]"), function (button) {
    button.addEventListener("click", closeParticipantForm);
  });

  if (form) {
    form.addEventListener("submit", submitParticipant);
  }

  if (root) {
    loadEvents();
  }
}());

(function () {
  var logoutButton = document.getElementById("logout-button");
  var isLoggingOut = false;

  function replaceDocument(html, nextUrl) {
    if (window.history && window.history.pushState) {
      window.history.pushState({}, "", nextUrl);
    }
    document.open();
    document.write(html);
    document.close();
  }

  function deleteSessionCookies() {
    document.cookie = "session-id=; Path=/; Max-Age=0; SameSite=Lax";
    document.cookie = "user-login=; Path=/; Max-Age=0; SameSite=Lax";
  }

  function logout() {
    if (isLoggingOut) {
      return;
    }
    isLoggingOut = true;
    logoutButton.disabled = true;
    logoutButton.textContent = "Logging out";
    fetch("http://localhost:9992/api/sessions/logout/", {
      method: "DELETE",
      credentials: "same-origin"
    }).then(function (response) {
      deleteSessionCookies();
      if (response.status >= 300) {
        return response.text().then(function (html) {
          replaceDocument(html, window.location.href);
        });
      }
      return fetch("http://localhost:9992/control/panel/login/", {
        method: "GET",
        credentials: "same-origin"
      }).then(function (loginResponse) {
        return loginResponse.text().then(function (html) {
          replaceDocument(html, "http://localhost:9992/control/panel/login/");
        });
      });
    }).catch(function () {
      isLoggingOut = false;
      logoutButton.disabled = false;
      logoutButton.textContent = "Logout";
    });
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }
}());
