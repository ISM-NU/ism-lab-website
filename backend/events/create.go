package events

import (
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
)

func CreateEventsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	current_handler_action := "create"
	current_handler_route := fmt.Sprintf("/api/events/%s/", current_handler_action)
	current_handler_method := http.MethodPost
	if r.URL.Path != current_handler_route {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateEventsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != current_handler_method {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     fmt.Sprintf("Only %s is allowed", current_handler_method),
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateEventsApiCallHandler]: Incorrect method was applied")
		return
	}

	if _, ok := authorizeEventsRequest("CreateEventsApiCallHandler", w, r); !ok {
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
		log.Println("[CreateEventsApiCallHandler]: " + err.Error())
		return
	}

	eventHash := sha512.Sum512([]byte(fmt.Sprintf(
		"%s%s%s%s%s%s%s%s%s%s%s",
		event.EventTitle,
		event.EventPlace,
		event.EventStartDate.String(),
		event.EventStartTime.String(),
		event.EventFinishDate.String(),
		event.EventFinishTime.String(),
		event.RegistrationLink,
		event.AnnouncementDate.String(),
		event.AnnouncementTime.String(),
		event.RegistrationFinishDate.String(),
		event.RegistrationFinishTime.String(),
	)))
	event.EventID = hex.EncodeToString(eventHash[:])

	for {
		exists, err := eventExists(r.Context(), event.EventID)
		if err != nil {
			handleEventsError("CreateEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		if !exists {
			break
		}
		eventHash = sha512.Sum512([]byte(event.EventID))
		event.EventID = hex.EncodeToString(eventHash[:])
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`INSERT INTO Events (
			EventID,
			EventTitle,
			EventPlace,
			EventStartDate,
			EventStartTime,
			EventFinishDate,
			EventFinishTime,
			Description,
			RegistrationLink,
			AnnouncementDate,
			AnnouncementTime,
			RegistrationFinishDate,
			RegistrationFinishTime
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
		event.EventID,
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
	)
	if err != nil {
		handleEventsError("CreateEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(models.ReturnEventID{EventID: event.EventID})
}
