package events

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func ListEventsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	current_handler_action := "list"
	current_handler_route := fmt.Sprintf("/api/events/%s/", current_handler_action)
	current_handler_method := http.MethodGet
	if r.URL.Path != current_handler_route {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListEventsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != current_handler_method {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     fmt.Sprintf("Only %s is allowed", current_handler_method),
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListEventsApiCallHandler]: Incorrect method was applied")
		return
	}

	query := r.URL.Query()
	eventIDs, hasEventID := query["event_id"]
	targets, hasTarget := query["target"]

	if len(query) != 1 || hasEventID == hasTarget || (hasEventID && (len(eventIDs) != 1 || eventIDs[0] == "")) || (hasTarget && (len(targets) != 1 || targets[0] != "all")) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListEventsApiCallHandler]: Incorrect query format")
		return
	}

	events := make([]models.EventsData, 0)
	if hasTarget {
		rows, err := database.DbConn.Query(
			r.Context(),
			`SELECT EventID, EventTitle, EventPlace, EventStartDate, EventStartTime, EventFinishDate,
				EventFinishTime, Description, RegistrationLink, AnnouncementDate, AnnouncementTime,
				RegistrationFinishDate, RegistrationFinishTime
			FROM Events
			ORDER BY EventStartDate, EventStartTime, EventTitle`,
		)
		if err != nil {
			handleEventsError("ListEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		defer rows.Close()

		for rows.Next() {
			var event models.EventsData
			err = rows.Scan(
				&event.EventID,
				&event.EventTitle,
				&event.EventPlace,
				&event.EventStartDate,
				&event.EventStartTime,
				&event.EventFinishDate,
				&event.EventFinishTime,
				&event.EventDescription,
				&event.RegistrationLink,
				&event.AnnouncementDate,
				&event.AnnouncementTime,
				&event.RegistrationFinishDate,
				&event.RegistrationFinishTime,
			)
			if err != nil {
				handleEventsError("ListEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
				return
			}
			events = append(events, event)
		}
		if err = rows.Err(); err != nil {
			handleEventsError("ListEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
	} else {
		var event models.EventsData
		err := database.DbConn.QueryRow(
			r.Context(),
			`SELECT EventID, EventTitle, EventPlace, EventStartDate, EventStartTime, EventFinishDate,
				EventFinishTime, Description, RegistrationLink, AnnouncementDate, AnnouncementTime,
				RegistrationFinishDate, RegistrationFinishTime
			FROM Events
			WHERE EventID = $1`,
			eventIDs[0],
		).Scan(
			&event.EventID,
			&event.EventTitle,
			&event.EventPlace,
			&event.EventStartDate,
			&event.EventStartTime,
			&event.EventFinishDate,
			&event.EventFinishTime,
			&event.EventDescription,
			&event.RegistrationLink,
			&event.AnnouncementDate,
			&event.AnnouncementTime,
			&event.RegistrationFinishDate,
			&event.RegistrationFinishTime,
		)
		if errors.Is(err, pgx.ErrNoRows) {
			current_error := models.ErrorPage{
				ErrorCode:       http.StatusNotFound,
				OfficialMessage: http.StatusText(http.StatusNotFound),
				Explanation:     "No such event ID exists",
			}
			error_handling.ErrorPageHandler(current_error, w, r)
			log.Println("[ListEventsApiCallHandler]: No such event ID exists")
			return
		}
		if err != nil {
			handleEventsError("ListEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		events = append(events, event)
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(events); err != nil {
		handleEventsError("ListEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

}
