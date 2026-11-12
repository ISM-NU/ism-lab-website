package backend

import (
	"crypto/sha512"
	"encoding/json"
	"errors"
	"fmt"
	"main/database"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func UpdatePasswordApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "UpdatePasswordApiCallHandler"
	handler_route := "/api/password/update/"
	hander_method := http.MethodPut
	ok := RouteMethodValidation(handler_route, hander_method, handler_name, w, r)
	if !ok {
		return
	}

	user_login, signed_in := AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	passwordHashCookie, err := r.Cookie("password-hash")
	if err != nil {
		HandleCommonError(handler_name, w, r, http.StatusBadRequest, "No password retreived from request", "Missing password-hash cookie")
		return
	}

	passwordHash := sha512.Sum512([]byte(passwordHashCookie.Value))
	passwordHashHex := fmt.Sprintf("%x", passwordHash)

	commandTag, err := database.DbConn.Exec(
		r.Context(),
		`WITH admin_update AS (
			UPDATE Administrator
			SET AdminPassHash = $1
			WHERE AdminLogin = $2
			RETURNING 1
		), manager_update AS (
			UPDATE Manager
			SET MngPassHash = $1
			WHERE MngLogin = $2
			AND NOT EXISTS (SELECT 1 FROM admin_update)
			RETURNING 1
		)
		SELECT 1
		FROM admin_update
		UNION ALL
		SELECT 1
		FROM manager_update`,
		passwordHashHex,
		user_login,
	)
	if err != nil || commandTag.RowsAffected() == 0 {
		logMessage := "User login was not found in Administrator or Manager"
		if err != nil {
			logMessage = err.Error()
		}
		HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transasction", logMessage)
		return
	}

	w.WriteHeader(http.StatusOK)

}

func UpdateAdminApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "UpdateAdminApiCallHandler"
	handler_route := "/api/admin/update/"
	handler_method := http.MethodPut
	ok := RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	user_login, signed_in := AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	isAdmin := CheckAdministratorRole(handler_name, w, r)
	if !isAdmin {
		return
	}

	var admin models.Admins
	if err := json.NewDecoder(r.Body).Decode(&admin); err != nil {
		HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect Body Format", err.Error())
		return
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`UPDATE Administrator
		SET AdminFirstName = $1,
			AdminLastName = $2,
			AdminEmail = $3,
			AdminIcon = $4
		WHERE AdminLogin = $5`,
		admin.AdminFirstName,
		admin.AdminLastName,
		admin.AdminEmail,
		admin.AdminIconUrl,
		user_login,
	)
	if err != nil {
		HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}

func ListAdminApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ListAdminApiCallHandler"
	handler_route := "/api/admin/list/"
	handler_method := http.MethodGet
	ok := RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	query := r.URL.Query()
	userLogins, ok := query["user_login"]
	if len(query) != 1 || !ok || len(userLogins) != 1 || userLogins[0] == "" {
		HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var admin models.Admins
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT AdminLogin,
			AdminPassHash,
			AdminFirstName,
			AdminLastName,
			AdminEmail,
			COALESCE(AdminIcon, '')
		FROM Administrator
		WHERE AdminLogin = $1`,
		userLogins[0],
	).Scan(
		&admin.AdminLogin,
		&admin.AdminPassHash,
		&admin.AdminFirstName,
		&admin.AdminLastName,
		&admin.AdminEmail,
		&admin.AdminIconUrl,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		HandleCommonError(handler_name, w, r, http.StatusNotFound, "No such Admin exsits", "No such Admin exsits")
		return
	}
	if err != nil {
		HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(admin); err != nil {
		HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during transaction", err.Error())
	}
}
