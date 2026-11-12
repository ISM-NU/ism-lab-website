package events

import (
	"context"
	"errors"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func handleEventsError(handlerName string, w http.ResponseWriter, r *http.Request, statusCode int, explanation string, logMessage string) {
	current_error := models.ErrorPage{
		ErrorCode:       statusCode,
		OfficialMessage: http.StatusText(statusCode),
		Explanation:     explanation,
	}
	error_handling.ErrorPageHandler(current_error, w, r)
	log.Println("[" + handlerName + "]: " + logMessage)
}

func authorizeEventsRequest(handlerName string, w http.ResponseWriter, r *http.Request) (string, bool) {
	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		handleEventsError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", "Missing session-id cookie")
		return "", false
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		handleEventsError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", "Missing user-login cookie")
		return "", false
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		logMessage := "Unauthorized events access attempt"
		if err != nil {
			logMessage = err.Error()
		}
		handleEventsError(handlerName, w, r, http.StatusBadRequest, "Only authorized users can access this route", logMessage)
		return "", false
	}

	return userLoginCookie.Value, true
}

func validateEventIDQuery(r *http.Request) (string, bool) {
	query := r.URL.Query()
	eventIDs, hasEventID := query["event_id"]
	returnValue := hasEventID && len(query) == 1 && len(eventIDs) == 1 && eventIDs[0] != ""
	if !returnValue {
		return "", false
	}
	return eventIDs[0], true
}

func eventExists(ctx context.Context, eventID string) (bool, error) {
	var foundEventID string
	err := database.DbConn.QueryRow(
		ctx,
		`SELECT EventID
		FROM Events
		WHERE EventID = $1`,
		eventID,
	).Scan(&foundEventID)
	if errors.Is(err, pgx.ErrNoRows) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	return true, nil
}
