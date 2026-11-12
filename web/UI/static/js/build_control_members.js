(function () {
  var membersList = document.getElementById("members-list");
  var showCreateFormButton = document.getElementById("show-create-form");
  var createMemberForm = document.getElementById("create-member-form");
  var photoFileInput = document.getElementById("photo-file-input");
  var toast = document.getElementById("toast");
  var pendingPhotoMember = null;
  var toastTimer = null;
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
    return fetch(url, options).then(function (response) {
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

  function memberPhotoUrl(member) {
    var url = member.member_icon || defaultMemberIcon;
    if (url.indexOf("http://") === 0 || url.indexOf("https://") === 0) {
      return url;
    }
    return "http://localhost:9992" + url;
  }

  function dateForInput(value) {
    if (typeof value === "string" && value.length >= 10 && value.slice(0, 10) !== "0001-01-01") {
      return value.slice(0, 10);
    }
    return "";
  }

  function dateForPayload(value) {
    return value ? value + "T00:00:00Z" : "0001-01-01T00:00:00Z";
  }

  function displayDate(value) {
    var date = dateForInput(value);
    return date || "Not set";
  }

  function makeMemberPayload(member) {
    return {
      member_id: member.member_id || 0,
      first_name: member.first_name || "",
      last_name: member.last_name || "",
      current_year_of_study: Number(member.current_year_of_study || 0),
      currently_studying: member.currently_studying || "",
      degree: member.degree || "",
      join_date: member.join_date || "0001-01-01T00:00:00Z",
      additional_description: member.additional_description || "",
      member_icon: member.member_icon || defaultMemberIcon,
      email: member.email || ""
    };
  }

  function createPill(label, value) {
    var pill = createElement("div", "data-pill", "");
    pill.appendChild(createElement("strong", "", label));
    pill.appendChild(createElement("span", "", value || "Not set"));
    return pill;
  }

  function createField(labelText, name, type, value, required) {
    var label = document.createElement("label");
    var input = document.createElement("input");
    label.appendChild(document.createTextNode(labelText));
    input.name = name;
    input.type = type;
    input.value = value || "";
    input.required = required !== false;
    if (type === "number") {
      input.min = "0";
      input.step = "1";
    }
    label.appendChild(input);
    return label;
  }

  function createTextArea(labelText, name, value) {
    var label = document.createElement("label");
    var textarea = document.createElement("textarea");
    label.appendChild(document.createTextNode(labelText));
    textarea.name = name;
    textarea.rows = 4;
    textarea.value = value || "";
    label.appendChild(textarea);
    return label;
  }

  function payloadFromForm(form, memberIcon) {
    return {
      first_name: form.elements.first_name.value.trim(),
      last_name: form.elements.last_name.value.trim(),
      current_year_of_study: Number(form.elements.current_year_of_study.value || 0),
      currently_studying: form.elements.currently_studying.value.trim(),
      degree: form.elements.degree.value.trim(),
      join_date: dateForPayload(form.elements.join_date.value),
      additional_description: form.elements.additional_description.value.trim(),
      member_icon: memberIcon || defaultMemberIcon,
      email: form.elements.email.value.trim()
    };
  }

  function createActionButton(text, className) {
    var button = createElement("button", "card-action " + (className || ""), text);
    button.type = "button";
    return button;
  }

  function createUpdateForm(member) {
    var form = createElement("form", "member-form", "");
    var actions = createElement("div", "form-actions", "");
    var submitButton = createElement("button", "small-action primary-tool", "Save");
    var cancelButton = createElement("button", "small-action subtle", "Cancel");

    submitButton.type = "submit";
    cancelButton.type = "button";
    actions.appendChild(submitButton);
    actions.appendChild(cancelButton);

    form.appendChild(createElement("h2", "", "Update member"));
    form.appendChild(createField("First name", "first_name", "text", member.first_name));
    form.appendChild(createField("Last name", "last_name", "text", member.last_name));
    form.appendChild(createField("Current year of study", "current_year_of_study", "number", String(member.current_year_of_study || 0)));
    form.appendChild(createField("Currently studying", "currently_studying", "text", member.currently_studying));
    form.appendChild(createField("Degree", "degree", "text", member.degree));
    form.appendChild(createField("Join date", "join_date", "date", dateForInput(member.join_date)));
    form.appendChild(createField("Email", "email", "email", member.email));
    form.appendChild(createTextArea("Additional description", "additional_description", member.additional_description));
    form.appendChild(actions);

    cancelButton.addEventListener("click", function () {
      form.remove();
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      updateMember(member.email, payloadFromForm(form, member.member_icon));
    });

    return form;
  }

  function createMemberCard(member) {
    var card = createElement("article", "member-card", "");
    var image = createElement("img", "member-photo", "");
    var info = createElement("div", "member-info", "");
    var name = createElement("h2", "member-name", ((member.first_name || "") + " " + (member.last_name || "")).trim() || member.email || "Member");
    var data = createElement("div", "member-data", "");
    var actions = createElement("div", "member-card-actions", "");
    var photoButton = createActionButton("Update photo", "");
    var updateButton = createActionButton("Update info", "");
    var deleteButton = createActionButton("Delete member", "danger");

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
    actions.appendChild(photoButton);
    actions.appendChild(updateButton);
    actions.appendChild(deleteButton);

    card.appendChild(image);
    card.appendChild(info);
    card.appendChild(actions);

    photoButton.addEventListener("click", function () {
      pendingPhotoMember = member;
      photoFileInput.value = "";
      photoFileInput.click();
    });

    updateButton.addEventListener("click", function () {
      var existingForm = card.querySelector(".member-form");
      if (existingForm) {
        existingForm.remove();
        return;
      }
      card.appendChild(createUpdateForm(member));
    });

    deleteButton.addEventListener("click", function () {
      deleteMember(member.member_id);
    });

    return card;
  }

  function renderMembers(members) {
    clearElement(membersList);
    if (!Array.isArray(members) || members.length === 0) {
      membersList.appendChild(createElement("p", "muted", "No members found."));
      return;
    }
    members.forEach(function (member) {
      membersList.appendChild(createMemberCard(makeMemberPayload(member)));
    });
  }

  function loadMembers() {
    return requestJson("http://localhost:9992/api/members/list/?target=all", {
      method: "GET",
      credentials: "same-origin"
    }).then(renderMembers).catch(function () {
      clearElement(membersList);
      membersList.appendChild(createElement("p", "error-text", "Could not load members."));
    });
  }

  function submitMember(url, method, payload) {
    return requestJson(url, {
      method: method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function () {
      showToast("Transaction Successful");
      return loadMembers();
    });
  }

  function updateMember(originalEmail, payload) {
    return submitMember(
      "http://localhost:9992/api/members/update/?member_email=" + encodeURIComponent(originalEmail),
      "PUT",
      payload
    );
  }

  function deleteMember(memberID) {
    return requestJson("http://localhost:9992/api/members/erase/?member_id=" + encodeURIComponent(memberID), {
      method: "DELETE",
      credentials: "same-origin"
    }).then(function () {
      showToast("Transaction Successful");
      return loadMembers();
    }).catch(function () {
      showToast("Could not delete member");
    });
  }

  function createMemberFromForm(event) {
    event.preventDefault();
    submitMember(
      "http://localhost:9992/api/members/create/",
      "POST",
      payloadFromForm(createMemberForm, defaultMemberIcon)
    ).then(function () {
      createMemberForm.reset();
      createMemberForm.classList.add("hidden");
    }).catch(function () {
      showToast("Could not create member");
    });
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

  function uploadPhotoForMember(file, member) {
    return readFileAsBase64(file).then(function (base64Photo) {
      var safeFileName = file.name.replace(/[^A-Za-z0-9._-]/g, "_") || "member_photo";
      return requestJson("http://localhost:9992/api/photo/create/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          photo_description: safeFileName,
          photo: base64Photo
        })
      });
    }).then(function (data) {
      if (!data.photo_url) {
        showToast("Photo upload did not return a URL");
        return null;
      }
      return updateMember(member.email, {
        first_name: member.first_name,
        last_name: member.last_name,
        current_year_of_study: member.current_year_of_study,
        currently_studying: member.currently_studying,
        degree: member.degree,
        join_date: member.join_date,
        additional_description: member.additional_description,
        member_icon: data.photo_url,
        email: member.email
      });
    });
  }

  if (showCreateFormButton && createMemberForm) {
    showCreateFormButton.addEventListener("click", function () {
      createMemberForm.classList.toggle("hidden");
    });

    createMemberForm.addEventListener("submit", createMemberFromForm);

    Array.prototype.forEach.call(createMemberForm.querySelectorAll("[data-close-create]"), function (button) {
      button.addEventListener("click", function () {
        createMemberForm.classList.add("hidden");
      });
    });
  }

  if (photoFileInput) {
    photoFileInput.addEventListener("change", function () {
      var file = photoFileInput.files && photoFileInput.files[0];
      if (!file || !pendingPhotoMember) {
        return;
      }
      uploadPhotoForMember(file, pendingPhotoMember).catch(function () {
        showToast("Could not update member photo");
      }).then(function () {
        pendingPhotoMember = null;
      });
    });
  }

  if (membersList) {
    loadMembers();
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
