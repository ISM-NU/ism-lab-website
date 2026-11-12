(function () {
var announcementsRoot = document.getElementById("announcements");

function clearAnnouncements() {
  while (announcementsRoot.firstChild) {
    announcementsRoot.removeChild(announcementsRoot.firstChild);
  }
}

function formatAnnouncementDate(dateValue, timeValue) {
  const date = dateValue ? new Date(dateValue) : null;
  const timeMatch = typeof timeValue === "string" ? timeValue.match(/T(\d{2}:\d{2})/) : null;
  const parts = [];

  if (date && !Number.isNaN(date.getTime())) {
    parts.push(date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric"
    }));
  }

  if (timeMatch) {
    parts.push(timeMatch[1]);
  }

  return parts.join(" ");
}

function createEmptyAnnouncementCard() {
  const card = document.createElement("div");
  card.className = "card";

  const title = document.createElement("h4");
  title.textContent = "No announcements added yet";

  card.appendChild(title);
  return card;
}

function truncateAnnouncementText(text) {
  if (!text || text.length <= 50) {
    return text || "";
  }

  return text.slice(0, 50) + "...";
}

function createAnnouncementCard(announcement) {
  const card = document.createElement("article");
  card.className = "card";

  const title = document.createElement("h4");
  title.textContent = announcement.announcement_title || "Untitled announcement";

  const description = document.createElement("p");
  description.textContent = truncateAnnouncementText(announcement.announcement_description);

  const metaText = formatAnnouncementDate(
    announcement.announcement_date,
    announcement.announcement_time
  );

  card.appendChild(title);

  if (description.textContent) {
    card.appendChild(description);
  }

  if (metaText) {
    const meta = document.createElement("div");
    meta.className = "pill-row";

    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = metaText;

    meta.appendChild(pill);
    card.appendChild(meta);
  }

  return card;
}

function renderAnnouncements(announcements) {
  clearAnnouncements();

  if (!Array.isArray(announcements) || announcements.length === 0) {
    announcementsRoot.appendChild(createEmptyAnnouncementCard());
    return;
  }

  announcements.forEach(function (announcement) {
    announcementsRoot.appendChild(createAnnouncementCard(announcement));
  });
}

function loadAnnouncements() {
  fetch("http://localhost:9992/api/announcements/list/?target=all")
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Could not load announcements");
      }
      return response.json();
    })
    .then(renderAnnouncements)
    .catch(function () {
      renderAnnouncements([]);
    });
}

if (announcementsRoot) {
  loadAnnouncements();
}
}());
