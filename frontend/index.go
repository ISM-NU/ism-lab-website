package frontend

import (
	"html/template"
	"log"
	error_handling "main/errors"
	"main/models"
	"net/http"
	"time"
)

func MainPageHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		log.Println("[MainPageHandler]: Incorrect path")
		log.Println("[MainPageHandler]: Path that was called - " + r.URL.Path)
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
	tmpl, tmplErr := template.ParseFiles("./web/UI/templates/index.html")
	if tmplErr != nil {
		log.Println("[MainPageHandler]: Could not parse the HTML template")
		log.Println("[MainPageHandler]: tmplErr -> " + tmplErr.Error())
		sent := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Something went wrong during the page parsing",
		}
		error_handling.ErrorPageHandler(sent, w, r)
		return
	}
	currentTime := time.Now()
	var tm models.MainPagePrinter
	tm.CurrentYear = currentTime.Year()
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, tm)
	if execErr != nil {
		log.Println("[MainPageHandler]: Error during the template execution")
		log.Println("[MainPageHandler]: execErr -> " + execErr.Error())
		sent := models.ErrorPage{
			ErrorCode:       http.StatusInternalServerError,
			OfficialMessage: http.StatusText(http.StatusInternalServerError),
			Explanation:     "Unable to construct working response",
		}
		error_handling.ErrorPageHandler(sent, w, r)
	}
}
