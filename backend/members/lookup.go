package members

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func ListMembersApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/members/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("%sMembersApiCallHandler", "List")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	memberIDs, hasMemberID := query["member_id"]
	memberEmails, hasMemberEmail := query["member_email"]
	targets, hasTarget := query["target"]
	validMemberID := hasMemberID && len(memberIDs) == 1 && memberIDs[0] != ""
	validMemberEmail := hasMemberEmail && len(memberEmails) == 1 && memberEmails[0] != ""
	validTarget := hasTarget && len(targets) == 1 && targets[0] == "all"
	if len(query) != 1 || !validMemberID && !validMemberEmail && !validTarget {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	const selectMembers = `SELECT MemberID, FirstName, LastName, COALESCE(CurrentYearOfStudy, 0),
		COALESCE(CurrentlyStudying, ''), COALESCE(Degree, ''), COALESCE(JoinDate, DATE '0001-01-01'),
		COALESCE(AdditionalDescription, ''), COALESCE(MemberIcon, ''), COALESCE(Email, '')
		FROM ISMLabMembers`

	if validMemberID || validMemberEmail {
		var statement string
		var argument string
		if validMemberID {
			statement, argument = selectMembers+" WHERE MemberID = $1", memberIDs[0]
		} else {
			statement, argument = selectMembers+" WHERE Email = $1", memberEmails[0]
		}

		var member models.MemberData
		err := database.DbConn.QueryRow(r.Context(), statement, argument).Scan(
			&member.MemberID, &member.FirstName, &member.LastName, &member.CurrentYearOfStudy,
			&member.CurrentlyStudying, &member.Degree, &member.JoinDate, &member.AdditionalDescription,
			&member.MemberIcon, &member.Email)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a member does not exists", "Member was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(member); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		}
		return
	}

	rows, err := database.DbConn.Query(r.Context(), selectMembers+" ORDER BY MemberID")
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}
	defer rows.Close()

	members := make([]models.MemberData, 0)
	for rows.Next() {
		var member models.MemberData
		if err := rows.Scan(
			&member.MemberID, &member.FirstName, &member.LastName, &member.CurrentYearOfStudy,
			&member.CurrentlyStudying, &member.Degree, &member.JoinDate, &member.AdditionalDescription,
			&member.MemberIcon, &member.Email); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
			return
		}
		members = append(members, member)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(members); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong during the transaction", err.Error())
	}
}
