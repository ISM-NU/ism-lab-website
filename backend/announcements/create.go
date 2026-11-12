package announcements

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreateAnnouncementsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/announcements/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("%sAnnouncementsApiCallHandler", "Create")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var announcement models.Announcements
	if err := json.NewDecoder(r.Body).Decode(&announcement); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`INSERT INTO Announcements
			(AnnouncementTitle, AnnouncementDescription, AnnouncementDate, AnnouncementTime)
		VALUES ($1, $2, $3, $4)`,
		announcement.AnnouncementTitle,
		announcement.AnnouncementDescription,
		announcement.AnnouncementDate,
		announcement.AnnouncementTime,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
