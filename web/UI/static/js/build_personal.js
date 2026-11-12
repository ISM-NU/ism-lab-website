(function () {
  var profileForm = document.getElementById("profile-form");
  var fieldsRoot = document.getElementById("profile-fields");
  var passwordForm = document.getElementById("password-form");
  var roleChip = document.getElementById("role-chip");
  var toast = document.getElementById("toast");
  var toastTimer = null;
  var currentUser = null;

  function replaceDocument(html, nextUrl) {
    if (window.history && window.history.pushState) {
      window.history.pushState({}, "", nextUrl || window.location.href);
    }
    document.open();
    document.write(html);
    document.close();
  }

  function requestJson(url, options) {
    return fetch("http://localhost:9992" + url, options || { method: "GET", credentials: "same-origin" }).then(function (response) {
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

  function showToast(message) {
    if (!toast) {
      return;
    }
    window.clearTimeout(toastTimer);
    toast.textContent = message || "Transaction Successful";
    toast.classList.add("visible");
    toastTimer = window.setTimeout(function () { toast.classList.remove("visible"); }, 2800);
  }

  function clear(element) {
    while (element && element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function bytesToHex(buffer) {
    var bytes = new Uint8Array(buffer);
    var hex = [];
    var index;

    for (index = 0; index < bytes.length; index += 1) {
      hex.push(bytes[index].toString(16).padStart(2, "0"));
    }

    return hex.join("");
  }

  function sha256Hex(value) {
    if (!window.crypto || !window.crypto.subtle || !window.TextEncoder) {
      return Promise.reject(new Error("Secure password hashing is not available in this browser."));
    }

    return window.crypto.subtle
      .digest("SHA-256", new TextEncoder().encode(value))
      .then(bytesToHex);
  }

  function createField(labelText, name, type, value) {
    var label = document.createElement("label");
    var input = document.createElement("input");
    label.textContent = labelText;
    input.name = name;
    input.type = type || "text";
    input.required = true;
    input.value = value || "";
    label.appendChild(input);
    return label;
  }

  function createStaticField(labelText, value) {
    var label = document.createElement("label");
    var text = document.createElement("span");
    label.textContent = labelText;
    text.className = "account-static-value";
    text.textContent = value || "";
    label.appendChild(text);
    return label;
  }

  function renderProfile(user) {
    clear(fieldsRoot);
    if (roleChip) {
      roleChip.textContent = user.role + ": " + user.login;
    }
    fieldsRoot.appendChild(createStaticField("Login", user.login));
    fieldsRoot.appendChild(createField("First name", "first_name", "text", user.firstName));
    fieldsRoot.appendChild(createField("Last name", "last_name", "text", user.lastName));
    fieldsRoot.appendChild(createField("Email", "email", "email", user.email));
    fieldsRoot.appendChild(createField("Icon URL", "icon_url", "text", user.iconUrl));
  }

  function normalizeAdmin(data, login) {
    return {
      role: "Admin",
      login: data.admin_login || login,
      firstName: data.admin_firstname || "",
      lastName: data.admin_lastname || "",
      email: data.admin_email || "",
      iconUrl: data.admin_iconurl || ""
    };
  }

  function normalizeManager(data, login) {
    var manager = Array.isArray(data) ? data[0] : data;
    manager = manager || {};
    return {
      role: "Manager",
      login: manager.manager_login || login,
      firstName: manager.manager_firstname || "",
      lastName: manager.manager_lastname || "",
      email: manager.manager_email || "",
      iconUrl: manager.manager_iconurl || ""
    };
  }

  function activeUser() {
    return requestJson("/api/sessions/active/").then(function (users) {
      var selected = null;
      if (Array.isArray(users)) {
        users.some(function (user) {
          if (user.current_session) {
            selected = user;
            return true;
          }
          return false;
        });
        if (!selected && users.length === 1) {
          selected = users[0];
        }
      }
      if (!selected) {
        throw new Error("Current session was not found");
      }
      return selected;
    });
  }

  function loadProfile() {
    return activeUser().then(function (session) {
      var login = session.user_login;
      var role = String(session.user_role || "").toLowerCase();
      if (role.indexOf("admin") >= 0) {
        return requestJson("/api/admin/list/?user_login=" + encodeURIComponent(login)).then(function (data) {
          currentUser = normalizeAdmin(data, login);
          renderProfile(currentUser);
        });
      }
      return requestJson("/api/manager/list/?mng_login=" + encodeURIComponent(login)).then(function (data) {
        currentUser = normalizeManager(data, login);
        renderProfile(currentUser);
      });
    }).catch(function () {
      clear(fieldsRoot);
      fieldsRoot.appendChild(document.createTextNode("Could not load account information."));
    });
  }

  function updateProfile(event) {
    event.preventDefault();
    if (!currentUser) {
      return;
    }
    var login = currentUser.login;
    var firstName = profileForm.elements.first_name.value.trim();
    var lastName = profileForm.elements.last_name.value.trim();
    var email = profileForm.elements.email.value.trim();
    var iconUrl = profileForm.elements.icon_url.value.trim();
    var isAdmin = currentUser.role.toLowerCase().indexOf("admin") >= 0;
    var url = isAdmin ? "/api/admin/update/" : "/api/manager/update/?mng_login=" + encodeURIComponent(currentUser.login);
    var payload = isAdmin ? {
      admin_login: login,
      admin_firstname: firstName,
      admin_lastname: lastName,
      admin_email: email,
      admin_iconurl: iconUrl
    } : {
      manager_login: login,
      manager_firstname: firstName,
      manager_lastname: lastName,
      manager_email: email,
      manager_iconurl: iconUrl
    };
    requestJson(url, {
      method: "PUT",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function () {
      showToast("Transaction Successful");
      loadProfile();
    }).catch(function () { showToast("Could not update account"); });
  }

  function updatePassword(event) {
    event.preventDefault();
    var password = passwordForm.elements.password.value;
    var repeat = passwordForm.elements.repeat_password.value;
    if (password !== repeat) {
      showToast("Passwords do not match");
      return;
    }
    sha256Hex(password).then(function (passwordHash) {
      document.cookie = "password-hash=" + encodeURIComponent(passwordHash) + "; Path=/; SameSite=Lax";
      return requestJson("/api/password/update/", {
        method: "PUT",
        credentials: "same-origin"
      });
    }).then(function () {
      document.cookie = "password-hash=; Path=/; Max-Age=0; SameSite=Lax";
      passwordForm.reset();
      showToast("Transaction Successful");
    }).catch(function () {
      document.cookie = "password-hash=; Path=/; Max-Age=0; SameSite=Lax";
      showToast("Could not update password");
    });
  }

  if (profileForm) {
    profileForm.addEventListener("submit", updateProfile);
  }
  if (passwordForm) {
    passwordForm.addEventListener("submit", updatePassword);
  }
  loadProfile();
}());
