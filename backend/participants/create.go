package participants

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreateParticipantsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/participants/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("[%sParticipantsApiCallHandler]", "Create")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var participant models.ParticipantData
	if err := json.NewDecoder(r.Body).Decode(&participant); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect json format", err.Error())
		return
	}

	var event_exists bool
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (
			SELECT 1
			FROM Events
			WHERE EventID = $1
		)`,
		participant.AttendingEvent,
	).Scan(&event_exists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !event_exists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an event does not exists", "Attending event was not found")
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`INSERT INTO ListsOfParticipants (FirstName, LastName, MiddleName, Organization, AttendingEvent)
		VALUES ($1, $2, $3, $4, $5)`,
		participant.FirstName,
		participant.LastName,
		participant.MiddleName,
		participant.Organization,
		participant.AttendingEvent,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
