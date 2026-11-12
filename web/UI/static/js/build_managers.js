(function () {
  var managersList = document.getElementById("managers-list");
  var showCreateFormButton = document.getElementById("show-create-form");
  var createManagerForm = document.getElementById("create-manager-form");
  var photoFileInput = document.getElementById("photo-file-input");
  var toast = document.getElementById("toast");
  var pendingPhotoManager = null;
  var toastTimer = null;

  var defaultManagerIcon = "/static/icons/default_pict.png";

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
    toast.textContent = message || "Transaction finished";
    toast.classList.add("visible");
    toastTimer = window.setTimeout(function () {
      toast.classList.remove("visible");
    }, 3200);
  }

  function buildMessage(data, fallback) {
    if (!data || typeof data !== "object") {
      return fallback;
    }

    if (data.message_title && data.message_content) {
      return data.message_title + ": " + data.message_content;
    }

    if (data.message_title) {
      return data.message_title;
    }

    if (data.message_content) {
      return data.message_content;
    }

    return fallback;
  }

  function isSuccessfulMessage(data) {
    var title = data && data.message_title ? data.message_title.toLowerCase() : "";
    return title.indexOf("transaction successful") !== -1 || title.indexOf("transaction successfull") !== -1;
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
        if (!body) {
          return {};
        }

        return JSON.parse(body);
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

  function makeManagerPayload(manager) {
    return {
      manager_login: manager.manager_login || "",
      manager_firstname: manager.manager_firstname || "",
      manager_lastname: manager.manager_lastname || "",
      manager_email: manager.manager_email || "",
      manager_iconurl: manager.manager_iconurl || defaultManagerIcon
    };
  }

  function managerPhotoUrl(manager) {
    var url = manager.manager_iconurl || defaultManagerIcon;

    if (url.indexOf("http://") === 0 || url.indexOf("https://") === 0) {
      return url;
    }

    return "http://localhost:9992" + url;
  }

  function createDataPill(label, value) {
    var pill = createElement("div", "data-pill", "");
    var strong = createElement("strong", "", label);
    var span = createElement("span", "", value || "Not set");

    pill.appendChild(strong);
    pill.appendChild(span);
    return pill;
  }

  function createUpdateForm(manager) {
    var form = createElement("form", "manager-form", "");
    var title = createElement("h2", "", "Update manager");
    var loginField = createField("Login", "manager_login", "text", manager.manager_login);
    var firstNameField = createField("First name", "manager_firstname", "text", manager.manager_firstname);
    var lastNameField = createField("Last name", "manager_lastname", "text", manager.manager_lastname);
    var emailField = createField("Email", "manager_email", "email", manager.manager_email);
    var actions = createElement("div", "form-actions", "");
    var submitButton = createElement("button", "small-action", "Save");
    var cancelButton = createElement("button", "small-action subtle", "Cancel");

    submitButton.type = "submit";
    cancelButton.type = "button";

    actions.appendChild(submitButton);
    actions.appendChild(cancelButton);

    form.appendChild(title);
    form.appendChild(loginField);
    form.appendChild(firstNameField);
    form.appendChild(lastNameField);
    form.appendChild(emailField);
    form.appendChild(actions);

    cancelButton.addEventListener("click", function () {
      form.remove();
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      updateManager(manager.manager_login, {
        manager_login: form.elements.manager_login.value.trim(),
        manager_firstname: form.elements.manager_firstname.value.trim(),
        manager_lastname: form.elements.manager_lastname.value.trim(),
        manager_email: form.elements.manager_email.value.trim(),
        manager_iconurl: manager.manager_iconurl || defaultManagerIcon
      });
    });

    return form;
  }

  function createField(labelText, name, type, value) {
    var label = document.createElement("label");
    var input = document.createElement("input");

    label.appendChild(document.createTextNode(labelText));
    input.name = name;
    input.type = type;
    input.required = true;
    input.value = value || "";
    label.appendChild(input);

    return label;
  }

  function createActionButton(text, className) {
    var button = createElement("button", "card-action " + (className || ""), text);
    button.type = "button";
    return button;
  }

  function passwordIsValid(password) {
    return password.length > 8 && /[0-9]/.test(password) && /[A-Za-z]/.test(password);
  }

  function sha256Hex(value) {
    var encoder = new TextEncoder();

    return window.crypto.subtle.digest("SHA-256", encoder.encode(value)).then(function (hashBuffer) {
      return Array.prototype.map.call(new Uint8Array(hashBuffer), function (byte) {
        return byte.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function setPasswordHashCookie(passwordHash) {
    document.cookie = "password-hash=" + encodeURIComponent(passwordHash) + "; Path=/; SameSite=Lax";
  }

  function createManagerCard(manager) {
    var card = createElement("article", "manager-card", "");
    var image = createElement("img", "manager-photo", "");
    var info = createElement("div", "manager-info", "");
    var name = createElement("h2", "manager-name", ((manager.manager_firstname || "") + " " + (manager.manager_lastname || "")).trim() || manager.manager_login || "Manager");
    var data = createElement("div", "manager-data", "");
    var actions = createElement("div", "manager-card-actions", "");
    var updateButton = createActionButton("Update info", "");
    var deleteButton = createActionButton("Delete manager", "danger");
    var photoButton = createActionButton("Change photo", "");

    image.src = managerPhotoUrl(manager);
    image.alt = "Manager icon for " + (manager.manager_login || "manager");

    data.appendChild(createDataPill("Login", manager.manager_login));
    data.appendChild(createDataPill("First name", manager.manager_firstname));
    data.appendChild(createDataPill("Last name", manager.manager_lastname));
    data.appendChild(createDataPill("Email", manager.manager_email));
    data.appendChild(createDataPill("Icon URL", manager.manager_iconurl));

    info.appendChild(name);
    info.appendChild(data);

    actions.appendChild(updateButton);
    actions.appendChild(deleteButton);
    actions.appendChild(photoButton);

    card.appendChild(image);
    card.appendChild(info);
    card.appendChild(actions);

    updateButton.addEventListener("click", function () {
      var existingForm = card.querySelector(".manager-form");
      if (existingForm) {
        existingForm.remove();
        return;
      }
      card.appendChild(createUpdateForm(manager));
    });

    deleteButton.addEventListener("click", function () {
      deleteManager(manager);
    });

    photoButton.addEventListener("click", function () {
      pendingPhotoManager = manager;
      photoFileInput.value = "";
      photoFileInput.click();
    });

    return card;
  }

  function renderManagers(managers) {
    clearElement(managersList);

    if (!Array.isArray(managers) || managers.length === 0) {
      managersList.appendChild(createElement("p", "muted", "No managers found."));
      return;
    }

    managers.forEach(function (manager) {
      managersList.appendChild(createManagerCard(makeManagerPayload(manager)));
    });
  }

  function renderManagersError() {
    clearElement(managersList);
    managersList.appendChild(createElement("p", "error-text", "Could not load managers."));
  }

  function loadManagers() {
    return requestJson("http://localhost:9992/api/manager/list/?target=all", {
      method: "GET",
      credentials: "same-origin"
    })
      .then(renderManagers)
      .catch(function () {
        renderManagersError();
      });
  }

  function submitManager(url, method, payload, successFallback) {
    return requestJson(url, {
      method: method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }).then(function (data) {
      showToast(buildMessage(data, successFallback));

      if (isSuccessfulMessage(data) || !data.message_title) {
        return loadManagers().then(function () {
          return true;
        });
      }

      return false;
    });
  }

  function updateManager(originalLogin, payload) {
    return submitManager(
      "http://localhost:9992/api/manager/update/?mng_login=" + encodeURIComponent(originalLogin),
      "PUT",
      payload,
      "Manager data updated"
    );
  }

  function deleteManager(manager) {
    return requestJson("http://localhost:9992/api/manager/erase/?mng_email=" + encodeURIComponent(manager.manager_email), {
      method: "DELETE",
      credentials: "same-origin"
    }).then(function (data) {
      showToast(buildMessage(data, "Manager deleted"));

      if (isSuccessfulMessage(data)) {
        return loadManagers();
      }

      return null;
    });
  }

  function createManagerFromForm(event) {
    var password = createManagerForm.elements.manager_password.value;
    var repeatPassword = createManagerForm.elements.manager_repeat_password.value;
    var payload = {
      manager_login: createManagerForm.elements.manager_login.value.trim(),
      manager_firstname: createManagerForm.elements.manager_firstname.value.trim(),
      manager_lastname: createManagerForm.elements.manager_lastname.value.trim(),
      manager_email: createManagerForm.elements.manager_email.value.trim(),
      manager_iconurl: defaultManagerIcon
    };

    event.preventDefault();

    if (password !== repeatPassword) {
      showToast("Passwords do not match");
      return;
    }

    if (!passwordIsValid(password)) {
      showToast("Password must be longer than 8 characters and include at least one digit and one English letter");
      return;
    }

    sha256Hex(password).then(function (passwordHash) {
      setPasswordHashCookie(passwordHash);
      return submitManager("http://localhost:9992/api/manager/create/", "POST", payload, "New manager added");
    })
      .then(function (created) {
        if (created) {
          createManagerForm.reset();
          createManagerForm.classList.add("hidden");
        }
      })
      .catch(function () {
        showToast("Could not create manager");
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

  function uploadPhotoForManager(file, manager) {
    return readFileAsBase64(file).then(function (base64Photo) {
      var safeFileName = file.name.replace(/[^A-Za-z0-9._-]/g, "_") || "manager_photo";

      return requestJson("http://localhost:9992/api/photo/create/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          photo_description: safeFileName,
          photo: base64Photo
        })
      });
    }).then(function (data) {
      if (!data.photo_url) {
        showToast(buildMessage(data, "Photo upload did not return a URL"));
        return null;
      }

      return updateManager(manager.manager_login, {
        manager_login: manager.manager_login,
        manager_firstname: manager.manager_firstname,
        manager_lastname: manager.manager_lastname,
        manager_email: manager.manager_email,
        manager_iconurl: data.photo_url
      });
    });
  }

  if (showCreateFormButton && createManagerForm) {
    showCreateFormButton.addEventListener("click", function () {
      createManagerForm.classList.toggle("hidden");
    });

    createManagerForm.addEventListener("submit", createManagerFromForm);

    Array.prototype.forEach.call(createManagerForm.querySelectorAll("[data-close-create]"), function (button) {
      button.addEventListener("click", function () {
        createManagerForm.classList.add("hidden");
      });
    });
  }

  if (photoFileInput) {
    photoFileInput.addEventListener("change", function () {
      var file = photoFileInput.files && photoFileInput.files[0];

      if (!file || !pendingPhotoManager) {
        return;
      }

      uploadPhotoForManager(file, pendingPhotoManager)
        .catch(function () {
          showToast("Could not change manager photo");
        })
        .then(function () {
          pendingPhotoManager = null;
        });
    });
  }

  if (managersList) {
    loadManagers();
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
