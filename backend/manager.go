package backend

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"main/database"
	error_handling "main/errors"
	"main/models"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
)

func ListManagerApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/manager/list/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListManagerApiCallHandler]: Incorrect URL path was applied")
		return
	}
	if r.Method != http.MethodGet {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only GET method is allowed in this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListManagerApiCallHandler]: Wrong method was applied to this route")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListManagerApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListManagerApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[ListManagerApiCallHandler]: " + err.Error())
		} else {
			log.Println("[ListManagerApiCallHandler]: Unauthorized manager list attempt")
		}
		return
	}

	query := r.URL.Query()
	managerLogins, hasManagerLogin := query["mng_login"]
	managerEmails, hasManagerEmail := query["mng_email"]
	targets, hasTarget := query["target"]

	queryCount := 0
	if hasManagerLogin {
		queryCount++
	}
	if hasManagerEmail {
		queryCount++
	}
	if hasTarget {
		queryCount++
	}

	if len(query) != 1 || queryCount != 1 || (hasManagerLogin && (len(managerLogins) != 1 || managerLogins[0] == "")) || (hasManagerEmail && (len(managerEmails) != 1 || managerEmails[0] == "")) || (hasTarget && (len(targets) != 1 || targets[0] != "all")) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[ListManagerApiCallHandler]: Incorrect query format")
		return
	}

	var managers []models.Managers

	if hasTarget {
		rows, err := database.DbConn.Query(
			r.Context(),
			`SELECT MngLogin, MngFirstName, MngLastName, MngEmail, MngIcon
			FROM Manager`,
		)
		if err != nil {
			log.Println("[ListManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		defer rows.Close()

		for rows.Next() {
			var manager models.Managers
			err = rows.Scan(&manager.ManagerLogin, &manager.ManagerFirstName, &manager.ManagerLastName, &manager.ManagerEmail, &manager.ManagerIconUrl)
			if err != nil {
				log.Println("[ListManagerApiCallHandler]: " + err.Error())
				http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
				return
			}
			managers = append(managers, manager)
		}
		if err = rows.Err(); err != nil {
			log.Println("[ListManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
	} else {
		var manager models.Managers
		if hasManagerLogin {
			err = database.DbConn.QueryRow(
				r.Context(),
				`SELECT MngLogin, MngFirstName, MngLastName, MngEmail, MngIcon
				FROM Manager
				WHERE MngLogin = $1`,
				managerLogins[0],
			).Scan(&manager.ManagerLogin, &manager.ManagerFirstName, &manager.ManagerLastName, &manager.ManagerEmail, &manager.ManagerIconUrl)
		} else {
			err = database.DbConn.QueryRow(
				r.Context(),
				`SELECT MngLogin, MngFirstName, MngLastName, MngEmail, MngIcon
				FROM Manager
				WHERE MngEmail = $1`,
				managerEmails[0],
			).Scan(&manager.ManagerLogin, &manager.ManagerFirstName, &manager.ManagerLastName, &manager.ManagerEmail, &manager.ManagerIconUrl)
		}
		if errors.Is(err, pgx.ErrNoRows) {
			current_error := models.ErrorPage{
				ErrorCode:       http.StatusNotFound,
				OfficialMessage: http.StatusText(http.StatusNotFound),
				Explanation:     "No such Manager found in the database",
			}
			error_handling.ErrorPageHandler(current_error, w, r)
			log.Println("[ListManagerApiCallHandler]: No such Manager found in the database")
			return
		}
		if err != nil {
			log.Println("[ListManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}

		managers = append(managers, manager)
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(managers); err != nil {
		log.Println("[ListManagerApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}

func CreateManagerApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/manager/create/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was called",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: Wrong path was applied")
		return
	}
	if r.Method != http.MethodPost {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only POST method is allowed on this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: Wrong method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		} else {
			log.Println("[CreateManagerApiCallHandler]: Unauthorized manager create attempt")
		}
		return
	}

	var administratorExists bool
	err = database.DbConn.QueryRow(
		context.Background(),
		`SELECT EXISTS (
			SELECT 1
			FROM Administrator
			WHERE AdminLogin = $1
		)`,
		userLoginCookie.Value,
	).Scan(&administratorExists)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		return
	}

	if !administratorExists {
		message := models.Message{
			MessageTitle:   "Permission Denied",
			MessageContent: "Only Administrators are allowed",
			AdditionalInfo: models.MetaData{
				AppliedMethod:      r.Method,
				TargetRoute:        r.URL.Path,
				ResponseServerTime: time.Now(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(message); err != nil {
			log.Println("[CreateManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		return
	}

	var manager models.Managers
	if err := json.NewDecoder(r.Body).Decode(&manager); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect request body format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		return
	}

	emailExists, err := database.CheckIfEmailAlreadyExists(database.DbConn, manager.ManagerEmail)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		return
	}

	loginExists, err := database.CheckIfLoginAlreadyExists(database.DbConn, manager.ManagerLogin)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		return
	}

	if emailExists || loginExists {
		message := models.Message{
			MessageTitle:   "Permission denied",
			MessageContent: "Email or Login already exists",
			AdditionalInfo: models.MetaData{
				AppliedMethod:      r.Method,
				TargetRoute:        r.URL.Path,
				ResponseServerTime: time.Now(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(message); err != nil {
			log.Println("[CreateManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		return
	}

	passwordHashCookie, err := r.Cookie("password-hash")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: Missing password-hash cookie")
		return
	}
	manager.ManagerPassHash = passwordHashCookie.Value

	if err := database.InsertNewManager(database.DbConn, manager); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the work",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		return
	}

	message := models.Message{
		MessageTitle:   "Transaction Successful",
		MessageContent: "New Manager Added",
		AdditionalInfo: models.MetaData{
			AppliedMethod:      r.Method,
			TargetRoute:        r.URL.Path,
			ResponseServerTime: time.Now(),
		},
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(message); err != nil {
		log.Println("[CreateManagerApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}

func UpdateManagerApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/manager/update/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was applied",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: Wrong path was applied")
		return
	}
	if r.Method != http.MethodPut {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only PUT method is allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: Wrong method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users are allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users are allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users are allowed",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[UpdateManagerApiCallHandler]: " + err.Error())
		} else {
			log.Println("[UpdateManagerApiCallHandler]: Unauthorized manager update attempt")
		}
		return
	}

	query := r.URL.Query()
	managerLogins, hasManagerLogin := query["mng_login"]
	managerEmails, hasManagerEmail := query["mng_email"]

	if len(query) != 1 || hasManagerLogin == hasManagerEmail || (hasManagerLogin && (len(managerLogins) != 1 || managerLogins[0] == "")) || (hasManagerEmail && (len(managerEmails) != 1 || managerEmails[0] == "")) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: Incorrect query format")
		return
	}

	var manager models.Managers
	if err := json.NewDecoder(r.Body).Decode(&manager); err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect request body format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: " + err.Error())
		return
	}

	var rowsAffected int64
	if hasManagerLogin {
		commandTag, execErr := database.DbConn.Exec(
			context.Background(),
			`UPDATE Manager
			SET MngLogin = $1,
				MngFirstName = $2,
				MngLastName = $3,
				MngEmail = $4,
				MngIcon = $5
			WHERE MngLogin = $6`,
			manager.ManagerLogin,
			manager.ManagerFirstName,
			manager.ManagerLastName,
			manager.ManagerEmail,
			manager.ManagerIconUrl,
			managerLogins[0],
		)
		err = execErr
		rowsAffected = commandTag.RowsAffected()
	} else {
		commandTag, execErr := database.DbConn.Exec(
			context.Background(),
			`UPDATE Manager
			SET MngLogin = $1,
				MngFirstName = $2,
				MngLastName = $3,
				MngEmail = $4,
				MngIcon = $5
			WHERE MngEmail = $6`,
			manager.ManagerLogin,
			manager.ManagerFirstName,
			manager.ManagerLastName,
			manager.ManagerEmail,
			manager.ManagerIconUrl,
			managerEmails[0],
		)
		err = execErr
		rowsAffected = commandTag.RowsAffected()
	}
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transactoin",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[UpdateManagerApiCallHandler]: " + err.Error())
		return
	}

	if rowsAffected == 0 {
		message := models.Message{
			MessageTitle:   "Permission denied",
			MessageContent: "Such a manager with given login or email does not given",
			AdditionalInfo: models.MetaData{
				AppliedMethod:      r.Method,
				TargetRoute:        r.URL.Path,
				ResponseServerTime: time.Now(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(message); err != nil {
			log.Println("[UpdateManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		return
	}

	message := models.Message{
		MessageTitle:   "Transaction Successful",
		MessageContent: "Manager Data Updated",
		AdditionalInfo: models.MetaData{
			AppliedMethod:      r.Method,
			TargetRoute:        r.URL.Path,
			ResponseServerTime: time.Now(),
		},
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(message); err != nil {
		log.Println("[UpdateManagerApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}

func EraseManagerApiCallHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/api/manager/erase/" {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "Wrong path was applied",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: Incorrect path was called")
		return
	}
	if r.Method != http.MethodDelete {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Only DELETE method is allowed on this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: Incorrect method was applied")
		return
	}

	sessionIdCookie, err := r.Cookie("session-id")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: Missing session-id cookie")
		return
	}

	userLoginCookie, err := r.Cookie("user-login")
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: Missing user-login cookie")
		return
	}

	sessionExists, err := database.CheckIfSessionExists(database.DbConn, userLoginCookie.Value, sessionIdCookie.Value)
	if err != nil || !sessionExists {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Only authorized users can access this route",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		if err != nil {
			log.Println("[EraseManagerApiCallHandler]: " + err.Error())
		} else {
			log.Println("[EraseManagerApiCallHandler]: Unauthorized manager erase attempt")
		}
		return
	}

	var administratorExists bool
	err = database.DbConn.QueryRow(
		context.Background(),
		`SELECT EXISTS (
			SELECT 1
			FROM Administrator
			WHERE AdminLogin = $1
		)`,
		userLoginCookie.Value,
	).Scan(&administratorExists)
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transaction",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: " + err.Error())
		return
	}

	if !administratorExists {
		message := models.Message{
			MessageTitle:   "Access Denied",
			MessageContent: "Only Administrators can Erase Managers",
			AdditionalInfo: models.MetaData{
				AppliedMethod:      r.Method,
				TargetRoute:        r.URL.Path,
				ResponseServerTime: time.Now(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(message); err != nil {
			log.Println("[EraseManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		return
	}

	query := r.URL.Query()
	managerLogins, hasManagerLogin := query["mng_login"]
	managerEmails, hasManagerEmail := query["mng_email"]

	if len(query) != 1 || hasManagerLogin == hasManagerEmail || (hasManagerLogin && (len(managerLogins) != 1 || managerLogins[0] == "")) || (hasManagerEmail && (len(managerEmails) != 1 || managerEmails[0] == "")) {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusBadRequest,
			OfficialMessage: http.StatusText(http.StatusBadRequest),
			Explanation:     "Incorrect query format",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: Incorrect query format")
		return
	}

	var rowsAffected int64
	if hasManagerLogin {
		commandTag, execErr := database.DbConn.Exec(
			context.Background(),
			`DELETE FROM Manager
			WHERE MngLogin = $1`,
			managerLogins[0],
		)
		err = execErr
		rowsAffected = commandTag.RowsAffected()
	} else {
		commandTag, execErr := database.DbConn.Exec(
			context.Background(),
			`DELETE FROM Manager
			WHERE MngEmail = $1`,
			managerEmails[0],
		)
		err = execErr
		rowsAffected = commandTag.RowsAffected()
	}
	if err != nil {
		current_error := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the transaction",
		}
		error_handling.ErrorPageHandler(current_error, w, r)
		log.Println("[EraseManagerApiCallHandler]: " + err.Error())
		return
	}

	if rowsAffected == 0 {
		message := models.Message{
			MessageTitle:   "No transaction",
			MessageContent: "No such manager with given login or email exists",
			AdditionalInfo: models.MetaData{
				AppliedMethod:      r.Method,
				TargetRoute:        r.URL.Path,
				ResponseServerTime: time.Now(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(message); err != nil {
			log.Println("[EraseManagerApiCallHandler]: " + err.Error())
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		return
	}

	message := models.Message{
		MessageTitle:   "Transaction Successfull",
		MessageContent: "Manager is deleted succesfully",
		AdditionalInfo: models.MetaData{
			AppliedMethod:      r.Method,
			TargetRoute:        r.URL.Path,
			ResponseServerTime: time.Now(),
		},
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(message); err != nil {
		log.Println("[EraseManagerApiCallHandler]: " + err.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}
