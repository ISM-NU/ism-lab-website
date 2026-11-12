package frontend

import (
	"html/template"
	"log"
	"main/backend"
	error_handling "main/errors"
	"main/models"
	"net/http"
)

func MembersPageHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/members/" {
		log.Println("[ProjectsPageHandler]: Incorrect path")
		log.Println("[ProjectsPageHandler]: The path that was used - " + r.URL.Path)
		sent := models.ErrorPage{
			ErrorCode:       http.StatusNotFound,
			OfficialMessage: http.StatusText(http.StatusNotFound),
			Explanation:     "The page you are requesting does not exists",
		}
		error_handling.ErrorPageHandler(sent, w, r)
		return
	}
	if r.Method != http.MethodGet {
		log.Println("[MainPageHandler]: Incorrect method was applied")
		log.Println("[MainPageHandler]: Method that was used - " + r.Method)
		sent := models.ErrorPage{
			ErrorCode:       http.StatusMethodNotAllowed,
			OfficialMessage: http.StatusText(http.StatusMethodNotAllowed),
			Explanation:     "Wrong method was applied. This endpoint supports only GET",
		}
		error_handling.ErrorPageHandler(sent, w, r)
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/members.html")
	if parseErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError("MembersPageHandler", w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError("MembersPageHandler", w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}

func ControlMembersPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ControlMembersPageHandler"
	handler_route := "/control/panel/members/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/control_members.html")
	if parseErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError("MembersPageHandler", w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError("MembersPageHandler", w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}
