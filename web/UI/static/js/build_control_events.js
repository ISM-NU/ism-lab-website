(function () {
  var eventsList = document.getElementById("events-list");
  var showCreateFormButton = document.getElementById("show-create-form");
  var modal = document.getElementById("event-modal");
  var form = document.getElementById("event-form");
  var modalTitle = document.getElementById("event-modal-title");
  var photoInput = document.getElementById("photo-file-input");
  var photoPreview = document.getElementById("photo-preview");
  var insertPhotoButton = document.getElementById("insert-photo-button");
  var toast = document.getElementById("toast");
  var editingEventID = "";
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

  function toApiDate(value) {
    return value ? value + "T00:00:00Z" : "0001-01-01T00:00:00Z";
  }

  function toApiTime(value) {
    return value ? "0001-01-01T" + value + ":00Z" : "0001-01-01T00:00:00Z";
  }

  function createPill(label, value) {
    var pill = createElement("div", "data-pill", "");
    pill.appendChild(createElement("strong", "", label));
    pill.appendChild(createElement("span", "", value || "Not set"));
    return pill;
  }

  function addEventData(card, event, includeHiddenFields) {
    var grid = createElement("div", "data-grid", "");
    grid.appendChild(createPill("Place", event.event_place));
    grid.appendChild(createPill("Starts", formatDateTime(event.event_start_date, event.event_start_time)));
    grid.appendChild(createPill("Finishes", formatDateTime(event.event_finish_date, event.event_finish_time)));
    grid.appendChild(createPill("Announced", formatDateTime(event.announcement_date, event.announcement_time)));
    grid.appendChild(createPill("Registration closes", formatDateTime(event.registration_finish_date, event.registration_finish_time)));
    if (includeHiddenFields) {
      grid.appendChild(createPill("Registration link", event.registration_link));
    }
    card.appendChild(grid);
  }

  function createActionButton(text, className) {
    var button = createElement("button", "card-action " + (className || ""), text);
    button.type = "button";
    return button;
  }

  function createEventCard(event) {
    var card = createElement("article", "data-card has-actions", "");
    var actions = createElement("div", "card-actions", "");
    var showButton = createActionButton("Show more", "");
    var updateButton = createActionButton("Update event", "");
    var deleteButton = createActionButton("Delete event", "danger");

    card.dataset.eventId = event.event_id || "";
    actions.appendChild(showButton);
    actions.appendChild(updateButton);
    actions.appendChild(deleteButton);
    card.appendChild(actions);
    card.appendChild(createElement("h2", "", event.event_title || "Untitled event"));
    addEventData(card, event, false);

    showButton.addEventListener("click", function () {
      showEvent(event.event_id);
    });
    updateButton.addEventListener("click", function () {
      openEventForm(event);
    });
    deleteButton.addEventListener("click", function () {
      deleteEvent(event.event_id);
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
    return requestJson("http://localhost:9992/api/events/list/?target=all", {
      method: "GET",
      credentials: "same-origin"
    }).then(renderEvents).catch(function () {
      clearElement(eventsList);
      eventsList.appendChild(createElement("p", "error-text", "Could not load events."));
    });
  }

  function showEvent(eventID) {
    return requestJson("http://localhost:9992/api/events/list/?event_id=" + encodeURIComponent(eventID), {
      method: "GET",
      credentials: "same-origin"
    }).then(function (events) {
      var event = Array.isArray(events) ? events[0] : events;
      var card = createElement("article", "data-card has-actions", "");
      var actions = createElement("div", "card-actions", "");
      var seeAll = createActionButton("See all", "");
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

  function fillEventForm(event) {
    form.elements.event_title.value = event.event_title || "";
    form.elements.event_place.value = event.event_place || "";
    form.elements.event_start_date.value = splitDate(event.event_start_date);
    form.elements.event_start_time.value = splitTime(event.event_start_time);
    form.elements.event_finish_date.value = splitDate(event.event_finish_date);
    form.elements.event_finish_time.value = splitTime(event.event_finish_time);
    form.elements.announcement_date.value = splitDate(event.announcement_date);
    form.elements.announcement_time.value = splitTime(event.announcement_time);
    form.elements.registration_finish_date.value = splitDate(event.registration_finish_date);
    form.elements.registration_finish_time.value = splitTime(event.registration_finish_time);
    form.elements.registration_link.value = event.registration_link || "";
    form.elements.event_description.value = event.event_description || "";
  }

  function openEventForm(event) {
    editingEventID = event && event.event_id ? event.event_id : "";
    modalTitle.textContent = editingEventID ? "Update event" : "Create event";
    form.reset();
    clearElement(photoPreview);
    fillEventForm(event || {});
    modal.classList.remove("hidden");
  }

  function closeEventForm() {
    modal.classList.add("hidden");
    editingEventID = "";
  }

  function eventPayload() {
    return {
      event_title: form.elements.event_title.value.trim(),
      event_place: form.elements.event_place.value.trim(),
      event_start_date: toApiDate(form.elements.event_start_date.value),
      event_start_time: toApiTime(form.elements.event_start_time.value),
      event_finish_date: toApiDate(form.elements.event_finish_date.value),
      event_finish_time: toApiTime(form.elements.event_finish_time.value),
      event_description: form.elements.event_description.value.trim(),
      registration_link: form.elements.registration_link.value.trim(),
      announcement_date: toApiDate(form.elements.announcement_date.value),
      announcement_time: toApiTime(form.elements.announcement_time.value),
      registration_finish_date: toApiDate(form.elements.registration_finish_date.value),
      registration_finish_time: toApiTime(form.elements.registration_finish_time.value)
    };
  }

  function submitEvent(event) {
    var url = "http://localhost:9992/api/events/create/";
    var method = "POST";
    event.preventDefault();
    if (editingEventID) {
      url = "http://localhost:9992/api/events/update/?event_id=" + encodeURIComponent(editingEventID);
      method = "PUT";
    }
    requestJson(url, {
      method: method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(eventPayload())
    }).then(function () {
      showToast("Transaction Successful");
      closeEventForm();
      loadEvents();
    }).catch(function () {
      showToast("Could not save event");
    });
  }

  function deleteEvent(eventID) {
    requestJson("http://localhost:9992/api/events/erase/?event_id=" + encodeURIComponent(eventID), {
      method: "DELETE",
      credentials: "same-origin"
    }).then(function () {
      showToast("Transaction Successful");
      loadEvents();
    }).catch(function () {
      showToast("Could not delete event");
    });
  }

  function wrapSelection(before, after) {
    var textarea = form.elements.event_description;
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var value = textarea.value;
    var selected = value.slice(start, end) || "Text";
    textarea.value = value.slice(0, start) + before + selected + after + value.slice(end);
    textarea.focus();
  }

  function insertAtCursor(valueToInsert) {
    var textarea = form.elements.event_description;
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var value = textarea.value;
    textarea.value = value.slice(0, start) + valueToInsert + value.slice(end);
    textarea.focus();
  }

  function readFileAsBase64(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var result = String(reader.result || "");
        var commaIndex = result.indexOf(",");
        resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function insertPhoto(file) {
    return readFileAsBase64(file).then(function (base64Photo) {
      var safeFileName = file.name.replace(/[^A-Za-z0-9._-]/g, "_") || "event_photo";
      return requestJson("http://localhost:9992/api/photo/create/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ photo_description: safeFileName, photo: base64Photo })
      });
    }).then(function (data) {
      if (!data.photo_url) {
        showToast("Photo upload did not return a URL");
        return;
      }
      insertAtCursor('<img src="' + data.photo_url + '" alt="">');
      var image = createElement("img", "", "");
      image.src = data.photo_url;
      image.alt = "";
      photoPreview.appendChild(image);
      showToast("Photo inserted");
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-close-modal]"), function (button) {
    button.addEventListener("click", closeEventForm);
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-format]"), function (button) {
    button.addEventListener("click", function () {
      var format = button.getAttribute("data-format");
      if (format === "h2") {
        wrapSelection("<h2>", "</h2>");
      } else if (format === "bold") {
        wrapSelection("<strong>", "</strong>");
      } else if (format === "italic") {
        wrapSelection("<em>", "</em>");
      }
    });
  });

  if (showCreateFormButton) {
    showCreateFormButton.addEventListener("click", function () {
      openEventForm({});
    });
  }

  if (form) {
    form.addEventListener("submit", submitEvent);
  }

  if (insertPhotoButton && photoInput) {
    insertPhotoButton.addEventListener("click", function () {
      photoInput.value = "";
      photoInput.click();
    });
    photoInput.addEventListener("change", function () {
      var file = photoInput.files && photoInput.files[0];
      if (file) {
        insertPhoto(file).catch(function () {
          showToast("Could not insert photo");
        });
      }
    });
  }

  if (eventsList) {
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
