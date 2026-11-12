package participants

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func UpdateParticipantsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/participants/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("[%sParticipantsApiCallHandler]", "Update")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	query := r.URL.Query()
	participant_ids, has_participant_id := query["participant_id"]
	if len(query) != 1 || !has_participant_id || len(participant_ids) != 1 || participant_ids[0] == "" {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var participant_exists bool
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (
			SELECT 1
			FROM ListsOfParticipants
			WHERE ParticipantID = $1
		)`,
		participant_ids[0],
	).Scan(&participant_exists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !participant_exists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a participant was not found", "Participant was not found")
		return
	}

	var participant models.ParticipantData
	if err := json.NewDecoder(r.Body).Decode(&participant); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect json format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE ListsOfParticipants
		SET FirstName = $1,
			LastName = $2,
			MiddleName = $3,
			Organization = $4,
			AttendingEvent = $5
		WHERE ParticipantID = $6`,
		participant.FirstName,
		participant.LastName,
		participant.MiddleName,
		participant.Organization,
		participant.AttendingEvent,
		participant_ids[0],
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
