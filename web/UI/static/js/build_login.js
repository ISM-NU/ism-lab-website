(function () {
  var form = document.getElementById("login-form");
  var loginInput = document.getElementById("user-login");
  var passwordInput = document.getElementById("user-password");
  var submitButton = document.getElementById("login-submit");
  var message = document.getElementById("login-message");
  var isSigningIn = false;

  function setMessage(text, kind) {
    if (!message) {
      return;
    }
    message.textContent = text;
    message.className = "form-message" + (kind ? " " + kind : "");
  }

  function setCookie(name, value, maxAgeSeconds) {
    document.cookie = [
      encodeURIComponent(name) + "=" + encodeURIComponent(value),
      "path=/",
      "max-age=" + String(maxAgeSeconds),
      "samesite=lax"
    ].join("; ");
  }

  function clearCookie(name) {
    document.cookie = encodeURIComponent(name) + "=; path=/; max-age=0; samesite=lax";
  }

  function bytesToHex(buffer) {
    var bytes = new Uint8Array(buffer);
    var hex = [];

    for (var index = 0; index < bytes.length; index += 1) {
      hex.push(bytes[index].toString(16).padStart(2, "0"));
    }

    return hex.join("");
  }

  function sha256(value) {
    if (!window.crypto || !window.crypto.subtle || !window.TextEncoder) {
      return Promise.reject(new Error("Secure password hashing is not available in this browser."));
    }

    return window.crypto.subtle
      .digest("SHA-256", new TextEncoder().encode(value))
      .then(bytesToHex);
  }

  function replaceDocument(html, nextUrl) {
    if (window.history && window.history.pushState) {
      window.history.pushState({}, "", nextUrl);
    }
    document.open();
    document.write(html);
    document.close();
  }

  function loadPanelPage() {
    return fetch("http://localhost:9992/control/panel/", {
      method: "GET",
      credentials: "same-origin"
    }).then(function (response) {
      return response.text().then(function (html) {
        replaceDocument(html, "http://localhost:9992/control/panel/");
      });
    });
  }

  window.SignInTheUser = function SignInTheUser(event) {
    if (event && event.preventDefault) {
      event.preventDefault();
    }

    if (isSigningIn) {
      return false;
    }

    var login = loginInput ? loginInput.value.trim() : "";
    var password = passwordInput ? passwordInput.value : "";

    if (!login || !password) {
      setMessage("Login and password are required.", "error");
      return false;
    }

    isSigningIn = true;
    if (submitButton) {
      submitButton.disabled = true;
    }
    setMessage("Checking credentials...", "");

    function finishSigningIn() {
      isSigningIn = false;
      if (submitButton) {
        submitButton.disabled = false;
      }
    }

    sha256(password)
      .then(function (passwordHash) {
        setCookie("user-login", login, 120);
        setCookie("password-hash", passwordHash, 120);

        return fetch("http://localhost:9992/api/sessions/login/", {
          method: "POST",
          credentials: "same-origin"
        });
      })
      .then(function (response) {
        clearCookie("password-hash");

        if (response.status >= 300) {
          return response.text().then(function (html) {
            replaceDocument(html, window.location.href);
          });
        }

        setMessage("Signed in. Opening control panel...", "good");
        return loadPanelPage();
      })
      .catch(function (error) {
        clearCookie("password-hash");
        setMessage(error.message || "Could not sign in. Try again.", "error");
        finishSigningIn();
      })
      .then(function () {
        finishSigningIn();
      });

    return false;
  };

  if (form) {
    form.addEventListener("submit", window.SignInTheUser);
  }

  if (submitButton) {
    submitButton.addEventListener("click", window.SignInTheUser);
  }
}());
