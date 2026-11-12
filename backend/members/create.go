package members

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreateMembersApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/members/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("%sMembersApiCallHandler", "Create")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var member models.MemberData
	if err := json.NewDecoder(r.Body).Decode(&member); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	var memberExists bool
	err := database.DbConn.QueryRow(r.Context(), `SELECT EXISTS (SELECT 1 FROM ISMLabMembers WHERE Email = $1)`, member.Email).Scan(&memberExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if memberExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "The member with such an email already exists", "Member email already exists")
		return
	}

	_, err = database.DbConn.Exec(r.Context(), `INSERT INTO ISMLabMembers (
		FirstName, LastName, CurrentYearOfStudy, CurrentlyStudying, Degree, JoinDate,
		AdditionalDescription, MemberIcon, Email
	) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
		member.FirstName, member.LastName, member.CurrentYearOfStudy, member.CurrentlyStudying,
		member.Degree, member.JoinDate, member.AdditionalDescription, member.MemberIcon, member.Email)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
