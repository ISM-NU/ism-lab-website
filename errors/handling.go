package error_handling

import (
	"html/template"
	"log"
	"main/models"
	"net/http"
)

func ErrorPageHandler(err_msg models.ErrorPage, w http.ResponseWriter, r *http.Request) {
	tmpl, parseErr := template.ParseFiles("./web/UI/templates/errors.html")
	if parseErr != nil {
		log.Println("[ErrorPageHandler]: Error while parsing the template")
		log.Println("[ErrorPageHandler]: parseErr -> " + parseErr.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(err_msg.ErrorCode)
	execErr := tmpl.Execute(w, err_msg)
	if execErr != nil {
		log.Println("[ErrorPageHandler]: Error while executing the template")
		log.Println("[ErrorPageHandler]: execErr -> " + execErr.Error())
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
}
