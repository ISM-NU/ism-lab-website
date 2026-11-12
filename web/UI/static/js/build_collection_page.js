(function () {
  var section = document.body.getAttribute("data-section");
  var mode = document.body.getAttribute("data-mode");
  var list = document.getElementById("items-list");
  var modal = document.getElementById("item-modal");
  var form = document.getElementById("item-form");
  var fieldsRoot = document.getElementById("form-fields");
  var title = document.getElementById("item-modal-title");
  var showCreate = document.getElementById("show-create-form");
  var closeModal = document.getElementById("close-modal");
  var editorTools = document.getElementById("editor-tools");
  var photoInput = document.getElementById("photo-file-input");
  var insertPhoto = document.getElementById("insert-photo-button");
  var toast = document.getElementById("toast");
  var editingId = "";
  var descriptionName = "";
  var toastTimer = null;

  var configs = {
    projects: {
      title: "project",
      list: "/api/projects/list/?target=all",
      create: "/api/projects/create/",
      update: "/api/projects/update/?project_id=",
      erase: "/api/projects/erase/?project_id=",
      id: "project_id",
      dataId: "projectId",
      name: "project_name",
      fields: [
        { name: "project_name", label: "Project name", type: "text", required: true },
        { name: "project_description", label: "Description", type: "textarea", rich: true }
      ],
      display: [["Description", "project_description", true]]
    },
    announcements: {
      title: "announcement",
      list: "/api/announcements/list/?target=all",
      create: "/api/announcements/create/",
      update: "/api/announcements/update/?announce_id=",
      erase: "/api/announcements/erase/?announce_id=",
      id: "announcement_id",
      dataId: "announceId",
      name: "announcement_title",
      fields: [
        { name: "announcement_title", label: "Title", type: "text", required: true },
        { name: "announcement_date", label: "Date", type: "date" },
        { name: "announcement_time", label: "Time", type: "time" },
        { name: "announcement_description", label: "Description", type: "textarea", rich: true }
      ],
      display: [["Date", "announcement_date"], ["Time", "announcement_time"], ["Description", "announcement_description", true]]
    },
    publications: {
      title: "publication",
      list: "/api/publications/list/?target=all",
      create: "/api/publications/create/",
      update: "/api/publications/update/?pub_id=",
      erase: "/api/publications/erase/?pub_id=",
      id: "publication_id",
      dataId: "pubId",
      name: "publication_title",
      fields: [
        { name: "publication_title", label: "Title", type: "text", required: true },
        { name: "publication_keywords", label: "Keywords, comma separated", type: "text" },
        { name: "doi", label: "DOI", type: "text" }
      ],
      display: [["Keywords", "publication_keywords"], ["DOI", "doi"]]
    },
    datasets: {
      title: "dataset",
      list: "/api/datasets/list/?target=all",
      create: "/api/datasets/create/",
      update: "/api/datasets/update/?data_id=",
      erase: "/api/datasets/erase/?data_id=",
      id: "data_id",
      dataId: "dataId",
      name: "data_name",
      fields: [
        { name: "data_name", label: "Name", type: "text", required: true },
        { name: "data_type", label: "Type", type: "text" },
        { name: "data_date", label: "Date", type: "date" },
        { name: "data_version", label: "Version", type: "number" },
        { name: "data_size", label: "Size", type: "number", step: "0.01" },
        { name: "data_format", label: "Format", type: "text" },
        { name: "data_description", label: "Description", type: "textarea", rich: true }
      ],
      display: [["Type", "data_type"], ["Date", "data_date"], ["Version", "data_version"], ["Size", "data_size"], ["Format", "data_format"], ["Description", "data_description", true]]
    }
  };

  var config = configs[section];
  if (!config || !list) {
    return;
  }

  function clear(element) {
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

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = String(text);
    }
    return node;
  }

  function splitTime(value) {
    if (typeof value !== "string") {
      return "";
    }
    var match = value.match(/T(\d{2}:\d{2})/);
    if (match) {
      return match[1];
    }
    return value.length >= 5 ? value.slice(0, 5) : value;
  }

  function formatValue(value, fieldName) {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (fieldName && fieldName.indexOf("_time") > -1 && typeof value === "string") {
      return splitTime(value);
    }
    if (typeof value === "string" && value.length >= 10 && value.indexOf("T") > -1) {
      return value.slice(0, 10);
    }
    return value === undefined || value === null || value === "" ? "Not set" : value;
  }

  function sanitizeDescription(html) {
    var template = document.createElement("template");
    template.innerHTML = html || "";
    Array.prototype.slice.call(template.content.querySelectorAll("*")).forEach(function (node) {
      var tag = node.tagName;
      var allowed = ["A", "BR", "DIV", "EM", "H2", "IMG", "LI", "OL", "P", "SPAN", "STRONG", "UL"].indexOf(tag) >= 0;
      if (!allowed) {
        node.replaceWith(document.createTextNode(node.textContent || ""));
        return;
      }
      Array.prototype.slice.call(node.attributes).forEach(function (attr) {
        var name = attr.name.toLowerCase();
        var value = attr.value || "";
        var keep = tag === "IMG" && (name === "alt" || name === "src" && (value.indexOf("/static/icons/") === 0 || value.indexOf("http://localhost:9992/static/icons/") === 0)) ||
          tag === "A" && (name === "title" || name === "href" && value.toLowerCase().indexOf("javascript:") !== 0);
        if (!keep) {
          node.removeAttribute(attr.name);
        }
      });
    });
    return template.innerHTML;
  }

  function renderCard(item) {
    var card = el("article", "data-card" + (mode === "control" ? " has-actions" : ""), "");
    var grid = el("div", "data-grid", "");
    var heading = el("h2", "", item[config.name] || (config.title.charAt(0).toUpperCase() + config.title.slice(1)));
    card.dataset[config.dataId] = item[config.id] || "";

    if (mode === "control") {
      var actions = el("div", "card-actions", "");
      var update = el("button", "card-action", "Update");
      var remove = el("button", "card-action danger", "Delete");
      update.type = "button";
      remove.type = "button";
      update.addEventListener("click", function () { openForm(item); });
      remove.addEventListener("click", function () { deleteItem(card.dataset[config.dataId]); });
      actions.appendChild(update);
      actions.appendChild(remove);
      card.appendChild(actions);
    }

    card.appendChild(heading);
    config.display.forEach(function (field) {
      var pill = el("div", "data-pill" + (field[2] ? " description-block" : ""), "");
      var label = el("strong", "", field[0]);
      pill.appendChild(label);
      if (field[2]) {
        var desc = el("div", "event-description", "");
        desc.innerHTML = sanitizeDescription(item[field[1]] || "");
        pill.appendChild(desc);
      } else {
        pill.appendChild(document.createTextNode(formatValue(item[field[1]], field[1])));
      }
      grid.appendChild(pill);
    });
    card.appendChild(grid);
    return card;
  }

  function renderItems(items) {
    clear(list);
    if (!Array.isArray(items) || !items.length) {
      list.appendChild(el("p", "muted", "No " + section + " found."));
      return;
    }
    items.forEach(function (item) {
      list.appendChild(renderCard(item));
    });
  }

  function loadItems() {
    requestJson(config.list).then(renderItems).catch(function () {
      clear(list);
      list.appendChild(el("p", "error-text", "Could not load " + section + "."));
    });
  }

  function inputValue(field, item) {
    var value = item[field.name] || "";
    if (field.type === "date" && typeof value === "string" && value.length >= 10) {
      return value.slice(0, 10);
    }
    if (field.type === "time" && typeof value === "string") {
      return splitTime(value);
    }
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    return value;
  }

  function fieldNode(field, item) {
    var label = el("label", field.type === "textarea" ? "wide" : "", field.label);
    var input = document.createElement(field.type === "textarea" ? "textarea" : "input");
    input.name = field.name;
    input.required = !!field.required;
    if (field.type !== "textarea") {
      input.type = field.type;
    }
    if (field.step) {
      input.step = field.step;
    }
    input.value = inputValue(field, item || {});
    if (field.type === "textarea") {
      input.rows = 8;
    }
    label.appendChild(input);
    return label;
  }

  function openForm(item) {
    if (!form || !modal || !fieldsRoot) {
      return;
    }
    editingId = item && item[config.id] ? String(item[config.id]) : "";
    descriptionName = "";
    clear(fieldsRoot);
    title.textContent = (editingId ? "Update " : "Create ") + config.title;
    config.fields.forEach(function (field) {
      if (field.rich) {
        descriptionName = field.name;
      }
      fieldsRoot.appendChild(fieldNode(field, item || {}));
    });
    if (editorTools) {
      editorTools.classList.toggle("hidden", !descriptionName);
    }
    modal.classList.remove("hidden");
  }

  function closeForm() {
    if (modal) {
      modal.classList.add("hidden");
    }
  }

  function toRFCDate(value) {
    return value ? value + "T00:00:00Z" : "0001-01-01T00:00:00Z";
  }

  function toRFCTime(value) {
    return "0001-01-01T" + (value || "00:00") + ":00Z";
  }

  function payload() {
    var data = {};
    config.fields.forEach(function (field) {
      var value = form.elements[field.name].value.trim();
      if (field.name === "publication_keywords") {
        data[field.name] = value ? value.split(",").map(function (part) { return part.trim(); }).filter(Boolean) : [];
      } else if (field.type === "number") {
        data[field.name] = value === "" ? 0 : Number(value);
      } else if (field.type === "date") {
        data[field.name] = toRFCDate(value);
      } else if (field.type === "time") {
        data[field.name] = toRFCTime(value);
      } else {
        data[field.name] = value;
      }
    });
    return data;
  }

  function submitItem(event) {
    event.preventDefault();
    var url = editingId ? config.update + encodeURIComponent(editingId) : config.create;
    requestJson(url, {
      method: editingId ? "PUT" : "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload())
    }).then(function () {
      showToast("Transaction Successful");
      closeForm();
      loadItems();
    }).catch(function () { showToast("Could not save " + config.title); });
  }

  function deleteItem(id) {
    requestJson(config.erase + encodeURIComponent(id), { method: "DELETE", credentials: "same-origin" }).then(function () {
      showToast("Transaction Successful");
      loadItems();
    }).catch(function () { showToast("Could not delete " + config.title); });
  }

  function textarea() {
    return descriptionName && form ? form.elements[descriptionName] : null;
  }

  function wrapSelection(before, after) {
    var input = textarea();
    if (!input) {
      return;
    }
    var start = input.selectionStart;
    var end = input.selectionEnd;
    var selected = input.value.slice(start, end) || "Text";
    input.value = input.value.slice(0, start) + before + selected + after + input.value.slice(end);
    input.focus();
  }

  function insertAtCursor(text) {
    var input = textarea();
    if (!input) {
      return;
    }
    var start = input.selectionStart;
    var end = input.selectionEnd;
    input.value = input.value.slice(0, start) + text + input.value.slice(end);
    input.focus();
  }

  function readFile(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var result = String(reader.result || "");
        var comma = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function uploadPhoto(file) {
    return readFile(file).then(function (photo) {
      return requestJson("/api/photo/create/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ photo_description: file.name.replace(/[^A-Za-z0-9._-]/g, "_") || "content_photo", photo: photo })
      });
    }).then(function (data) {
      if (data.photo_url) {
        insertAtCursor('<img src="' + data.photo_url + '" alt="">');
        showToast("Photo inserted");
      }
    });
  }

  if (showCreate) {
    showCreate.addEventListener("click", function () { openForm({}); });
  }
  if (closeModal) {
    closeModal.addEventListener("click", closeForm);
  }
  if (form) {
    form.addEventListener("submit", submitItem);
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-command]"), function (button) {
    button.addEventListener("click", function () {
      var command = button.getAttribute("data-command");
      if (command === "bold") {
        wrapSelection("<strong>", "</strong>");
      } else if (command === "italic") {
        wrapSelection("<em>", "</em>");
      } else if (command === "heading") {
        wrapSelection("<h2>", "</h2>");
      }
    });
  });
  if (insertPhoto && photoInput) {
    insertPhoto.addEventListener("click", function () {
      photoInput.value = "";
      photoInput.click();
    });
    photoInput.addEventListener("change", function () {
      var file = photoInput.files && photoInput.files[0];
      if (file) {
        uploadPhoto(file).catch(function () { showToast("Could not insert photo"); });
      }
    });
  }

  loadItems();
}());
