package members

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func UpdateMembersApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/members/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("%sMembersApiCallHandler", "Update")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
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

	var member models.MemberData
	if err := json.NewDecoder(r.Body).Decode(&member); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(r.Context(), fmt.Sprintf(`UPDATE ISMLabMembers SET
		FirstName = $1, LastName = $2, CurrentYearOfStudy = $3, CurrentlyStudying = $4,
		Degree = $5, JoinDate = $6, AdditionalDescription = $7, MemberIcon = $8, Email = $9
		WHERE %s = $10`, whereColumn),
		member.FirstName, member.LastName, member.CurrentYearOfStudy, member.CurrentlyStudying,
		member.Degree, member.JoinDate, member.AdditionalDescription, member.MemberIcon, member.Email, identifier)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
