(function () {
  var activityFeed = document.getElementById("activity-feed");
  var activeUsersRoot = document.getElementById("active-users");

  function clearElement(element) {
    if (!element) {
      return;
    }

    while (element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function requestJson(url) {
    return fetch(url, {
      method: "GET",
      credentials: "same-origin"
    }).then(function (response) {
      if (response.status >= 300) {
        return response.text().then(function (html) {
          document.open();
          document.write(html);
          document.close();
          throw new Error("Request failed");
        });
      }

      return response.json();
    });
  }

  function parseDateParts(dateValue, timeValue) {
    var date = dateValue ? new Date(dateValue) : null;
    var time = timeValue ? new Date(timeValue) : null;
    var year = date && !Number.isNaN(date.getTime()) ? date.getFullYear() : 1;
    var month = date && !Number.isNaN(date.getTime()) ? date.getMonth() : 0;
    var day = date && !Number.isNaN(date.getTime()) ? date.getDate() : 1;
    var hours = time && !Number.isNaN(time.getTime()) ? time.getHours() : 0;
    var minutes = time && !Number.isNaN(time.getTime()) ? time.getMinutes() : 0;
    var seconds = time && !Number.isNaN(time.getTime()) ? time.getSeconds() : 0;

    return new Date(year, month, day, hours, minutes, seconds);
  }

  function formatDateTime(dateValue, timeValue) {
    var dateTime = parseDateParts(dateValue, timeValue);
    var valid = !Number.isNaN(dateTime.getTime()) && dateTime.getFullYear() > 1;

    if (!valid) {
      return "Date not set";
    }

    return dateTime.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
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

  function createActivityCard(item) {
    var card = createElement("article", "activity-card", "");
    var kind = createElement("span", "activity-kind " + item.kindClass, item.kind);
    var title = createElement("h2", "", item.title);
    var description = createElement("p", "", item.description);
    var metaRow = createElement("div", "meta-row", "");
    var announced = createElement("span", "date-pill", "Announced: " + formatDateTime(item.announcementDate, item.announcementTime));

    card.appendChild(kind);
    card.appendChild(title);

    if (item.description) {
      card.appendChild(description);
    }

    metaRow.appendChild(announced);

    if (item.extraMeta) {
      metaRow.appendChild(createElement("span", "date-pill", item.extraMeta));
    }

    card.appendChild(metaRow);
    return card;
  }

  function normalizeAnnouncements(announcements) {
    if (!Array.isArray(announcements)) {
      return [];
    }

    return announcements.map(function (announcement) {
      return {
        kind: "Announcement",
        kindClass: "announcement",
        title: announcement.announcement_title || "Untitled announcement",
        description: announcement.announcement_description || "",
        announcementDate: announcement.announcement_date,
        announcementTime: announcement.announcement_time,
        extraMeta: ""
      };
    });
  }

  function normalizeEvents(events) {
    if (!Array.isArray(events)) {
      return [];
    }

    return events.map(function (event) {
      return {
        kind: "Event",
        kindClass: "event",
        title: event.event_title || "Untitled event",
        description: event.event_description || "",
        announcementDate: event.announcement_date,
        announcementTime: event.announcement_time,
        extraMeta: "Starts: " + formatDateTime(event.event_start_date, event.event_start_time)
      };
    });
  }

  function renderActivity(announcements, events) {
    var items = normalizeAnnouncements(announcements).concat(normalizeEvents(events));

    items.sort(function (left, right) {
      return parseDateParts(right.announcementDate, right.announcementTime).getTime() -
        parseDateParts(left.announcementDate, left.announcementTime).getTime();
    });

    clearElement(activityFeed);

    if (!items.length) {
      activityFeed.appendChild(createActivityCard({
        kind: "Empty",
        kindClass: "",
        title: "No announcements or events found",
        description: "",
        announcementDate: "",
        announcementTime: "",
        extraMeta: ""
      }));
      return;
    }

    items.forEach(function (item) {
      activityFeed.appendChild(createActivityCard(item));
    });
  }

  function renderUsers(users) {
    clearElement(activeUsersRoot);

    if (!Array.isArray(users) || users.length === 0) {
      activeUsersRoot.appendChild(createElement("p", "muted", "No active users found"));
      return;
    }

    users.forEach(function (user) {
      var card = createElement("article", "user-card", "");
      var login = createElement("strong", "", user.user_login || "Unknown user");
      var role = createElement("span", "role-pill", user.user_role || "Role not set");

      card.appendChild(login);
      card.appendChild(role);
      activeUsersRoot.appendChild(card);
    });
  }

  function renderActivityError() {
    clearElement(activityFeed);
    activityFeed.appendChild(createActivityCard({
      kind: "Error",
      kindClass: "",
      title: "Could not load lab activity",
      description: "Refresh the page or sign in again.",
      announcementDate: "",
      announcementTime: "",
      extraMeta: ""
    }));
  }

  function renderUsersError() {
    clearElement(activeUsersRoot);
    activeUsersRoot.appendChild(createElement("p", "error-text", "Could not load active users."));
  }

  function loadActivity() {
    return Promise.all([
      requestJson("http://localhost:9992/api/announcements/list/?target=all"),
      requestJson("http://localhost:9992/api/events/list/?target=all")
    ])
      .then(function (responses) {
        renderActivity(responses[0], responses[1]);
      })
      .catch(function () {
        renderActivityError();
      });
  }

  function loadActiveUsers() {
    return requestJson("http://localhost:9992/api/sessions/active/")
      .then(renderUsers)
      .catch(function () {
        renderUsersError();
      });
  }

  if (activityFeed) {
    loadActivity();
  }

  if (activeUsersRoot) {
    loadActiveUsers();
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

  function loadLoginPage() {
    return fetch("http://localhost:9992/control/panel/login/", {
      method: "GET",
      credentials: "same-origin"
    }).then(function (response) {
      return response.text().then(function (html) {
        replaceDocument(html, "http://localhost:9992/control/panel/login/");
      });
    });
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
    if (logoutButton) {
      logoutButton.disabled = true;
      logoutButton.textContent = "Logging out";
    }

    fetch("http://localhost:9992/api/sessions/logout/", {
      method: "DELETE",
      credentials: "same-origin"
    })
      .then(function (response) {
        deleteSessionCookies();

        if (response.status >= 300) {
          return response.text().then(function (html) {
            replaceDocument(html, window.location.href);
          });
        }

        return loadLoginPage();
      })
      .catch(function () {
        isLoggingOut = false;
        if (logoutButton) {
          logoutButton.disabled = false;
          logoutButton.textContent = "Logout";
        }
      });
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }
}());
