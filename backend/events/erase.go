package events

import (
	"fmt"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
)

func EraseEventsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	current_handler_action := "erase"
	current_handler_route := fmt.Sprintf("/api/events/%s/", current_handler_action)
	current_handler_method := http.MethodDelete
	if r.URL.Path != current_handler_route {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Incorrect path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseEventsApiCallHandler]: Wrong route was applied to the request")
		return
	}
	if r.Method != current_handler_method {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     fmt.Sprintf("Only %s is allowed", current_handler_method),
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseEventsApiCallHandler]: Incorrect method was applied")
		return
	}

	userLogin, ok := authorizeEventsRequest("EraseEventsApiCallHandler", w, r)
	if !ok {
		return
	}

	var administratorExists bool
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (
			SELECT 1
			FROM Administrator
			WHERE AdminLogin = $1
		)`,
		userLogin,
	).Scan(&administratorExists)
	if err != nil {
		handleEventsError("EraseEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !administratorExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only Administrators can erase events",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseEventsApiCallHandler]: Only Administrators can erase events")
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
		log.Println("[EraseEventsApiCallHandler]: Incorrect query format")
		return
	}

	exists, err := eventExists(r.Context(), eventID)
	if err != nil {
		handleEventsError("EraseEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !exists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Such an event with given ID does not exists",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseEventsApiCallHandler]: Such an event with given ID does not exists")
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`DELETE FROM Events
		WHERE EventID = $1`,
		eventID,
	)
	if err != nil {
		handleEventsError("EraseEventsApiCallHandler", w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
