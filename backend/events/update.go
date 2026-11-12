package events

import (
	"encoding/json"
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
)

func UpdateEventsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	current_handler_action := "update"
	current_handler_route := fmt.Sprintf("/api/events/%s/", current_handler_action)
	current_handler_method := http.MethodPut
	if r.URL.Path != current_handler_route {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateEventsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != current_handler_method {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     fmt.Sprintf("Only %s is allowed", current_handler_method),
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateEventsApiCallHandler]: Incorrect method was applied")
		return
	}

	if _, ok := authorizeEventsRequest("UpdateEventsApiCallHandler", w, r); !ok {
		return
	}

	eventID, ok := validateEventIDQuery(r)
	if !ok {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateEventsApiCallHandler]: Incorrect query format")
		return
	}

	exists, err := eventExists(r.Context(), eventID)
	if err != nil {
		handleEventsError("UpdateEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !exists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Such an event with given ID does not exists",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateEventsApiCallHandler]: Such an event with given ID does not exists")
		return
	}

	var event models.EventsData
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect request body format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateEventsApiCallHandler]: " + err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Events
		SET EventTitle = $1,
			EventPlace = $2,
			EventStartDate = $3,
			EventStartTime = $4,
			EventFinishDate = $5,
			EventFinishTime = $6,
			Description = $7,
			RegistrationLink = $8,
			AnnouncementDate = $9,
			AnnouncementTime = $10,
			RegistrationFinishDate = $11,
			RegistrationFinishTime = $12
		WHERE EventID = $13`,
		event.EventTitle,
		event.EventPlace,
		event.EventStartDate,
		event.EventStartTime,
		event.EventFinishDate,
		event.EventFinishTime,
		event.EventDescription,
		event.RegistrationLink,
		event.AnnouncementDate,
		event.AnnouncementTime,
		event.RegistrationFinishDate,
		event.RegistrationFinishTime,
		eventID,
	)
	if err != nil {
		handleEventsError("UpdateEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
