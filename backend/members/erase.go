package members

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
)

func EraseMembersApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/members/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("%sMembersApiCallHandler", "Erase")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signedIn := backend.AuthorizeRequest(handler_name, w, r)
	if !signedIn {
		return
	}

	isAdministrator := backend.CheckAdministratorRole(handler_name, w, r)
	if !isAdministrator {
		return
	}

	query := r.URL.Query()
	memberIDs, hasMemberID := query["member_id"]
	memberEmails, hasMemberEmail := query["member_email"]
	validMemberID := hasMemberID && len(memberIDs) == 1 && memberIDs[0] != ""
	validMemberEmail := hasMemberEmail && len(memberEmails) == 1 && memberEmails[0] != ""
	if len(query) != 1 || !validMemberID && !validMemberEmail {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	var whereColumn string
	var identifier string
	if validMemberID {
		whereColumn, identifier = "MemberID", memberIDs[0]
	} else {
		whereColumn, identifier = "Email", memberEmails[0]
	}

	var memberExists bool
	err := database.DbConn.QueryRow(r.Context(), fmt.Sprintf("SELECT EXISTS (SELECT 1 FROM ISMLabMembers WHERE %s = $1)", whereColumn), identifier).Scan(&memberExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	if !memberExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a member does not exists", "Member was not found")
		return
	}

	_, err = database.DbConn.Exec(r.Context(), fmt.Sprintf("DELETE FROM ISMLabMembers WHERE %s = $1", whereColumn), identifier)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
