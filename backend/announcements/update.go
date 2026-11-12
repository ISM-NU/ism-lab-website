package announcements

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
	"strconv"
)

func UpdateAnnouncementsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/announcements/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("%sAnnouncementsApiCallHandler", "Update")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	query := r.URL.Query()
	announcementIDs, hasAnnouncementID := query["announce_id"]
	if len(query) != 1 || !hasAnnouncementID || len(announcementIDs) != 1 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}
	announcementID, err := strconv.ParseInt(announcementIDs[0], 10, 64)
	if err != nil || announcementID <= 0 {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var announcementExists bool
	err = database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (SELECT 1 FROM Announcements WHERE AnnouncementID = $1)`,
		announcementID,
	).Scan(&announcementExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}
	if !announcementExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "No such an announcement with given ID found", "Announcement was not found")
		return
	}

	var announcement models.Announcements
	if err := json.NewDecoder(r.Body).Decode(&announcement); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Announcements
		SET AnnouncementTitle = $1,
			AnnouncementDescription = $2,
			AnnouncementDate = $3,
			AnnouncementTime = $4
		WHERE AnnouncementID = $5`,
		announcement.AnnouncementTitle,
		announcement.AnnouncementDescription,
		announcement.AnnouncementDate,
		announcement.AnnouncementTime,
		announcementID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
