package participants

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func ListParticipantsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/participants/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("[%sParticipantsApiCallHandler]", "List")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	participant_ids, has_participant_id := query["participant_id"]
	attending_events, has_attending_event := query["attending_event"]
	targets, has_target := query["target"]
	valid_participant_id := has_participant_id && len(participant_ids) == 1 && participant_ids[0] != ""
	valid_attending_event := has_attending_event && len(attending_events) == 1 && attending_events[0] != ""
	valid_target := has_target && len(targets) == 1 && targets[0] == "all"
	if len(query) != 1 || !valid_participant_id && !valid_attending_event && !valid_target {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	if valid_participant_id {
		var participant models.ParticipantData
		err := database.DbConn.QueryRow(
			r.Context(),
			`SELECT ParticipantID::text, FirstName, LastName, COALESCE(MiddleName, ''),
				COALESCE(Organization, ''), COALESCE(AttendingEvent, '')
			FROM ListsOfParticipants
			WHERE ParticipantID = $1`,
			participant_ids[0],
		).Scan(
			&participant.ParticipantID,
			&participant.FirstName,
			&participant.LastName,
			&participant.MiddleName,
			&participant.Organization,
			&participant.AttendingEvent,
		)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a participant with given ID does not exists", "Participant was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(participant); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		}
		return
	}

	if valid_attending_event {
		var event_exists bool
		err := database.DbConn.QueryRow(
			r.Context(),
			`SELECT EXISTS (
				SELECT 1
				FROM Events
				WHERE EventID = $1
			)`,
			attending_events[0],
		).Scan(&event_exists)
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		if !event_exists {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such an event does not exists", "Attending event was not found")
			return
		}
	}

	statement := `SELECT ParticipantID::text, FirstName, LastName, COALESCE(MiddleName, ''),
			COALESCE(Organization, ''), COALESCE(AttendingEvent, '')
		FROM ListsOfParticipants
		ORDER BY ParticipantID`
	arguments := []any{}
	if valid_attending_event {
		statement = `SELECT ParticipantID::text, FirstName, LastName, COALESCE(MiddleName, ''),
				COALESCE(Organization, ''), COALESCE(AttendingEvent, '')
			FROM ListsOfParticipants
			WHERE AttendingEvent = $1
			ORDER BY ParticipantID`
		arguments = append(arguments, attending_events[0])
	}

	rows, err := database.DbConn.Query(r.Context(), statement, arguments...)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	defer rows.Close()

	participants := make([]models.ParticipantData, 0)
	for rows.Next() {
		var participant models.ParticipantData
		if err := rows.Scan(
			&participant.ParticipantID,
			&participant.FirstName,
			&participant.LastName,
			&participant.MiddleName,
			&participant.Organization,
			&participant.AttendingEvent,
		); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		participants = append(participants, participant)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(participants); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
	}

}
