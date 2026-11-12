package announcements

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"

	"github.com/jackc/pgx/v5"
)

func ListAnnouncementsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/announcements/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("%sAnnouncementsApiCallHandler", "List")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	announcementIDs, hasAnnouncementID := query["announce_id"]
	targets, hasTarget := query["target"]
	validTarget := hasTarget && len(targets) == 1 && targets[0] == "all"
	announcementID := int64(0)
	validAnnouncementID := false
	if hasAnnouncementID && len(announcementIDs) == 1 {
		parsedID, err := strconv.ParseInt(announcementIDs[0], 10, 64)
		if err == nil && parsedID > 0 {
			announcementID = parsedID
			validAnnouncementID = true
		}
	}
	if len(query) != 1 || validAnnouncementID == validTarget {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	const selectAnnouncements = `SELECT AnnouncementID, AnnouncementTitle,
		COALESCE(AnnouncementDescription, ''),
		COALESCE(AnnouncementDate, DATE '0001-01-01'),
		COALESCE(AnnouncementTime, TIME '00:00:00')
	FROM Announcements`

	if validAnnouncementID {
		var announcement models.Announcements
		err := database.DbConn.QueryRow(
			r.Context(),
			selectAnnouncements+" WHERE AnnouncementID = $1",
			announcementID,
		).Scan(
			&announcement.AnnouncementID,
			&announcement.AnnouncementTitle,
			&announcement.AnnouncementDescription,
			&announcement.AnnouncementDate,
			&announcement.AnnouncementTime,
		)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "No such an announcement with given ID found", "Announcement was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(announcement); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		}
		return
	}

	rows, err := database.DbConn.Query(r.Context(), selectAnnouncements+" ORDER BY AnnouncementID")
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}
	defer rows.Close()

	announcements := make([]models.Announcements, 0)
	for rows.Next() {
		var announcement models.Announcements
		if err := rows.Scan(
			&announcement.AnnouncementID,
			&announcement.AnnouncementTitle,
			&announcement.AnnouncementDescription,
			&announcement.AnnouncementDate,
			&announcement.AnnouncementTime,
		); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
			return
		}
		announcements = append(announcements, announcement)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(announcements); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
	}

}
