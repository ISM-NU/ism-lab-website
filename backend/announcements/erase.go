package announcements

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
	"strconv"
)

func EraseAnnouncementsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/announcements/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("%sAnnouncementsApiCallHandler", "Erase")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	isAdmin := backend.CheckAdministratorRole(handler_name, w, r)
	if !isAdmin {
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

	_, err = database.DbConn.Exec(
		r.Context(),
		`DELETE FROM Announcements WHERE AnnouncementID = $1`,
		announcementID,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
