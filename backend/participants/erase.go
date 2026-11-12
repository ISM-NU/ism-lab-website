package participants

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
)

func EraseParticipantsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/participants/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("[%sParticipantsApiCallHandler]", "Erase")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	user_login, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var administrator_exists bool
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (
			SELECT 1
			FROM Administrator
			WHERE AdminLogin = $1
		)`,
		user_login,
	).Scan(&administrator_exists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !administrator_exists {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Only Administrators can access this route", "Non-administrator attempted to erase a participant")
		return
	}

	query := r.URL.Query()
	participant_ids, has_participant_id := query["participant_id"]
	if len(query) != 1 || !has_participant_id || len(participant_ids) != 1 || participant_ids[0] == "" {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var participant_exists bool
	err = database.DbConn.QueryRow(
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
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a participant does not exists", "Participant was not found")
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`DELETE FROM ListsOfParticipants
		WHERE ParticipantID = $1`,
		participant_ids[0],
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
