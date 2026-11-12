(function () {
  var membersList = document.getElementById("members-list");
  var defaultMemberIcon = "/static/icons/default_pict.png";

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
    return fetch(url, {
      method: "GET",
      credentials: "same-origin"
    }).then(function (response) {
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

  function memberPhotoUrl(member) {
    var url = member.member_icon || defaultMemberIcon;
    if (url.indexOf("http://") === 0 || url.indexOf("https://") === 0) {
      return url;
    }
    return "http://localhost:9992" + url;
  }

  function displayDate(value) {
    if (typeof value === "string" && value.length >= 10 && value.slice(0, 10) !== "0001-01-01") {
      return value.slice(0, 10);
    }
    return "Not set";
  }

  function createPill(label, value) {
    var pill = createElement("div", "data-pill", "");
    pill.appendChild(createElement("strong", "", label));
    pill.appendChild(createElement("span", "", value || "Not set"));
    return pill;
  }

  function createMemberCard(member) {
    var card = createElement("article", "member-card", "");
    var image = createElement("img", "member-photo", "");
    var info = createElement("div", "member-info", "");
    var name = createElement("h2", "member-name", ((member.first_name || "") + " " + (member.last_name || "")).trim() || member.email || "Member");
    var data = createElement("div", "member-data", "");

    image.src = memberPhotoUrl(member);
    image.alt = "Member icon for " + (((member.first_name || "") + " " + (member.last_name || "")).trim() || "member");

    data.appendChild(createPill("Email", member.email));
    data.appendChild(createPill("Degree", member.degree));
    data.appendChild(createPill("Current year", String(member.current_year_of_study || 0)));
    data.appendChild(createPill("Currently studying", member.currently_studying));
    data.appendChild(createPill("Joined", displayDate(member.join_date)));
    data.appendChild(createPill("Description", member.additional_description));

    info.appendChild(name);
    info.appendChild(data);
    card.appendChild(image);
    card.appendChild(info);
    return card;
  }

  function renderMembers(members) {
    clearElement(membersList);
    if (!Array.isArray(members) || members.length === 0) {
      membersList.appendChild(createElement("p", "muted", "No members found."));
      return;
    }
    members.forEach(function (member) {
      membersList.appendChild(createMemberCard(member));
    });
  }

  function loadMembers() {
    return requestJson("http://localhost:9992/api/members/list/?target=all").then(renderMembers).catch(function () {
      clearElement(membersList);
      membersList.appendChild(createElement("p", "error-text", "Could not load members."));
    });
  }

  if (membersList) {
    loadMembers();
  }
}());
